import os

from flask import Flask


def create_app() -> Flask:
    app = Flask(__name__)

    app.config.from_mapping(
        SECRET_KEY=os.getenv("CWEB_SECRET_KEY"),
        DATABASE_SERVICE_HOST=os.getenv("CDATABASESERVICE_SERVICE_HOST"),
    )
    print(app.config)

    from . import web

    app.register_blueprint(web.bp)

    @app.route("/heartbeat")
    def heartbeat() -> dict[str, int]:
        return {"status": 1}

    return app
