from flask import Blueprint, request, render_template, abort, redirect, url_for
from . import db
from markdown import markdown
from bs4 import BeautifulSoup

bp = Blueprint("web", __name__, url_prefix="/web")


@bp.route("/")
def index():
    communities = db.get_communities()
    for community in communities:
        if community["description"]:
            html = markdown(community["description"])
            community["description"] = BeautifulSoup(
                html, features="html.parser"
            ).get_text()
    return render_template("index.html", communities=communities)


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
        return redirect(url_for("web.index"))
    return render_template("add.html")


@bp.route("/<int:communityId>/posts")
def post(communityId: int):
    return db.get_posts(communityId)
