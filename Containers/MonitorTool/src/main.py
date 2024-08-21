import os
import csv
from flask import Flask, render_template, redirect, url_for
from pymongo import MongoClient
import requests
import threading
import json
import datetime
import pandas as pd
import base64
from io import BytesIO
from matplotlib.figure import Figure

UPDATE_INTERVAL = int(os.getenv("UPDATE_INTERVAL", 5))
PORT = 5000

app = Flask(__name__, instance_relative_config=True)

app.config.from_mapping(DB_HOST=os.getenv("DB_HOST"), DB_NAME=os.getenv("DB_NAME"))


@app.route("/reset")
def reset():
    with app.open_instance_resource("current_stats.json", "w") as f:
        pass
    with app.open_instance_resource("history.csv", "w") as f:
        pass
    return redirect(url_for("index"))


@app.route("/")
def index():
    with app.open_instance_resource("current_stats.json", "r") as f:
        try:
            current_stats = json.load(f)
        except json.JSONDecodeError:
            current_stats = {"files": 0, "chunks": 0, "candidates": 0, "clones": 0}
    with app.open_instance_resource("history.csv", "r") as f:
        try:
            df = pd.read_csv(f, parse_dates=['timestamp'])
        except pd.errors.EmptyDataError:
            df = pd.DataFrame(
                {
                    "timestamp": [datetime.datetime.now(datetime.UTC)],
                    "files": [0],
                    "chunks": [0],
                    "candidates": [0],
                    "clones": [0],
                }
            )
    fig = Figure(figsize=(12, 12))
    ax = fig.subplots(4, 1)
    for idx, data in enumerate(['files', 'chunks', 'candidates', 'clones']):
        ax[idx].plot(df[(df[data] > 0) & (~df[data].diff(2).eq(0))]["timestamp"], df[(df[data] > 0) & (~df[data].diff(2).eq(0))][data])
        ax[idx].set_title(f'{data.capitalize()} processed')
        ax[idx].set_xlabel('Time (UTC)')
        ax[idx].set_ylabel(data.capitalize())
        ax[idx].legend([data.capitalize()])
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png")
    plot = base64.b64encode(buf.getbuffer()).decode("ascii")
    db = get_database(app.config["DB_HOST"], app.config["DB_NAME"])
    logs_coll = db["statusUpdates"]
    logs = list(logs_coll.find())
    return render_template(
        "index.html", current_stats=current_stats, plot=f"data:image/png;base64,{plot}", logs=logs
    )


@app.route("/update-stats")
def update_stats():
    db = get_database(app.config["DB_HOST"], app.config["DB_NAME"])
    files = db["files"]
    chunks = db["chunks"]
    candidates = db["candidates"]
    clones = db["clones"]
    files_stats = files.count_documents({})
    chunks_stats = chunks.count_documents({})
    candidates_stats = candidates.count_documents({})
    clones_stats = clones.count_documents({})
    t = datetime.datetime.now(datetime.UTC)
    with app.open_instance_resource("current_stats.json", "w") as f:
        json.dump(
            {
                "files": files_stats,
                "chunks": chunks_stats,
                "candidates": candidates_stats,
                "clones": clones_stats,
            },
            f,
        )
    with app.open_instance_resource("history.csv", "a") as f:
        fieldnames = ["timestamp", "files", "chunks", "candidates", "clones"]
        writer = csv.DictWriter(f, fieldnames)
        if f.tell() == 0:
            writer.writeheader()
        writer.writerow(
            {
                "timestamp": t.isoformat(),
                "files": files_stats,
                "chunks": chunks_stats,
                "candidates": candidates_stats,
                "clones": clones_stats,
            }
        )
    return {"success": True}


def worker():
    requests.get(f"http://localhost:{PORT}/update-stats")
    threading.Timer(UPDATE_INTERVAL, worker).start()


def get_database(connection_string: str, database_name: str):
    client = MongoClient(connection_string)
    return client[database_name]


if __name__ == "__main__":
    threading.Timer(3, worker).start() # Allow time for MongoDB to start
    app.run(host="0.0.0.0", port=PORT)
