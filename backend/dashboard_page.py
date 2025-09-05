from backend.application import application
from flask import render_template


@application.route("/dashboard", methods=["GET"])
async def dashboard_route():
    return render_template("dashboard.html")
