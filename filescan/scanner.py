import re
from psycopg2 import sql
from contextlib import closing


class Scanner:
    """
    Class to scan document strings for specific patterns and write the matches to a database
    """
    db_config = {}
    label = ""
    table_name = ""
    pattern = None

    def __init__(self, db_config):
        self.db_config = db_config

    def scan(self, db_connection, document, file_path, file_id):
        """
        Scans the document and invokes the update method
        :param db_connection: a database connection
        :param document: the document string to scan
        :param file_path: the filesystem path to the document
        :param file_url: the url of the origin site for the file
        :param file_archive_url: the archived version of the origin site for the file
        """
        print("scanning %s for %ss" % (file_path, self.label))
        data = self.pattern.findall(document)

        if data is not None and len(data) > 0:
            self.update(db_connection, data, file_id)
        else:
            print("No %ss found in file %s" % (self.label, str(file_path)))

    def update(self, db_connection, data, file_id):
        """
        Tries to write the scanned dataset into a database
        :param db_connection: a database connection
        :param file_path: the filesystem path to the document
        :param data: the scanned dataset
        :param file_url: the url of the origin site for the file
        :param file_archive_url: the archived version of the origin site for the file
        :return:
        """
        with closing(db_connection.cursor()) as cursor:
            for match in data:
                graph = match[0]

                graph_id = self.get_graph_id(cursor, graph, file_id)

                rank = 0
                # We expect ten results plus the graph_id from the match, so we are offset by one
                for entry in match[1:11]:
                    rank += 1
                    if entry:
                        cursor.execute(sql.SQL(
                            "INSERT INTO {table_name} (graph_id, rank, {label}) "
                            "VALUES(%s, %s, %s) "
                            "ON CONFLICT (graph_id, rank) DO NOTHING"
                        ).format(
                            label=sql.Identifier(self.label),
                            table_name=sql.Identifier(self.table_name)
                        ),(graph_id, rank, entry))

            db_connection.commit()

    @staticmethod
    def compile_pattern(start, iterate='', n=0, end=None):
        """
        Function to create a regex pattern for a list from a graph
        :param start: the beginning partial of the regex pattern
        :param iterate: the repeating partial
        :param n: controls how many times the iterate partial should be repeated
        :param end: (Optional) an ending partial for the regex pattern
        :return: the full regex pattern
        """
        pattern = start
        for i in range(n):
            pattern += iterate

        if end is not None:
            pattern += end

        return re.compile(pattern)

    @staticmethod
    def get_graph_id(cursor, name, file_id):
        """
        Helper function to do an upsert for graphs

        :param cursor: the cursor from a db_connection
        :param name: the name of the graph
        :param file_id: the file it appears in
        :return: the db id for the graph
        """
        cursor.execute(sql.SQL(
            "INSERT INTO graphs (name, file_id) "
            "VALUES(%(name)s, %(file_id)s) "
            "ON CONFLICT (name, file_id) DO UPDATE "
            # Workaround to get the id, even if it not yet exists 
            # Causes the row to lock, which is no problem for one shot scanning
            "SET id = graphs.id WHERE graphs.name = %(name)s AND graphs.file_id = %(file_id)s "
            "RETURNING id"
        ),{
            'name': name,
            'file_id': file_id
        })
        return cursor.fetchone()[0]


class DomainScanner(Scanner):
    def __init__(self, db_config):
        self.label = "domain"
        self.table_name = "ranked_domains"
        self.pattern = self.compile_pattern(
            r"Top\s+Domains\s+in\s+Tweet\s+in\s+(Entire Graph|G\d+):",
            r"(?:[^[]+\[\d+]\s+([^<]+)</a>)?",
            10
        )

        super().__init__(db_config)


class HashtagScanner(Scanner):
    def __init__(self, db_config):
        self.label = "hashtag"
        self.table_name = "ranked_hashtags"
        self.pattern = self.compile_pattern(
            r"Top\s+Hashtags\s+in\s+Tweet\s+in\s+(Entire Graph|G\d+):",
            r"(?:[^[]+\[\d+]\n?\s*([^<]+)</a>)?",
            10
        )

        super().__init__(db_config)


class WordScanner(Scanner):
    def __init__(self, db_config):
        self.label = "word"
        self.table_name = "ranked_words"
        self.pattern = self.compile_pattern(
            r"Top\s+Words\s+in\s+Tweet\s+in\s+(G\d+):",
            r"(?:[^\[]+\[\d+]\n?\s*([^<]+)<)?",
            10
        )

        super().__init__(db_config)


class WordPairScanner(Scanner):
    def __init__(self, db_config):
        self.label = "word_pair"
        self.table_name = "ranked_word_pairs"
        self.pattern = self.compile_pattern(
            r"Top\s+Word\s+Pairs\s+in\s+Tweet\s+in\s+(Entire Graph|G\d+):",
            r"(?:[^[]+\[\d+]\s*([^,]+),([^<]+))?",
            10
        )

        super().__init__(db_config)

    def update(self, db_connection, data, file_id):

        with closing(db_connection.cursor()) as cursor:
            for match in data:
                graph = match[0]

                graph_id = self.get_graph_id(cursor, graph, file_id)

                num_items = len(match) - 1
                rank = 0
                it = iter(match[1:num_items])
                for i in range(num_items // 2):
                    rank += 1
                    try:
                        word1 = it.__next__()
                        word2 = it.__next__()
                    except StopIteration:
                        pass

                    if word1 and word2:
                        cursor.execute(sql.SQL(
                            "INSERT INTO ranked_word_pairs (graph_id, rank, word1, word2) "
                            "VALUES(%s, %s, %s, %s) "
                            "ON CONFLICT (graph_id, rank) DO NOTHING"
                        ),
                            (graph_id, rank, word1, word2)
                        )
            db_connection.commit()


class HandleScanner(Scanner):
    def __init__(self, db_config):
        self.label = "handle"
        self.table_name = "ranked_handles"
        self.pattern = self.compile_pattern(
            r"Top\s+(Mentioned|Replied-To|Tweeters)\s+in\s+(Entire Graph|G\d+):",
            r"(?:[^@]*@(\w{1,15}))?",
            10
        )

        super().__init__(db_config)

    def update(self, db_connection, data, file_id):

        with closing(db_connection.cursor()) as cursor:
            for match in data:
                handle_type = match[0]
                graph = match[1]

                graph_id = self.get_graph_id(cursor, graph, file_id)

                rank = 0
                for handle in match[2:12]:
                    rank += 1
                    if handle:
                        cursor.execute(sql.SQL(
                            "INSERT INTO ranked_handles (graph_id, rank, type, handle) "
                            "VALUES(%s, %s, %s, %s) "
                            "ON CONFLICT (graph_id, rank, type) DO NOTHING"
                        ),
                            (graph_id, rank, handle_type, handle)
                        )
            db_connection.commit()

class InfluencerScanner(Scanner):
    def __init__(self, db_config):
        self.label = "handle"
        self.table_name = "ranked_handles"
        self.pattern = self.compile_pattern(
            r"Top(?:\s|\n)+Influencers:(?:\s|\n)+",
            r"(?:[^@]*@(\w{1,15}))?",
            10
        )

        super().__init__(db_config)

    def update(self, db_connection, data, file_id):

        with closing(db_connection.cursor()) as cursor:
            for match in data:
                type = 'Influencer'
                graph = 'Entire Graph'

                graph_id = self.get_graph_id(cursor, graph, file_id)

                rank = 0
                for handle in match[0:10]:
                    rank += 1
                    if handle:
                        cursor.execute(sql.SQL(
                            "INSERT INTO ranked_handles (graph_id, rank, type, handle) "
                            "VALUES(%s, %s, %s, %s) "
                            "ON CONFLICT (graph_id, rank, type) DO NOTHING"
                        ),
                            (graph_id, rank, type, handle)
                        )
            db_connection.commit()


class DescriptionScanner(Scanner):
    def __init__(self, db_config):
        self.label = "description"
        self.pattern = self.compile_pattern(
            r"\<\/span\>\s*Description\s*\<\/div\>\s*\<div\>(.+?)(?=\<\/div\>)",
        )

        super().__init__(db_config)

    def update(self, db_connection, data, file_id):

        if len(data) > 0:
            description = data[0]

            with closing(db_connection.cursor()) as cursor:
                cursor.execute(sql.SQL(
                    "UPDATE files SET description = %s "
                    "WHERE id = %s"
                ),
                    (description, file_id)
                )
            db_connection.commit()
