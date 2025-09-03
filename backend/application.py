from globals import *

from flask import Flask
from flask_socketio import SocketIO


FLASK_SECRET_KEY: str = SECRETS["FLASK_SECRET_KEY"]
TEMPLATE_FOLDER: str = "../frontend/templates"
STATIC_FOLDER: str = "../frontend/static"

application = Flask(
    __name__,
    template_folder=TEMPLATE_FOLDER,
    static_folder=STATIC_FOLDER
)


application.secret_key = FLASK_SECRET_KEY
application.debug = DEBUG

application.extensions = {}

socketio = SocketIO(application)


def run(port: int = 8080, host: str = "127.0.0.1"):
    """Runs application on "http://{host}:{port}/"""
    socketio.run(app=application, port=port, host=host, debug=True)
