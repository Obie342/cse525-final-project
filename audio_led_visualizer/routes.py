"""Web routes for the visualizer UI."""

from __future__ import annotations

from pathlib import Path

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

web = Blueprint("web", __name__)


def controller():
    return current_app.extensions["visualizer"]


@web.get("/")
def index():
    return render_template("index.html", controller=controller())


@web.post("/live")
def live():
    controller().start_live()
    return render_template("live.html")


@web.route("/file", methods=["GET", "POST"])
def file_audio():
    if request.method == "GET":
        return redirect(url_for("web.index"))

    uploaded_file = request.files.get("file")
    if not uploaded_file or not uploaded_file.filename:
        flash("Choose a WAV file first.", "error")
        return redirect(url_for("web.index"))

    filename = secure_filename(uploaded_file.filename)
    if Path(filename).suffix.lower() != ".wav":
        flash("Only .wav files are accepted.", "error")
        return redirect(url_for("web.index"))

    file_path = Path(current_app.config["UPLOAD_FOLDER"]) / filename
    uploaded_file.save(file_path)
    controller().start_file(file_path)
    return render_template("file.html", filename=filename)


@web.post("/stop")
def stop():
    controller().stop()
    flash("Visualization stopped and LEDs cleared.", "success")
    return redirect(url_for("web.index"))


@web.route("/settings", methods=["GET", "POST"])
def settings():
    visualizer = controller()
    if request.method == "POST":
        visualizer.update_settings(
            brightness=int(request.form.get("brightness", 255)),
            pattern=request.form.get("pattern", "rainbow"),
            r=int(request.form.get("red", 255)),
            g=int(request.form.get("green", 255)),
            b=int(request.form.get("blue", 255)),
        )
        flash("Settings saved.", "success")
        return redirect(url_for("web.settings"))
    return render_template("settings.html", settings=visualizer.settings)


@web.app_errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404
