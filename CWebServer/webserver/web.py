from flask import Blueprint, request, render_template, abort, redirect, url_for
from . import db

bp = Blueprint("web", __name__, url_prefix="/web")


@bp.route("/")
def index():
    return db.get_communities()


@bp.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        instance_urL = request.form["instance_url"]
        community_name = request.form["community_name"]
        result = db.post_communities(
            {"instanceUrl": instance_urL, "name": community_name}
        )
        if result != 200:
            abort(400, "Something went wrong, please try again.")
        redirect(url_for("web.index"))
    return render_template("add.html")


@bp.route("/<int:communityId>/posts")
def post(communityId: int):
    return db.get_posts(communityId)
