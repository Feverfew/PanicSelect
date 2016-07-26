from . import main
from flask import make_response, send_file

@main.route('/')
@main.route('/about')
@main.route('/donate')
def index():
    return make_response(open('app/templates/index.html').read())

@main.route('/riot.txt')
def riot():
    return send_file('static/riot.txt')

