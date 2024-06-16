import json
import os

basedir = os.path.abspath(os.path.dirname(__file__))


# setup template folder and static folder
class Config:

    @staticmethod
    def init_app(app):
        # do any other initialization here
        app.config['SECRET_KEY'] = os.getenv("PYTF_FLASK_SECRET_KEY")
        app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024


class DevelopmentConfig(Config):
    DEBUG = True
    SERVER = "http://localhost:8000"


class TestingConfig(Config):
    TESTING = True
    DEBUG = True


class ProductionConfig(Config):
    TESTING = False
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': ProductionConfig
}
