from backend.application import application
from flask import redirect, url_for, render_template, request


@application.route("/", methods=["GET", "POST"])
def index_route():
    if request.method == "POST":
        room_id = request.form['room_id']
        return redirect(url_for("entry_checkpoint", room_id=room_id))

    return render_template("index.html")
