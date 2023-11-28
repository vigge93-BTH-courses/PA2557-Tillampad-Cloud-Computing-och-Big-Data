import os

from flask import Flask, redirect, render_template, url_for
from werkzeug.exceptions import HTTPException


def create_app() -> Flask:
    app = Flask(__name__)

    app.config.from_mapping(
        SECRET_KEY=os.getenv("CWEB_SECRET_KEY"),
        DATABASE_SERVICE_HOST=os.getenv("CDATABASESERVICE_SERVICE_HOST"),
    )

    from . import communities

    app.register_blueprint(communities.bp)

    from . import posts

    app.register_blueprint(posts.bp)

    app.register_error_handler(HTTPException, error_page)

    @app.route("/healthz")
    def healthz() -> dict[str, int]:
        return {"status": 1}

    @app.route("/")
    def index():
        return redirect(url_for("communities.index"))

    return app


def error_page(e):
    return render_template("error_page.html", e=e), e.code
