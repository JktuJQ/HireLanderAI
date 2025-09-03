from backend.application import application
from flask import redirect, url_for


@application.route("/", methods=["GET"])
def index_route():
    """Index page view function."""

    return redirect(url_for("interview_route"))
