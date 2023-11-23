import os
import pika
from dataclasses import dataclass
from threading import Event
import datetime as dt
import logging
import sys
import functools

from pymongo import MongoClient

from gracefull_killer import GracefulKiller


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
    refreshRate = os.getenv("CWORKER_REFRESH_RATE")
    queue_host = os.getenv("CWORKER_MESSAGE_QUEUE_HOST")
    queue_username = os.getenv("CWORKER_MESSAGE_QUEUE_USERNAME")
    queue_password = os.getenv("CWORKER_MESSAGE_QUEUE_PASSWORD")
    queue_queues = os.getenv("CWORKER_MESSAGE_QUEUE_QUEUE")
    batch_size = os.getenv("CWORKER_BATCH_SIZE")
    log_level = os.getenv("CWORKER_LOG_LEVEL")

    return {
        "CWORKER_DATABASE_HOST": dbservice or "",
        "CWORKER_DATABASE_NAME": dbname or "CommunityMainDB",
        "CWORKER_REFRESH_RATE": refreshRate or "300",
        "CWORKER_MESSAGE_QUEUE_HOST": queue_host or "localhost",
        "CWORKER_MESSAGE_QUEUE_USERNAME": queue_username or "",
        "CWORKER_MESSAGE_QUEUE_PASSWORD": queue_password or "",
        "CWORKER_MESSAGE_QUEUE_QUEUE": queue_queues or "update-community",
        "CWORKER_BATCH_SIZE": batch_size or "50",
        "CWORKER_LOG_LEVEL": log_level or "WARNING",
    }


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

    logger = setup_logging(config["CWORKER_LOG_LEVEL"])
    logger.debug(config)

    connection_params = pika.ConnectionParameters(
        config["CWORKER_MESSAGE_QUEUE_HOST"],
        credentials=pika.PlainCredentials(
            config["CWORKER_MESSAGE_QUEUE_USERNAME"],
            config["CWORKER_MESSAGE_QUEUE_PASSWORD"],
        ),
    )
    queue_connection = pika.BlockingConnection(connection_params)
    channel = queue_connection.channel()

    queuename = config["CWORKER_MESSAGE_QUEUE_QUEUE"]
    channel.queue_declare(queuename)

    db = get_database(config["CWORKER_DATABASE_HOST"], config["CWORKER_DATABASE_NAME"])
    event = Event()
    backoff = ExponentialBackoff(sleeper=event)
    
    killer_callback = functools.partial(exit_worker, event=event, logger=logger)
    killer = GracefulKiller(killer_callback)

    collection = db["communities"]
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
                                        seconds=float(config["CWORKER_REFRESH_RATE"])
                                    )
                                }
                            },
                            {"last_update": None},
                        ]
                    }
                ).limit(int(config["CWORKER_BATCH_SIZE"]))
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
                logger.info(f"Added {len(objectsToUpdate)} objects to the queue...")
            else:
                logger.info(
                    f"Nothing to do, sleeping for {backoff.currentTime} seconds..."
                )
                backoff.sleep()
                backoff.increase()
        except Exception as ex:
            logger.error(f"Error: {ex}")
            backoff.sleep(backoff.maxTime)
    queue_connection.close()
    db.client.close()
    logger.info("Worker exited succesfully!")

if __name__ == "__main__":
    worker()
