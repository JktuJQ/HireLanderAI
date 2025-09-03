from backend.application import socketio, application
from flask import render_template, url_for, redirect, request, session
from backend.interview_page import logger

@application.route("/interview/room/<string:room_id>/checkpoint/", methods=["GET", "POST"])
def checkpoint_route(room_id):
    if request.method == "POST":
        logger.info(request.form)
        display_name = request.form["display_name"]
        mute_audio = request.form["mute_audio"]
        mute_video = request.form["mute_video"]
        session[room_id] = {"name": display_name, "mute_audio": mute_audio, "mute_video": mute_video}
        return redirect(url_for("interview_route", room_id=room_id))

    return render_template("checkpoint.html", room_id=room_id)