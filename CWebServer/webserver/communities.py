from flask import Blueprint, abort, redirect, render_template, request, url_for

from . import db, utils

bp = Blueprint("communities", __name__, url_prefix="/communities")


@bp.route("/")
def index():
    communities = db.get_communities()
    for community in communities:
        if community["description"]:
            community["description"] = utils.md_to_text(community["description"])
    return render_template("index.html", communities=communities)


@bp.route("/json")
def communities_json():
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
        return redirect(url_for("communities.index"))
    return render_template("add.html")


@bp.route("/<string:id>/delete", methods=["POST"])
def delete_community(id: str):
    db.delete_community(id)
    return redirect(url_for("communities.index"))
