import datetime as dt
import functools
import logging
import os
import random
import sys
from dataclasses import dataclass
from threading import Event

import pika
from gracefull_killer import GracefulKiller
from pymongo import MongoClient


@dataclass
class ExponentialBackoff:
    sleeper: Event
    minTime: int = 1
    maxTime: int = 30
    currentTime: int = minTime
    factor: int = 2

    def increase(self):
        self.currentTime = min(self.currentTime * self.factor, self.maxTime)

    def clear(self):
        self.currentTime = self.minTime

    def sleep(self, time=None):
        if time is None:
            time = self.currentTime
        self.sleeper.wait(time)


def load_config() -> dict[str, str]:
    dbservice = os.getenv("CWORKER_DATABASE_HOST")
    dbname = os.getenv("CWORKER_DATABASE_NAME")
    dbcollection = os.getenv("CWORKER_DATABASE_COLLECTION")
    refreshRate = os.getenv("CWORKER_REFRESH_RATE")
    queue_host = os.getenv("CWORKER_MESSAGE_QUEUE_HOST")
    queue_username = os.getenv("CWORKER_MESSAGE_QUEUE_USERNAME")
    queue_password = os.getenv("CWORKER_MESSAGE_QUEUE_PASSWORD")
    queue_queues = os.getenv("CWORKER_MESSAGE_QUEUE_QUEUE")
    batch_size = os.getenv("CWORKER_BATCH_SIZE")
    log_level = os.getenv("CWORKER_LOG_LEVEL")

    if not dbservice:
        logging.warning("CWORKER_DATABASE_HOST not provided")
    if not dbname:
        logging.warning("CWORKER_DATABASE_NAME not provided")
    if not dbcollection:
        logging.warning("CWORKER_DATABASE_COLLECTION not provided")
    if not queue_host:
        logging.warning("CWORKER_MESSAGE_QUEUE_HOST not provided")
    if not queue_username:
        logging.warning("CWORKER_MESSAGE_QUEUE_USERNAME not provided")
    if not queue_password:
        logging.warning("CWORKER_MESSAGE_QUEUE_PASSWORD not provided")
    if not queue_queues:
        logging.warning("CWORKER_MESSAGE_QUEUE_QUEUE not provided")
    if not log_level:
        logging.warning("CWORKER_LOG_LEVEL not provided")

    if not all(
        [
            dbname,
            dbservice,
            dbcollection,
            queue_host,
            queue_username,
            queue_password,
            queue_queues,
        ]
    ):
        exit()

    return {
        "DATABASE_HOST": dbservice,
        "DATABASE_NAME": dbname,
        "DATABASE_COLLECTION": dbcollection,
        "REFRESH_RATE": refreshRate or "300",
        "MESSAGE_QUEUE_HOST": queue_host,
        "MESSAGE_QUEUE_USERNAME": queue_username,
        "MESSAGE_QUEUE_PASSWORD": queue_password,
        "MESSAGE_QUEUE_QUEUE": queue_queues,
        "BATCH_SIZE": batch_size or "50",
        "LOG_LEVEL": log_level or "WARNING",
    }  # type: ignore , python does not recognise the not all() check as not allowing any None values.


def get_database(connection_string: str, database_name: str):
    client = MongoClient(connection_string)
    return client[database_name]


def setup_logging(loglevel):
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler(sys.stdout)
    logger.setLevel(loglevel)
    handler.setLevel(loglevel)
    logger.addHandler(handler)
    return logger


def exit_worker(event: Event, logger: logging.Logger):
    logger.info("Stopping worker...")
    event.set()


def worker():
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

    db = get_database(config["DATABASE_HOST"], config["DATABASE_NAME"])
    event = Event()
    backoff = ExponentialBackoff(sleeper=event)

    killer_callback = functools.partial(exit_worker, event=event, logger=logger)
    killer = GracefulKiller(killer_callback)

    collection = db[config["DATABASE_COLLECTION"]]

    # Sleep for a random amount of time to offset replicated workers.
    event.wait(random.randint(1, 10))
    
    logger.info("Worker setup finished, starting worker...")
    failures = 0
    while not killer.kill_now:
        try:
            objectsToUpdate = list(
                collection.find(
                    {
                        "$or": [
                            {
                                "last_update": {
                                    "$lt": dt.datetime.now(dt.UTC)
                                    - dt.timedelta(
                                        seconds=float(config["REFRESH_RATE"])
                                    )
                                }
                            },
                            {"last_update": None},
                        ]
                    }
                ).limit(int(config["BATCH_SIZE"]))
            )
            if len(objectsToUpdate) > 0:
                backoff.clear()
                for object in objectsToUpdate:
                    channel.basic_publish(
                        exchange="", routing_key=queuename, body=str(object["_id"])
                    )
                    collection.update_one(
                        {"_id": object["_id"]},
                        {"$set": {"last_update": dt.datetime.now(dt.UTC)}},
                    )
                logger.info(f"Added {len(objectsToUpdate)} objects to the queue.")
            else:
                logger.info(
                    f"Nothing to do, sleeping for {backoff.currentTime} seconds..."
                )
                backoff.sleep()
                backoff.increase()
            failures = 0
        except Exception as ex:
            logger.error(f"Error: {ex}")
            failures += 1
            if failures >= 3:
                exit(1)
            logger.info(f"Sleeping for {backoff.maxTime} seconds...")
            backoff.sleep(backoff.maxTime)
    queue_connection.close()
    db.client.close()
    logger.info("Worker exited succesfully!")


if __name__ == "__main__":
    worker()
