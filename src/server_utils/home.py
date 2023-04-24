import logging
import random
import string

from flask import Blueprint, render_template, redirect, request, jsonify, url_for

from src.server_utils.db import Association, Stats
from src.server_utils.shared import db

home_pages = Blueprint('home',
                       __name__,
                       template_folder='templates',
                       static_folder='static')


@home_pages.route("/", methods=["GET"])
def index() -> str:
    return render_template("index.html")


@home_pages.route("/qr/<id>", methods=["GET"])
def get(id: str) -> str:
    association = Association.query.filter_by(key=id).first()

    if association is None:
        return render_template("error.html", id=id)

    stats = Stats.query.filter_by(key=id).first()
    url = association.url
    stats.count += 1
    db.session.commit()

    if url.find("http://") != 0 and url.find("https://") != 0:
        url = "https://" + url

    return redirect(url)


@home_pages.route("/qr/<id>/stats", methods=["GET"])
def stats(id: str) -> str:
    association = Association.query.filter_by(key=id).first()
    stats = Stats.query.filter_by(key=id).first()
    url = association.url
    counter = stats.count
    return render_template("stats.html", url=url, counter=counter)


@home_pages.route("/", methods=["POST"])
def generate() -> str:
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

    db.session.add(association)
    db.session.add(stats)
    db.session.commit()

    logging.info(f"Generated key {key} for url {url}.")

    return redirect(url_for("home.stats", id=key))
