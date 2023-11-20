import os
import pika
from dataclasses import dataclass
from threading import Event
import datetime as dt
import json

from pymongo import MongoClient

from gracefull_killer import GracefulKiller


@dataclass
class ExponentialBackoff:
    minTime: int = 1
    maxTime: int = 30
    currentTime: int = minTime
    factor: int = 2
    sleeper: Event = Event()

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

    return {
        "CWORKER_DATABASE_HOST": dbservice or "",
        "CWORKER_DATABASE_NAME": dbname or "CommunityMainDB",
        "CWORKER_REFRESH_RATE": refreshRate or "300",
        "CWORKER_MESSAGE_QUEUE_HOST": queue_host or "localhost",
        "CWORKER_MESSAGE_QUEUE_USERNAME": queue_username or "",
        "CWORKER_MESSAGE_QUEUE_PASSWORD": queue_password or "",
        "CWORKER_MESSAGE_QUEUE_QUEUE": queue_queues or "update-community",
    }


def get_database(connection_string: str, database_name: str):
    client = MongoClient(connection_string)
    return client[database_name]


def worker() -> None:
    config = load_config()
    print(config)
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
    killer = GracefulKiller(event)

    collection = db["communities"]
    while not killer.kill_now:
        try:
            objectsToUpdate = list(
                collection.find(
                    {
                        "last_update": {
                            "$lt": dt.datetime.now(dt.UTC)
                            - dt.timedelta(
                                seconds=float(config["CWORKER_REFRESH_RATE"])
                            )
                        }
                    }
                )
            )
            if len(objectsToUpdate) > 0:
                backoff.clear()
                for object in objectsToUpdate:
                    channel.basic_publish(
                        exchange="", routing_key=queuename, body=json.dumps(object)
                    )
                    collection.update_one(
                        {"_id": object["_id"]}, {"last_update": dt.datetime.now(dt.UTC)}
                    )
            else:
                print(f"Nothing to do, sleeping for {backoff.currentTime} seconds...")
                backoff.sleep()
                backoff.increase()
        except Exception as ex:
            print(f"Error: {ex}")
            backoff.sleep(backoff.maxTime)


if __name__ == "__main__":
    worker()
