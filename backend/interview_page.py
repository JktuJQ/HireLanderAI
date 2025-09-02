from flask import render_template, Blueprint
from flask_socketio import emit
from application import socketio


interview_page_routes = Blueprint("interview_page_routes", __name__)


@interview_page_routes.route("/interview", methods=["GET"])
def interview_route():
    """Interview page view function."""
    return render_template("interview.html")


@socketio.on("code_change")
def handle_code_change(data):
    socketio.emit("code_update", {"code": data["code"]}, broadcast=True, include_self=False)
