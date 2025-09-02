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


from interview_page import interview_page_routes
from index_page import index_page_routes


application.register_blueprint(interview_page_routes)
application.register_blueprint(index_page_routes)
