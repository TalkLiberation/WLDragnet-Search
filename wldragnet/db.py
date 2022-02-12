import os

import click
from flask import current_app, g
from flask.cli import with_appcontext
from psycopg2.pool import ThreadedConnectionPool


def init_app(app):
    """
    Initialise components of this module for a Flask app

    :param app: The Flask app
    """
    app.teardown_appcontext(close_conn)
    app.cli.add_command(init_db_command)

    # Set up a threaded database connection pool for the current instance of the app
    app.config['dbc_pool'] = ThreadedConnectionPool(
        os.getenv('DB_POOL_SIZE_MIN'),
        os.getenv('DB_POOL_SIZE_MAX'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PW'),
    )


def init_db():
    """
    Function to execute a database setup schema
    """
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))


@click.command('init-db')
@with_appcontext
def init_db_command():
    """
    Function that is registered on the command 'init-db' to be executed via the flask executable

    Run this command with 'flask init-db'
    """
    init_db()
    click.echo('Initialized the database.')


def get_db():
    """
    Accessor for a database connection received from the database connection pool.
    This connection is stored in the session context g and then returned.
    :return: A database connection from the pool
    """
    if 'db' not in g:
        g.db = current_app.config['dbc_pool'].getconn()
    return g.db


def close_conn(e):
    """
    Closes the connection stored in the session context g.
    This function is registered on the teardown_appcontext lifecycle hook.
    """
    db = g.pop('db', None)
    if db is not None:
        current_app.config['dbc_pool'].putconn(db)
