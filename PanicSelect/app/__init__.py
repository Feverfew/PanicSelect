from flask import Flask
from config import config

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    from app.api_1_0 import api_1_0 as api_1_0_blueprint
    from app.main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    app.register_blueprint(api_1_0_blueprint, url_prefix='/api/v1.0')

    return app