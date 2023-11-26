import functools
import logging
import os
import sys
from logging import Logger

import pika
import plemmy
from bson.objectid import ObjectId
from gracefull_killer import GracefulKiller
from pika.adapters.blocking_connection import BlockingChannel
from pymongo import MongoClient
from pymongo.database import Database


def load_config() -> dict[str, str]:
    posts_dbhost = os.getenv("CFETCHER_POSTS_DATABASE_HOST")
    posts_dbname = os.getenv("CFETCHER_POSTS_DATABASE_NAME")
    posts_dbcollection = os.getenv("CFETCHER_POSTS_DATABASE_COLLECTION")
    community_dbhost = os.getenv("CFETCHER_COMMUNITY_DATABASE_HOST")
    community_dbname = os.getenv("CFETCHER_COMMUNITY_DATABASE_NAME")
    community_dbcollection = os.getenv("CFETCHER_COMMUNITY_DATABASE_COLLECTION")
    queue_host = os.getenv("CFETCHER_MESSAGE_QUEUE_HOST")
    queue_username = os.getenv("CFETCHER_MESSAGE_QUEUE_USERNAME")
    queue_password = os.getenv("CFETCHER_MESSAGE_QUEUE_PASSWORD")
    queue_queues = os.getenv("CFETCHER_MESSAGE_QUEUE_QUEUE")
    log_level = os.getenv("CFETCHER_LOG_LEVEL")

    if not posts_dbhost:
        logging.warning("CFETCHER_POSTS_DATABASE_HOST not provided")
    if not posts_dbname:
        logging.warning("CFETCHER_POSTS_DATABASE_NAME not provided")
    if not posts_dbcollection:
        logging.warning("CFETCHER_POSTS_DATABASE_COLLECTION not provided")
    if not community_dbhost:
        logging.warning("CFETCHER_COMMUNITY_DATABASE_HOST not provided")
    if not community_dbname:
        logging.warning("CFETCHER_COMMUNITY_DATABASE_NAME not provided")
    if not community_dbcollection:
        logging.warning("CFETCHER_COMMUNITY_DATABASE_COLLECTION not provided")
    if not queue_host:
        logging.warning("CFETCHER_MESSAGE_QUEUE_HOST not provided")
    if not queue_username:
        logging.warning("CFETCHER_MESSAGE_QUEUE_USERNAME not provided")
    if not queue_password:
        logging.warning("CFETCHER_MESSAGE_QUEUE_PASSWORD not provided")
    if not queue_queues:
        logging.warning("CFETCHER_MESSAGE_QUEUE_QUEUE not provided")
    if not log_level:
        logging.warning("CFETCHER_LOG_LEVEL not provided")

    if not all(
        [
            posts_dbname,
            posts_dbhost,
            posts_dbcollection,
            community_dbhost,
            community_dbname,
            community_dbcollection,
            queue_host,
            queue_username,
            queue_password,
            queue_queues,
        ]
    ):
        exit()

    return {
        "POSTS_DATABASE_HOST": posts_dbhost,
        "POSTS_DATABASE_NAME": posts_dbname,
        "POSTS_DATABASE_COLLECTION": posts_dbcollection,
        "COMMUNITY_DATABASE_HOST": community_dbhost,
        "COMMUNITY_DATABASE_NAME": community_dbname,
        "COMMUNITY_DATABASE_COLLECTION": community_dbcollection,
        "MESSAGE_QUEUE_HOST": queue_host,
        "MESSAGE_QUEUE_USERNAME": queue_username,
        "MESSAGE_QUEUE_PASSWORD": queue_password,
        "MESSAGE_QUEUE_QUEUE": queue_queues,
        "LOG_LEVEL": log_level or "WARNING",
    }  # type: ignore , python does not recognise the not all() check as not allowing any None values.


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


def get_community(
    db: Database, config: dict[str, str], id: bytes, logger: Logger
) -> dict | None:
    collection = db[config["COMMUNITY_DATABASE_COLLECTION"]]
    community = collection.find_one({"_id": ObjectId(id.decode())})
    if not community:
        return None
    logger.debug(f"Got community from database: {community}.")
    return community


def update_community(
    db: Database,
    lemmy_client: plemmy.LemmyHttp,
    community_name: str,
    id: ObjectId,
    config: dict[str, str],
    logger: Logger,
):
    logger.info(f"Updating community: {id}...")
    community_resp = lemmy_client.get_community(name=community_name)
    if community_resp is None or community_resp.status_code != 200:
        logger.warning(
            f"Something went wrong when fetching community: {community_resp.status_code}, {community_resp.text}."
        )
        return False

    community: dict = community_resp.json()["community_view"]["community"]
    collection = db[config["COMMUNITY_DATABASE_COLLECTION"]]
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

    logger.info("Community updated.")

    return True


def get_posts(
    db: Database,
    lemmy_client: plemmy.LemmyHttp,
    community_name: str,
    instance_url: str,
    config: dict[str, str],
    logger: Logger,
):
    logger.info(f"Updating posts for {instance_url}, {community_name}...")
    posts_resp = lemmy_client.get_posts(
        community_name=community_name, sort="New", limit=20
    )
    if posts_resp is None or posts_resp.status_code != 200:
        logger.warning(
            f"Something went wrong when fetching posts: {posts_resp.status_code}, {posts_resp.text}."
        )
        return False
    posts = posts_resp.json()["posts"]
    collection = db[config["POSTS_DATABASE_COLLECTION"]]
    for post in posts:
        post_data = post["post"]
        del post["post"]
        post = post | post_data | {"instance_url": instance_url}
        collection.update_one({"post_id": post["id"]}, {"$set": post}, upsert=True)
    logger.info(f"Updated {len(posts)} posts.")
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
    config: dict[str, str],
    logger: Logger,
):
    logger.info("Got 1 message from queue.")

    community = get_community(community_db, config, id, logger)
    if not community:
        logger.warning(f"Community not found: {id}.")
        handle_message_failed(method, channel)
        return

    client = plemmy.LemmyHttp(community["instance_url"])

    success = update_community(
        community_db, client, community["name"], community["_id"], config, logger
    )
    if not success:
        logger.warning(f"Failed to update community: {id}.")
        handle_message_failed(method, channel)
        return

    success = get_posts(
        posts_db, client, community["name"], community["instance_url"], config, logger
    )
    if not success:
        logger.warning(f"Failed to get posts.")
        handle_message_failed(method, channel)
        return

    channel.basic_ack(delivery_tag=method.delivery_tag)
    logger.info(f"Finished message handling.")


def stop_worker(tag: str, channel: BlockingChannel, logger: Logger):
    logger.info("Stopping worker...")
    channel.basic_cancel(tag)


def worker() -> None:
    config = load_config()

    logger = setup_logging(config["LOG_LEVEL"])
    logger.info("Setting up worker...")

    connection_params = pika.ConnectionParameters(
        config["MESSAGE_QUEUE_HOST"],
        credentials=pika.PlainCredentials(
            config["MESSAGE_QUEUE_USERNAME"],
            config["MESSAGE_QUEUE_PASSWORD"],
        ),
    )
    queue_connection = pika.BlockingConnection(connection_params)
    channel = queue_connection.channel()

    queuename = config["MESSAGE_QUEUE_QUEUE"]
    channel.queue_declare(queuename)
    channel.basic_qos(prefetch_count=1)

    posts_db = get_database(
        config["POSTS_DATABASE_HOST"],
        config["POSTS_DATABASE_NAME"],
    )
    community_db = get_database(
        config["COMMUNITY_DATABASE_HOST"],
        config["COMMUNITY_DATABASE_NAME"],
    )

    queue_message_callback = functools.partial(
        handle_queue_message,
        posts_db=posts_db,
        community_db=community_db,
        logger=logger,
        config=config,
    )
    consumer_tag = channel.basic_consume(queuename, queue_message_callback)

    exit_callback = functools.partial(
        stop_worker, tag=consumer_tag, channel=channel, logger=logger
    )
    killer = GracefulKiller(exit_callback)

    logger.info("Worker setup finished, starting worker...")
    channel.start_consuming()

    queue_connection.close()
    logger.info("Worker exited succesfully!")


if __name__ == "__main__":
    worker()
