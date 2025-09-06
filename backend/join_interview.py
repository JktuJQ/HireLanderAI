from backend.application import application

from flask import render_template


@application.route("/join_interview", methods=["GET", "POST"])
async def join_interview_route():
    return render_template("index.html")
