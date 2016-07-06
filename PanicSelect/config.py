import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'HwvWjTZ5GxZ12rv6cF0gQ8Yae7tW7ZKQ'
    #RIOT_API_KEY = '3bdf3fcc-39db-4f5a-8a1f-477fb97f7094'
    #CHAMPION_GG_API_KEY  = 'ae89f8f81c1334bf7174a6622d47aa2c'

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,  
    'production': Config,
    'default': DevelopmentConfig  
}