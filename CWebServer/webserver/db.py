from flask import current_app
import requests
import logging


def get_communities():
    resp = requests.get(
        f'http://{current_app.config["DATABASE_SERVICE_HOST"]}/communities'
    )
    return resp.json()


def post_communities(communities: dict):
    resp = requests.post(
        f'http://{current_app.config["DATABASE_SERVICE_HOST"]}/communities',
        json=communities,
    )
    if resp.status_code != 200:
        logging.debug(resp.reason)
        logging.debug(resp.request.method, resp.request.headers, resp.request.body)
        logging.debug(resp.text)
    return resp.status_code


def get_posts(community_obj_id: str):
    resp = requests.get(
        f'http://{current_app.config["DATABASE_SERVICE_HOST"]}/posts',
        params={"communityObjId": community_obj_id},
    )
    print(community_obj_id)
    return resp.json()

def delete_community(id: str):
    resp = requests.delete(f'http://{current_app.config["DATABASE_SERVICE_HOST"]}/communities', params={
        "id": id
    })
    if resp.status_code != 200:
        logging.debug(resp.reason)
        logging.debug(resp.request.method, resp.request.headers, resp.request.body)
        logging.debug(resp.text)
    community = resp.json()
    print("="*50)
    print(community)
    print("="*50, flush=True)
    resp = requests.delete(f'http://{current_app.config["DATABASE_SERVICE_HOST"]}/posts', params={
        "communityId": community['communityId'],
        "instanceUrl": community['instanceUrl']
    })
    if resp.status_code != 200:
        logging.debug(resp.reason)
        logging.debug(resp.request.method, resp.request.headers, resp.request.body)
        logging.debug(resp.text)