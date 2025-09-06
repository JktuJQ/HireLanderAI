from backend.application import application

from flask import render_template


@application.route("/create_interview", methods=["GET", "POST"])
async def create_interview_route():
    return render_template("index.html")
