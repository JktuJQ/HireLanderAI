from flask import redirect, url_for
from flask import Blueprint


index_page_routes = Blueprint("index_page_routes", __name__)


@index_page_routes.route("/", methods=["GET"])
def index_route():
    """Index page view function."""
    return redirect(url_for("interview_route"))
