from backend.application import application
from flask import redirect, url_for, render_template, request


@application.route("/", methods=["GET", "POST"])
async def index_route():
    if request.method == "POST":
        interview_room = request.form["interview_room"]
        return redirect(url_for("checkpoint_route", interview_room=interview_room))

    return render_template("index.html")
