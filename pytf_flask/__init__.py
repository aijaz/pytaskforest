
import os

from config import config
from flask import Flask, render_template, current_app, g

from .logs import setup_logging


def create_app(config_name):
    setup_logging()
    app = Flask(__name__)
    current_config = config[config_name]
    app.config.from_object(current_config)
    current_config.init_app(app)

    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

    # attach routes and error pages here
    from .public import public as public_blueprint
    app.register_blueprint(public_blueprint)

    #
    from .admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

    app.register_error_handler(404, page_not_found)

    @app.before_request
    def before_request():
        # print("Before request")
        pass

    @app.teardown_request
    def teardown(exc):
        # print("Teardown")
        teardown_impl(exc)

    @app.after_request
    def set_response_headers(response):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        # security via https://flask.palletsprojects.com/en/1.1.x/security/
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        # response.headers['Content-Security-Policy'] = "default-src 'self'"
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'

        return response

    return app


def page_not_found(_):
    return render_template('404.html'), 404


def teardown_impl(_):
    if g.get('file_to_delete'):
        os.remove(g.file_to_delete)

