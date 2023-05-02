import base64
import io
import logging
import random
import string
from datetime import datetime
from urllib.parse import quote

from flask import Blueprint, render_template, redirect, request, url_for, Response
from matplotlib import ticker

import matplotlib.pyplot as plt

from src.server_utils.db import Association, Stats, Impression
from src.server_utils.shared import db

home_pages = Blueprint('home',
                       __name__,
                       template_folder='templates',
                       static_folder='static')


@home_pages.route("/", methods=["GET"])
def index() -> str:
    return render_template("index.html")


@home_pages.route("/qr/<id>", methods=["GET"])
def get(id: str) -> str | Response:
    association = Association.query.filter_by(key=id).first()

    if association is None:
        return render_template("error.html", id=id)

    stats = Stats.query.filter_by(key=id).first()
    url = association.url
    new_impression = Impression(datetime.now())
    stats.impressions.append(new_impression)
    db.session.commit()

    if url.find("http://") != 0 and url.find("https://") != 0:
        url = "https://" + url

    return redirect(url)


@home_pages.route("/qr/<id>/stats", methods=["GET"])
def stats(id: str) -> str:
    association = Association.query.filter_by(key=id).first()
    stats = Stats.query.filter_by(key=id).first()
    url = association.url
    counter = len(stats.impressions)

    datetimes = [impression.datetime for impression in stats.impressions]
    datetimes.sort()

    # get random mock datetimes for testing using random numbers
    # datetimes = [datetime.fromtimestamp(random.normalvariate(40000000 + 1600000000, 10000000)) for _ in range(500)]
    # datetimes += [datetime.fromtimestamp(random.normalvariate(40000000 + 1500000000, 10000000)) for _ in range(100)]
    # datetimes += [datetime.fromtimestamp(random.normalvariate(40000000 + 1400000000, 10000000)) for _ in range(200)]
    # datetimes.sort()
    # counter = len(datetimes)

    if counter == 0:
        return render_template("stats.html", url=url, counter=counter, plot_url=None)
    elif counter == 1:
        return render_template("stats.html", url=url, counter=counter, plot_url=None, date=datetimes[0])

    img = io.BytesIO()
    plt.figure(figsize=(10, 5))
    plt.step(datetimes + [datetimes[-1]], range(len(datetimes) + 1))
    plt.xlabel("Time")
    plt.ylabel("Impressions")
    plt.title("Impressions over time")

    # set x axis to be formatted as dates
    ticks = [datetimes[0], datetimes[-1]]

    if counter > 2:
        max_ticks = 11
        # add to the "ticks" list until we have enough ticks, take the ticks evenly spaced from the list
        available_ticks = datetimes[1:-1]
        distance_between_ticks = len(available_ticks) / (max_ticks - 2)
        for i in range(1, max_ticks - 2):
            new_tick = available_ticks[int(i * distance_between_ticks)]
            if new_tick not in ticks:
                ticks.append(available_ticks[int(i * distance_between_ticks)])
        ticks.sort()

    plt.xticks(ticks, rotation=45)
    # set y axis to be formatted as integers
    plt.gca().yaxis.set_major_formatter(ticker.FormatStrFormatter('%d'))
    plt.gca().yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    plt.grid()
    plt.tight_layout()
    plt.savefig(img, format='png', dpi=400)
    plt.close()
    img.seek(0)
    plot_url = quote(base64.b64encode(img.read()).decode())

    return render_template("stats.html", url=url, counter=counter, plot_url=plot_url)


@home_pages.route("/", methods=["POST"])
def generate() -> str | Response:
    url = request.form["url"]
    key = request.form.get("key", None)

    if key is None:
        # generate a unique key
        already_exists = True
        while already_exists:
            valid_characters = string.ascii_lowercase + string.digits + string.ascii_uppercase
            key = "".join(random.choice(valid_characters) for i in range(10))
            already_exists = Association.query.filter_by(key=key).first() is not None
    else:
        # check if key already exists
        already_exists = Association.query.filter_by(key=key).first() is not None
        if already_exists:
            return render_template("index.html", error="Key already exists.", url=url)

    association = Association(key, url)
    stats = Stats(key, 0)
    association.stats = stats

    db.session.add(association)
    db.session.add(stats)
    db.session.commit()

    logging.info(f"Generated key {key} for url {url}.")

    return redirect(url_for("home.stats", id=key))
