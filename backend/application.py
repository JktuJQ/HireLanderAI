from globals import *
import os

from flask import Flask

from flask_sqlalchemy import SQLAlchemy
import sqlalchemy as sa
from sqlalchemy.ext.automap import automap_base

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

# File upload
application.config["UPLOAD_FOLDER"] = os.path.join(os.getcwd(), "frontend", "static", "uploads")
application.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

# DB configuration
application.config["SQLALCHEMY_DATABASE_URI"] =\
    f"sqlite:///{os.path.abspath(os.getcwd())}/backend/db.sqlite?check_same_thread=False"
application.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(application)
with application.app_context():
    metadata = sa.MetaData()
    metadata.reflect(db.engine)

    DB = automap_base(metadata=metadata)
    DB.prepare(db.engine, reflect=True)

    User = DB.classes.user

    UserRole = DB.classes.user_role

# Socket IO
socketio = SocketIO(application)


def run(host: str = HOST, port: int = PORT):
    """Runs application on `http://{host}:{port}/`"""

    socketio.run(app=application, host=host, port=port, debug=DEBUG)
