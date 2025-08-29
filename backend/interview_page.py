from backend.application import application
from flask import render_template

INTERVIEW_TEMPLATE: str = "interview.html"


@application.route("/interview", methods=["GET"])
def interview_route():
    """Interview page view function."""
    return render_template(INTERVIEW_TEMPLATE)
