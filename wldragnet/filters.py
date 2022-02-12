import os

import flask

blueprint = flask.Blueprint('filters', __name__)


@blueprint.app_template_filter('absolute_path')
def absolute_path_filter(path):
    """
    Template filter to generate an absolute filesystem path from a relative one

    :param path: the relative path
    :return: the absolute path
    """
    return os.path.abspath(path)