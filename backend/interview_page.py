from backend.application import socketio, application
from flask import render_template


@application.route("/interview", methods=["GET"])
def interview_route():
    """Interview page view function."""

    return render_template("interview.html")


@socketio.event
def coding_field_update(data):
    """Socket IO handler for live coding session."""

    socketio.emit(
        "coding_field_update",
        {"code": data["code"]},
        broadcast=True,
        include_self=False
    )
