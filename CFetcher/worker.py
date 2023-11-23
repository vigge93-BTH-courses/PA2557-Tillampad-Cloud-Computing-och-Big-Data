import functools
import os
import pika
from pika.adapters.blocking_connection import BlockingChannel
import logging
import sys
from logging import Logger
import plemmy

from pymongo import MongoClient

from bson.objectid import ObjectId
from pymongo.database import Database
from gracefull_killer import GracefulKiller


def load_config() -> dict[str, str]:
    posts_dbhost = os.getenv("CFETCHER_POSTS_DATABASE_HOST")
    posts_dbname = os.getenv("CFETCHER_POSTS_DATABASE_NAME")
    community_dbhost = os.getenv("CFETCHER_COMMUNITY_DATABASE_HOST")
    community_dbname = os.getenv("CFETCHER_COMMUNITY_DATABASE_NAME")
    queue_host = os.getenv("CFETCHER_MESSAGE_QUEUE_HOST")
    queue_username = os.getenv("CFETCHER_MESSAGE_QUEUE_USERNAME")
    queue_password = os.getenv("CFETCHER_MESSAGE_QUEUE_PASSWORD")
    queue_queues = os.getenv("CFETCHER_MESSAGE_QUEUE_QUEUE")
    log_level = os.getenv("CFETCHER_LOG_LEVEL")

    return {
        "CFETCHER_POSTS_DATABASE_HOST": posts_dbhost or "",
        "CFETCHER_POSTS_DATABASE_NAME": posts_dbname or "",
        "CFETCHER_COMMUNITY_DATABASE_HOST": community_dbhost or "",
        "CFETCHER_COMMUNITY_DATABASE_NAME": community_dbname or "",
        "CFETCHER_MESSAGE_QUEUE_HOST": queue_host or "localhost",
        "CFETCHER_MESSAGE_QUEUE_USERNAME": queue_username or "",
        "CFETCHER_MESSAGE_QUEUE_PASSWORD": queue_password or "",
        "CFETCHER_MESSAGE_QUEUE_QUEUE": queue_queues or "update-community",
        "CFETCHER_LOG_LEVEL": log_level or "WARNING",
    }


def get_database(connection_string: str, database_name: str):
    client = MongoClient(connection_string)
    return client[database_name]


def setup_logging(loglevel: str):
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler(sys.stdout)
    logger.setLevel(loglevel)
    handler.setLevel(loglevel)
    logger.addHandler(handler)
    return logger

def get_community(db: Database, id: bytes, logger: Logger) -> dict | None:
    collection = db["communities"]
    community = collection.find_one({"_id": ObjectId(id.decode())})
    logger.debug(f'Community: {community}')
    if not community:
        logger.debug("No community found")
        return None
    return community


def update_community(
    db: Database,
    lemmy_client: plemmy.LemmyHttp,
    community_name: str,
    id: ObjectId,
    logger: Logger,
):
    logger.debug(community_name)
    community_resp = lemmy_client.get_community(name=community_name)
    if community_resp is None or community_resp.status_code != 200:
        logger.warning(f"update_community: Unable to handle message: {community_resp.status_code}, {community_resp.text}")
        return False

    community: dict = community_resp.json()["community_view"]["community"]
    collection = db["communities"]
    collection.update_one(
        {"_id": id},
        {
            "$set": {
                "community_id": community.get("id", -1),
                "title": community.get("title", None),
                "description": community.get("description", None),
                "removed": community.get("removed", False),
                "nsfw": community.get("nsfw", True),
                "icon": community.get("icon", None),
                "banner": community.get("banner", None),
            }
        },
    )

    logger.info("Community updated...")

    return True


def get_posts(
    db: Database, lemmy_client: plemmy.LemmyHttp, community_name: str, instance_url: str, logger: Logger
):
    posts_resp = lemmy_client.get_posts(
        community_name=community_name, sort="New", limit=20
    )
    if posts_resp is None or posts_resp.status_code != 200:
        logger.warning(f"get_posts: Unable to handle message: {posts_resp.status_code}, {posts_resp.text}")
        return False
    posts = posts_resp.json()["posts"]
    collection = db["posts"]
    for post in posts:
        post_data = post["post"]
        del post["post"]
        post = post | post_data | {"instance_url": instance_url}
        collection.update_one({"post_id": post["id"]}, {"$set": post}, upsert=True)
    logger.info(f"Updated {len(posts)} posts...")
    return True


def handle_message_failed(method, channel: BlockingChannel):
    if method.redelivered:
        channel.basic_nack(
            delivery_tag=method.delivery_tag, multiple=False, requeue=False
        )
    else:
        channel.basic_nack(
            delivery_tag=method.delivery_tag, multiple=False, requeue=True
        )


def handle_queue_message(
    channel: BlockingChannel,
    method,
    properties: pika.BasicProperties,
    id: bytes,
    posts_db: Database,
    community_db: Database,
    logger: Logger,
):
    logger.info("Got 1 message from queue...")
    logger.debug(f'updating community {id}...')

    community = get_community(community_db, id, logger)
    if not community:
        logger.warning(f'Community not found: {id}.')
        handle_message_failed(method, channel)
        return

    logger.debug(f'updating {community["instance_url"]}, {community["name"]}')

    client = plemmy.LemmyHttp(community["instance_url"])

    success = update_community(
        community_db, client, community["name"], community["_id"], logger
    )
    if not success:
        handle_message_failed(method, channel)
        return

    success = get_posts(posts_db, client, community["name"], community["instance_url"], logger)
    if not success:
        handle_message_failed(method, channel)
        return

    channel.basic_ack(delivery_tag=method.delivery_tag)


def stop_worker(tag, channel: BlockingChannel, logger: Logger):
    logger.debug("Stopping worker...")
    channel.basic_cancel(tag)


def worker() -> None:
    config = load_config()

    logger = setup_logging(config["CFETCHER_LOG_LEVEL"])
    logger.debug(config)

    connection_params = pika.ConnectionParameters(
        config["CFETCHER_MESSAGE_QUEUE_HOST"],
        credentials=pika.PlainCredentials(
            config["CFETCHER_MESSAGE_QUEUE_USERNAME"],
            config["CFETCHER_MESSAGE_QUEUE_PASSWORD"],
        ),
    )
    queue_connection = pika.BlockingConnection(connection_params)
    channel = queue_connection.channel()

    queuename = config["CFETCHER_MESSAGE_QUEUE_QUEUE"]
    channel.queue_declare(queuename)
    channel.basic_qos(prefetch_count=1)

    posts_db = get_database(
        config["CFETCHER_POSTS_DATABASE_HOST"], config["CFETCHER_POSTS_DATABASE_NAME"]
    )
    community_db = get_database(
        config["CFETCHER_COMMUNITY_DATABASE_HOST"],
        config["CFETCHER_COMMUNITY_DATABASE_NAME"],
    )

    queue_message_callback = functools.partial(
        handle_queue_message,
        posts_db=posts_db,
        community_db=community_db,
        logger=logger,
    )
    consumer_tag = channel.basic_consume(queuename, queue_message_callback)

    exit_callback = functools.partial(
        stop_worker, tag=consumer_tag, channel=channel, logger=logger
    )
    killer = GracefulKiller(exit_callback)

    channel.start_consuming()

    queue_connection.close()
    logger.debug("Worker exited succesfully!")


if __name__ == "__main__":
    worker()
