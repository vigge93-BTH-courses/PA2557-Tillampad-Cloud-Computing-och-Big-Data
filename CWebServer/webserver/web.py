from flask import Blueprint
from . import db

bp = Blueprint("Web", __name__, url_prefix="/web")


@bp.route("/")
def index():
    return db.get_communities()
