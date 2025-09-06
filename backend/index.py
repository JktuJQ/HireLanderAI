from backend.application import application

from flask import render_template, flash


@application.route("/", methods=["GET", "POST"])
async def index_route():
    return render_template("index.html")
