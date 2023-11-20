from flask import current_app
import requests


def get_communities():
    resp = requests.get(
        f'http://{current_app.config["DATABASE_HANDLER_URI"]}/communities'
    )
    return resp.json()
