import json
import os
import re
from contextlib import closing
from time import time

import jwt
from flask import (
    Blueprint, current_app, escape, redirect, render_template, request, url_for
)

from wldragnet.db import get_db
from wldragnet.extractor import AbstractExtractor, MentionedExtractor, TweetersExtractor, RepliedToExtractor, \
    WordsExtractor, \
    HashtagsExtractor, InfluencerExtractor
from wldragnet.redis import get_redis

blueprint = Blueprint('result', __name__)

# Each class will search for a different kind of data in the db
extractors: [AbstractExtractor] = [
    MentionedExtractor(),
    TweetersExtractor(),
    RepliedToExtractor(),
    InfluencerExtractor(),
    WordsExtractor(),
    HashtagsExtractor(),
]


@blueprint.route('/result')
def result():
    """
    Endpoint for searching a twitter handle in the wldragnet db

    :return: the results page
    """
    query = str(escape(request.args.get('q')))

    if query == 'None':
        return redirect(url_for('index'))

    match = re.search(r'^@?(\w{1,15})', query)
    if match is None:
        return redirect(url_for('index'))

    query = match.group(1)
    query = query.lower()

    token = generate_jwt(query)

    redis_conn = get_redis()

    if redis_conn.exists(query):
        results = json.loads(redis_conn.hget(query, current_app.config['REDIS_RESULTS_KEY']))
        return render_template('site/pages/result.html', hit_count=len(results), query=query, token=token)

    results = fetch_results(query)

    if results is None:
        results = []

    redis_conn.hset(query, current_app.config['REDIS_RESULTS_KEY'], json.dumps(results))

    return render_template('site/pages/result.html', hit_count=len(results), query=query, token=token)


def generate_jwt(query):
    """
    Generates a JWT with a custom claim inside holding the query that was searched for
    :param query: the query to search for
    :return: a JsonWebToken
    """
    return jwt.encode({
        current_app.config['JWT_CLAIM_NAME']: query,
        'exp': time() + int(os.getenv('JWT_TOKEN_LIFETIME'))
    }, os.getenv('JWT_SECRET_KEY'), algorithm='HS256')


def fetch_results(query):
    """
    Fetches the results for a query search and writes it to a specific datastructure
    :param query: the query to search for
    :return: a list of dicts containing the results of the search
    """
    with closing(get_db().cursor()) as cursor:
        cursor.execute(
            "SELECT ranked_handles.rank, ranked_handles.type, g.id, "
            "g.name, f.id, f.file_url, f.archive_url, f.description "
            "FROM ranked_handles "
            "LEFT JOIN graphs g ON ranked_handles.graph_id = g.id "
            "LEFT JOIN files f ON g.file_id = f.id "
            "WHERE ranked_handles.handle = %s", (query,)
        )

        hits = cursor.fetchall()

        if hits is None or len(hits) == 0:
            return None

        dict_hits = [dict(
            rank=x[0],
            type=x[1],
            graph_id=x[2],
            graph_name=x[3],
            file_id=x[4],
            file_url=x[5],
            archive_url=x[6],
            file_description=shorten_text(x[7])
        ) for x in hits]

        graph_ids = tuple([x[2] for x in hits])

        for extractor in extractors:
            # Fetch additional data from db
            data = extractor.execute(cursor, graph_ids)
            # Populate search results with it
            extractor.update(dict_hits, data)

    results = transform_result(dict_hits)

    return results


def shorten_text(text):
    """
    Helper function to shorten a string
    :param text: text to be shortened
    :return: the shortened text
    """
    if not isinstance(text, str):
        return ''

    return re.sub(r'(^.{200}[^.]*\.).*', r'\g<1>..', text)


def transform_result(dict_hits):
    """
    Helper function to transform the results for report generation
    :param dict_hits: a list of db hits in dict form
    :return: a list of dicts containing the results
    """
    results = {}
    for hit in dict_hits:
        file_id = hit['file_id']

        if file_id not in results:
            results[file_id] = {}

        file_result = results[file_id]

        if 'file_url' not in file_result:
            file_result['file_url'] = hit['file_url']

        if 'archive_url' not in file_result:
            file_result['archive_url'] = hit['archive_url']

        if 'file_description' not in file_result:
            file_result['file_description'] = hit['file_description']

        if 'influencerhandles' not in file_result and 'influencerhandles' in hit:
            file_result['influencerhandles'] = hit['influencerhandles']

        if 'graphs' not in file_result:
            file_result['graphs'] = {}

        graph_id = hit['graph_id']
        graphs = file_result['graphs']

        if graph_id not in graphs:
            graphs[graph_id] = {}

        graph = graphs[graph_id]

        if 'mentionedhandles' not in graph and 'mentionedhandles' in hit:
            graph['mentionedhandles'] = hit['mentionedhandles']

        if 'tweetershandles' not in graph and 'tweetershandles' in hit:
            graph['tweetershandles'] = hit['tweetershandles']

        if 'repliedtohandles' not in graph and 'repliedtohandles' in hit:
            graph['repliedtohandles'] = hit['repliedtohandles']

        if 'hashtags' not in graph and 'hashtags' in hit:
            graph['hashtags'] = hit['hashtags']

        if 'words' not in graph and 'words' in hit:
            graph['words'] = hit['words']

        if 'graph_name' not in graph and 'graph_name' in hit:
            graph['graph_name'] = hit['graph_name']

        if 'words' not in graph and 'words' in hit:
            graph['words'] = hit['words']

        if 'hits' not in graph:
            graph['hits'] = []

        graph['hits'].append({
            'rank': hit['rank'],
            'type': hit['type']
        })

    return results