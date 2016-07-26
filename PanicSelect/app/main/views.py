from . import main
from flask import make_response

@main.route('/')
@main.route('/about')
@main.route('/donate')
def index():
    return make_response(open('app/templates/index.html').read())

