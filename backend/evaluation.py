from backend.application import application
from flask import render_template


@application.route("/evaluation", methods=["GET"])
async def evaluation_route():
    return render_template("evaluation.html")
