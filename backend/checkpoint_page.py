from backend.application import application

from flask import render_template, url_for, redirect, request, session
from backend.interview_page import logger


@application.route("/interview/room/<int:interview_room>/checkpoint/", methods=["GET", "POST"])
def checkpoint_route(interview_room: int):
    if request.method == "POST":
        logger.info(request.form)
        display_name = request.form["display_name"]
        mute_audio = request.form["mute_audio"]
        mute_video = request.form["mute_video"]
        session[interview_room] = {"name": display_name, "mute_audio": mute_audio, "mute_video": mute_video}
        return redirect(url_for("interview_route", interview_room=interview_room))

    return render_template("checkpoint.html", interview_room=interview_room)