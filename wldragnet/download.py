import json
import logging as log
import os
from io import BytesIO

import jwt
from flask import (
    Blueprint, escape, current_app, send_file, redirect, request, url_for
)

from wldragnet.pdfcreator import generate_report
from wldragnet.redis import get_redis

blueprint = Blueprint('download', __name__)


@blueprint.route('/download')
def download():
    """
    Endpoint for the '/download' path.
    Expects a get parameter 'ticket' which is a JWT that holds the query for which a download should be fetched
    :return: a filestream response
    """
    if request.method != 'GET':
        return redirect(url_for('index'))

    ticket = escape(request.args.get("ticket"))

    try:
        token = jwt.decode(ticket, os.getenv('JWT_SECRET_KEY'), algorithms=['HS256'])

    except jwt.ExpiredSignatureError:
        log.warning(current_app.config['ERROR_MESSAGES']['ticket_expired'])
        return redirect(url_for('index', error='ticket_expired'))

    except jwt.DecodeError:
        log.warning(current_app.config['ERROR_MESSAGES']['decoding_error'])
        return redirect(url_for('index'))

    except jwt.InvalidTokenError:
        log.warning(current_app.config['ERROR_MESSAGES']['invalid_token'])
        return redirect(url_for('index'))

    # We get the query for which to generate the report from a jwt claim
    query = token[current_app.config['JWT_CLAIM_NAME']]

    redis_connection = get_redis()

    if not redis_connection.hexists(query, current_app.config['REDIS_RESULTS_KEY']):
        log.warning(current_app.config['ERROR_MESSAGES']['result_empty'])
        return redirect(url_for('index', error='result_empty'))

    result_string = redis_connection.hget(query, current_app.config['REDIS_RESULTS_KEY'])
    results = json.loads(result_string)

    if results is None or len(results) < 0:
        log.warning(current_app.config['ERROR_MESSAGES']['result_empty'])
        return redirect(url_for('index', error='result_empty'))

    pdf_stream = BytesIO()
    # The report will be written directly to a buffer
    generate_report(query, results, pdf_stream)
    # Reset the pointer of the buffer
    pdf_stream.seek(0)

    return send_file(
        pdf_stream,
        mimetype='application/pdf',
        as_attachment=True,
        attachment_filename='wldragnet-report-%s.pdf' % query)