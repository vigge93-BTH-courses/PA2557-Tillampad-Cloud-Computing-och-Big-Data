from flask import current_app
import requests
import logging


def get_communities():
    resp = requests.get(
        f'http://{current_app.config["DATABASE_HANDLER_URI"]}/communities'
    )
    return resp.json()


def post_communities(communities):
    resp = requests.post(
        f'http://{current_app.config["DATABASE_HANDLER_URI"]}/communities',
        json=communities,
    )
    if resp.status_code != 200:
        logging.debug(resp.reason)
        logging.debug(resp.request.method, resp.request.headers, resp.request.body)
        logging.debug(resp.text)
    return resp.status_code


def get_posts(communityId):
    resp = requests.get(
        f'http://{current_app.config["DATABASE_HANDLER_URI"]}/posts',
        params={"communityId": communityId},
    )
    print(resp.request.method)
    print(resp.request.url)
    print(resp.request.body, flush=True)  
    return resp.json()
