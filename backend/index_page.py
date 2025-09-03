from flask import redirect, url_for
from .application import application


@application.route("/", methods=["GET"])
def index_route():
    """Index page view function."""
    return redirect(url_for("interview_route"))
