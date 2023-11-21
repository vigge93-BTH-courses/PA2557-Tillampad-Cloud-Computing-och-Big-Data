import functools
import os
import pika
from pika.adapters.blocking_connection import BlockingChannel
import logging
import sys
from logging import Logger
import plemmy

from pymongo import MongoClient

from bson import json_util
from pymongo.database import Database
from gracefull_killer import GracefulKiller


def load_config() -> dict[str, str]:
    dbhost = os.getenv("CFETCHER_DATABASE_HOST")
    dbname = os.getenv("CFETCHER_DATABASE_NAME")
    queue_host = os.getenv("CFETCHER_MESSAGE_QUEUE_HOST")
    queue_username = os.getenv("CFETCHER_MESSAGE_QUEUE_USERNAME")
    queue_password = os.getenv("CFETCHER_MESSAGE_QUEUE_PASSWORD")
    queue_queues = os.getenv("CFETCHER_MESSAGE_QUEUE_QUEUE")
    log_level = os.getenv("CFETCHER_LOG_LEVEL")

    return {
        "CFETCHER_DATABASE_HOST": dbhost or "postmaindb",
        "CFETCHER_DATABASE_NAME": dbname or "PostMainDB",
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


def handle_queue_message(
    channel: BlockingChannel,
    method,
    properties: pika.BasicProperties,
    body,
    db: Database,
    logger: Logger,
):
    body = json_util.loads(body)
    logger.info("Got 1 message from queue...")
    logger.debug(f'updating {body["instance_url"]}, {body["name"]}')
    client = plemmy.LemmyHttp(body["instance_url"])
    posts_resp = client.get_posts(community_name=body["name"], sort="New", limit=20)
    if posts_resp is None or posts_resp.status_code != 200:
        logger.warn("Unable to handle message")
        if method.redelivered:
            channel.basic_nack(
                delivery_tag=method.delivery_tag, multiple=False, requeue=False
            )
        else:
            channel.basic_nack(
                delivery_tag=method.delivery_tag, multiple=False, requeue=True
            )
        return
    posts = posts_resp.json()["posts"]
    collection = db["posts"]
    for post in posts:
        post_data = post["post"]
        del post["post"]
        post = post | post_data
        collection.update_one({"post_id": post["id"]}, {"$set": post}, upsert=True)
    logger.info(f"Updated {len(posts)} posts...")
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

    db = get_database(
        config["CFETCHER_DATABASE_HOST"], config["CFETCHER_DATABASE_NAME"]
    )

    queue_message_callback = functools.partial(
        handle_queue_message, db=db, logger=logger
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
