from backend.application import application

from flask import render_template, url_for, redirect, request, session


@application.route("/join_interview", methods=["GET", "POST"])
async def join_interview_route():
    if request.method == "POST":
        display_name = request.form["display_name"]
        interview_room = request.form["interview_room"]
        mute_audio = request.form["mute_audio"]
        mute_video = request.form["mute_video"]
        session[interview_room] = {"name": display_name, "mute_audio": mute_audio, "mute_video": mute_video}
        return redirect(url_for("interview_route", interview_room=interview_room))
    return render_template("join_room.html")
