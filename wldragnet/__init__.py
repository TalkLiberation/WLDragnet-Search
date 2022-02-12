import logging as log

from dotenv import load_dotenv
from flask import Flask, escape, request, render_template

from wldragnet.redis import get_redis

load_dotenv()
log.basicConfig(filename='application.log', encoding='utf-8', level=log.WARNING)


def create_app():
    """
    The App factory for the wldragnet flask app

    :return: an instance of the app
    """
    app = Flask(__name__)
    app.config.from_pyfile('config.py')

    # load blueprints
    from . import db, filters, result, download
    db.init_app(app)
    app.register_blueprint(filters.blueprint)
    app.register_blueprint(result.blueprint)
    app.register_blueprint(download.blueprint)

    @app.route('/')
    def index():
        error = str(escape(request.args.get("error")))

        if error is None:
            return render_template('site/pages/index.html')
        else:
            return render_template('site/pages/index.html', error=app.config['ERROR_MESSAGES'][error])

    @app.route('/faq')
    def faq():
        return render_template('site/pages/faq.html')

    return app
