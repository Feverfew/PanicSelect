#!/usr/bin/env python   
import os
from app import create_app
from flask.ext.script import Manager, Shell, Server

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)

def make_shell_context():
    return dict(app=app)

manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command("runserver", Server())

if __name__ == "__main__":
    app.run()