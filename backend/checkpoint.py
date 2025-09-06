from backend.application import application

from flask import render_template, url_for, redirect, request, session
from backend.interview import logger


@application.route("/interview/<string:interview_room>/checkpoint/", methods=["GET", "POST"])
async def checkpoint_route(interview_room: str):
    if request.method == "POST":
        logger.info(request.form)
        display_name = request.form["display_name"]
        mute_audio = request.form["mute_audio"]
        mute_video = request.form["mute_video"]
        session[interview_room] = {"name": display_name, "mute_audio": mute_audio, "mute_video": mute_video}
        return redirect(url_for("interview_route", interview_room=interview_room))

    return render_template("checkpoint.html", interview_room=interview_room)
