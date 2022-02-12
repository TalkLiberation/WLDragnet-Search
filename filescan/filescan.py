import csv
import os
import re
import sys
from concurrent.futures import ProcessPoolExecutor
from contextlib import closing
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql

from scanner import Scanner, WordScanner, DomainScanner, HandleScanner, WordPairScanner, HashtagScanner, \
    DescriptionScanner, InfluencerScanner  # , URLScanner

load_dotenv()

# The default database connection configuration derived from the environment
db_config = dict(
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT'),
    database=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PW'),
)

# List of scanners to be used for each file
scanners: [Scanner] = [
    HandleScanner(db_config),
    DomainScanner(db_config),
    HashtagScanner(db_config),
    WordScanner(db_config),
    WordPairScanner(db_config),
    DescriptionScanner(db_config),
    InfluencerScanner(db_config),
]

# The csv containing urls for the archived graphs
with open('archived-files.csv', newline='') as csvfile:
    fieldnames = ['graph', 'timestamp', 'archive_url']
    reader = csv.DictReader(csvfile, fieldnames=fieldnames)
    csv_data = {x['graph']: x for x in reader}


def print_psycopg2_exception(err):
    """
    Function to get a more verbose output for sql errors

    :param err: the raised exception
    """
    # get details about the exception
    err_type, err_obj, traceback = sys.exc_info()

    # get the line number when exception occured
    line_num = traceback.tb_lineno
    # print the connect() error
    print("\npsycopg2 ERROR:", err, "on line number:", line_num)
    print("psycopg2 traceback:", traceback, "-- type:", err_type)

    # psycopg2 extensions.Diagnostics object attribute
    print("\nextensions.Diagnostics:", err.diag)

    # print the pgcode and pgerror exceptions
    print("pgerror:", err.pgerror)
    print("pgcode:", err.pgcode, "\n")


def register_file(db_connection, graph_number, graph_timestamp, file_url, archive_url):
    with closing(db_connection.cursor()) as cursor:
        cursor.execute(sql.SQL(
            "INSERT INTO files (nodexl_id, timestamp, file_url, archive_url) "
            "VALUES(%(nodexl_id)s, %(timestamp)s, %(file_url)s, %(archive_url)s) "
            "ON CONFLICT (file_url) DO UPDATE "
            # Workaround to get the graph id, even if it not yet exists 
            # Causes the row to lock, which is no problem for one shot scanning
            "SET id = files.id WHERE files.file_url = %(file_url)s "
            "RETURNING id"
        ),{
            'nodexl_id': graph_number,
            'timestamp': graph_timestamp,
            'file_url': file_url,
            'archive_url': archive_url
        })
        return cursor.fetchone()[0]


def process_file(file_path):
    clean_path = file_path.relative_to(os.getenv('DOCUMENT_PATH'))

    # fetch graph number
    matches = re.findall(r".*Graph-(\d+)\.html", str(clean_path))

    graph_number = matches[0]
    archive_url = csv_data.get(graph_number)['archive_url']
    snapshot_timestamp = csv_data.get(graph_number)['timestamp']
    # from the archive url get the original url
    matches = re.findall(r".*/\d+/(.*)", archive_url)
    file_url = matches[0]

    document = file_path.read_text()

    db_connection = psycopg2.connect(**db_config)
    try:
        file_id = register_file(db_connection, graph_number, snapshot_timestamp, file_url, archive_url)

        for scanner in scanners:
            scanner.scan(db_connection, document, clean_path, file_id)

    except (Exception, psycopg2.DatabaseError) as error:
        print("Error while connecting to PostgreSQL", error)
        print_psycopg2_exception(error)

    finally:
        db_connection.close()


def main():
    base_path = Path(os.getenv('DOCUMENT_PATH'))
    known_files = base_path.glob(os.getenv('DOCUMENT_GLOB_PATTERN'))

    with ProcessPoolExecutor(max_workers=int(os.getenv('SCAN_PROCESS_POOL_SIZE_MAX'))) as executor:
        executor.map(process_file, known_files)


if __name__ == '__main__':
    main()