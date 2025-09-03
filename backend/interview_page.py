from flask import render_template
from .application import socketio, application


@application.route("/interview", methods=["GET"])
def interview_route():
    """Interview page view function."""
    return render_template("interview.html")


@socketio.on("code_change")
def handle_code_change(data):
    socketio.emit("code_update", {"code": data["code"]}, broadcast=True, include_self=False)
