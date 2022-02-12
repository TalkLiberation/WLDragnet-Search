from psycopg2 import sql


class AbstractExtractor:
    """
    A class that fetches data from a database and writes it to a dict
    """
    _sql = ""
    _table = ""

    _type = ""
    _label = ""

    def execute(self, cursor, graph_ids):
        """
        Queries the database for the data of set of graph_ids.
        Uses the private field sql to query the data

        :param cursor: the cursor of a database connection
        :param graphs: the graph ids to fetch data for
        :return: a list of dicts containing the fetched data
        """
        cursor.execute(self._sql, (graph_ids,))
        return cursor.fetchall()

    def update(self, results, data):
        """
        Appends each dataset to labeled attributes of the results dict

        :param results: a list of dicts containing
        :param data: the raw data fetched from the database
        """
        for element in results:
            for new_data in data:
                if element['graph_id'] == new_data[0]:
                    element[self._label] = new_data[1]


class AbstractHandleExtractor(AbstractExtractor):
    """
    An Extractor for entries in the ranked_handles table determined by the type set in a subclass
    """

    def __init__(self):
        self._sql = sql.SQL(
            "SELECT graph_id, array_to_string(array_agg(handle ORDER BY rank),',') AS handles "
            "FROM ranked_handles "
            "WHERE graph_id IN %s AND type = {type} "
            "GROUP BY graph_id"
        ).format(type=sql.Literal(self._type))
        super().__init__()


class MentionedExtractor(AbstractHandleExtractor):

    def __init__(self):
        self._type = "Mentioned"
        self._label = "mentionedhandles"
        super().__init__()


class TweetersExtractor(AbstractHandleExtractor):

    def __init__(self):
        self._type = "Tweeters"
        self._label = "tweetershandles"
        super().__init__()


class RepliedToExtractor(AbstractHandleExtractor):

    def __init__(self):
        self._type = "Replied-To"
        self._label = "repliedtohandles"
        super().__init__()


class InfluencerExtractor(AbstractHandleExtractor):

    def __init__(self):
        self._type = "Influencer"
        self._label = "influencerhandles"
        super().__init__()


class AbstractSimpleExtractor(AbstractExtractor):
    """
    An Extractor for data in a single column
    """

    def __init__(self):
        self._sql = sql.SQL(
            "SELECT graph_id, array_to_string(array_agg({type} ORDER BY rank),',') AS {label} "
            "FROM {table} "
            "WHERE graph_id IN %s "
            "GROUP BY graph_id"
        ).format(
            type=sql.Identifier(self._type),
            label=sql.Identifier(self._label),
            table=sql.Identifier(self._table)
        )
        super().__init__()


class URLsExtractor(AbstractSimpleExtractor):

    def __init__(self):
        self._table = "ranked_urls"
        self._type = "url"
        self._label = "urls"
        super().__init__()


class DomainsExtractor(AbstractSimpleExtractor):

    def __init__(self):
        self._table = "ranked_domains"
        self._type = "domain"
        self._label = "domains"
        super().__init__()


class HashtagsExtractor(AbstractSimpleExtractor):

    def __init__(self):
        self._table = "ranked_hashtags"
        self._type = "hashtag"
        self._label = "hashtags"
        super().__init__()


class WordsExtractor(AbstractSimpleExtractor):

    def __init__(self):
        self._table = "ranked_words"
        self._type = "word"
        self._label = "words"
        super().__init__()


class WordpairsExtractor(AbstractExtractor):

    def __init__(self):
        self._sql = sql.SQL(
            "SELECT graph_id, array_to_string(array_agg(word1 ||','|| word2  ORDER BY rank),' | ') AS wordpairs "
            "FROM ranked_word_pairs "
            "WHERE graph_id IN %s "
            "GROUP BY graph_id"
        )

        self._label = "wordpairs"
        super().__init__()
