import datetime

from flask import Blueprint, render_template

from . import db, utils

bp = Blueprint("posts", __name__, url_prefix="/posts")


@bp.route("/<string:communityObjId>")
def index(communityObjId: str):
    posts = db.get_posts(communityObjId)
    for post in posts:
        published = datetime.datetime.fromisoformat(post["published"])
        post["published"] = published.astimezone().strftime("%Y-%m-%d %H:%M")
        if post["body"]:
            post["body"] = utils.md_to_text(post["body"].replace("::", "\n"))
        if post["embedDescription"]:
            post["embedDescription"] = utils.md_to_text(
                post["embedDescription"].replace("::", "\n")
            )
    return render_template("posts.html", posts=posts)


@bp.route("/<string:communityObjId>/json")
def json(communityObjId: str):
    return db.get_posts(communityObjId)
