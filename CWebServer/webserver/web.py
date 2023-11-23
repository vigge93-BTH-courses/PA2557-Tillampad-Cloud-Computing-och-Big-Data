from flask import Blueprint, request, render_template, abort, redirect, url_for
from . import db
from markdown import markdown
from bs4 import BeautifulSoup
import datetime

bp = Blueprint("web", __name__, url_prefix="/web")


@bp.route("/")
def index():
    communities = db.get_communities()
    for community in communities:
        if community["description"]:
            community["description"] = md_to_text(community["description"])
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
        return redirect(url_for("web.index"))
    return render_template("add.html")

@bp.route("/<int:communityId>/posts")
def post(communityId: int):
    posts = db.get_posts(communityId)
    for post in posts:
        published = datetime.datetime.fromisoformat(post["published"])
        post["published"] = published.astimezone().strftime("%Y-%m-%d %H:%M")
        if post["body"]:
            post["body"] = md_to_text(post["body"].replace('::', '\n'))
        if post["embedDescription"]:
            post["embedDescription"] = md_to_text(post["embedDescription"].replace('::', '\n'))
    return render_template('posts.html', posts=posts)

@bp.route("/<int:communityId>/posts/json")
def post_json(communityId: int):
    return db.get_posts(communityId)

def md_to_text(text):
    html = markdown(text)
    return BeautifulSoup(html, features="html.parser").get_text()