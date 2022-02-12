import os
import sys

from flask import g

libpath = "venv/lib/python3.9/site-packages"
if libpath not in sys.path:
    sys.path.append(libpath)
import redis


def get_redis():
    """
    This function fetches a redis connection, whether newly spawned or from session context

    :return: a redis connection
    """
    if 'redis' not in g:
        g.redis = redis.Redis(
            host=os.getenv('REDIS_HOST'),
            port=int(os.getenv('REDIS_PORT')),
            db=int(os.getenv('REDIS_DB'))
        )
    return g.redis

