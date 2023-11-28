import logging

import requests
from flask import current_app


def get_communities():
    resp = requests.get(
        f'http://{current_app.config["DATABASE_SERVICE_HOST"]}/communities'
    )
    if resp.status_code != 200:
        logging.warning("Failed to get community.")
        logging.debug(resp.reason)
        logging.debug(resp.request.method, resp.request.headers, resp.request.body)
        logging.debug(resp.text)
        return []
    return resp.json()


def post_communities(communities: dict):
    resp = requests.post(
        f'http://{current_app.config["DATABASE_SERVICE_HOST"]}/communities',
        json=communities,
    )
    if resp.status_code != 200:
        logging.warning("Failed to add community.")
        logging.debug(resp.reason)
        logging.debug(resp.request.method, resp.request.headers, resp.request.body)
        logging.debug(resp.text)
    return resp.status_code


def get_posts(community_obj_id: str):
    resp = requests.get(
        f'http://{current_app.config["DATABASE_SERVICE_HOST"]}/posts',
        params={"communityObjId": community_obj_id},
    )
    if resp.status_code != 200:
        logging.warning("Failed to get posts.")
        logging.debug(resp.reason)
        logging.debug(resp.request.method, resp.request.headers, resp.request.body)
        logging.debug(resp.text)
        return []
    return resp.json()


def delete_community(id: str):
    resp = requests.delete(
        f'http://{current_app.config["DATABASE_SERVICE_HOST"]}/communities',
        params={"id": id},
    )
    if resp.status_code != 200:
        logging.warning("Failed to delete community.")
        logging.debug(resp.reason)
        logging.debug(resp.request.method, resp.request.headers, resp.request.body)
        logging.debug(resp.text)
        return

    community = resp.json()
    resp = requests.delete(
        f'http://{current_app.config["DATABASE_SERVICE_HOST"]}/posts',
        params={
            "communityId": community["communityId"],
            "instanceUrl": community["instanceUrl"],
        },
    )
    if resp.status_code != 200:
        logging.warning("Failed to delete community posts.")
        logging.debug(resp.reason)
        logging.debug(resp.request.method, resp.request.headers, resp.request.body)
        logging.debug(resp.text)
