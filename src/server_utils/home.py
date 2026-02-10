import json
import logging
import random
import string
from datetime import datetime
from typing import Union

from flask import Blueprint, jsonify, render_template, redirect, request, url_for, Response
from werkzeug.security import check_password_hash, generate_password_hash

from src.server_utils.config import get_config
from src.server_utils.db import Association, Stats, Impression
from src.server_utils.shared import db

config = get_config()
key_config = config["key_generation"]

home_pages = Blueprint('home',
                       __name__,
                       template_folder='templates',
                       static_folder='static')

public_pages = Blueprint('public',
                         __name__,
                         template_folder='templates',
                         static_folder='static')

admin_pages = Blueprint('admin',
                        __name__,
                        template_folder='templates',
                        static_folder='static')


@admin_pages.route("/", methods=["GET"])
@home_pages.route("/", methods=["GET"])
def index() -> str:
    """
    Render the main page with QR code generation form.
    
    Returns:
        str: Rendered HTML template
    """
    qr_config = config.get("qr_code", {})
    return render_template("index.html", qr_config=qr_config)


@public_pages.route("/qr/<id>", methods=["GET"])
@home_pages.route("/qr/<id>", methods=["GET"])
def get(id: str) -> Union[str, Response]:
    """
    Handle QR code redirect and record impression.
    
    Args:
        id: QR code key identifier
        
    Returns:
        Union[str, Response]: Error page if not found, redirect to target URL otherwise
    """
    association = Association.query.filter_by(key=id).first()

    if association is None:
        return render_template("error.html", id=id)

    stats = Stats.query.filter_by(key=id).first()
    
    if stats is None:
        logging.error(f"Stats not found for key: {id}")
        return render_template("error.html", id=id)
    
    url = association.url
    new_impression = Impression(datetime.now())
    new_impression.stats_id = stats.id
    stats.impressions.append(new_impression)
    db.session.add(new_impression)
    db.session.commit()
    
    logging.info(f"Recorded impression for key {id}, stats_id: {stats.id}, impression stats_id: {new_impression.stats_id}")

    if url.find("http://") != 0 and url.find("https://") != 0:
        url = "https://" + url

    return redirect(url)


@admin_pages.route("/qr/<id>/stats", methods=["GET", "POST"])
@home_pages.route("/qr/<id>/stats", methods=["GET", "POST"])
def stats(id: str) -> str:
    """
    Display statistics page for a QR code.
    
    Args:
        id: QR code key identifier
        
    Returns:
        str: Rendered HTML template with statistics
    """
    association = Association.query.filter_by(key=id).first()
    stats = Stats.query.filter_by(key=id).first()

    if association is None or stats is None:
        return render_template("error.html", id=id)

    has_password = stats.password is not None
    received_password = request.form.get("password", None)
    if has_password and received_password is None:
        return render_template("password.html", id=id)
    elif has_password and not check_password_hash(stats.password, received_password):
        return render_template("generic_error.html", error_message="Incorrect password! Refresh the page to try again.")

    # Generate public QR code URL using public port (do this early so it's always available)
    server_config = config.get("server", {})
    public_port = server_config.get("public_port", 8082)
    try:
        public_host = request.host.split(':')[0]
    except (AttributeError, ValueError):
        public_host = request.remote_addr if hasattr(request, 'remote_addr') else 'localhost'
    scheme = 'https' if request.is_secure else 'http'
    public_qr_url = f"{scheme}://{public_host}:{public_port}/qr/{id}"

    url = association.url
    counter = len(stats.impressions)

    datetimes = [impression.datetime for impression in stats.impressions]
    datetimes.sort()

    # Merge stored QR style config with config.toml defaults
    default_qr_config = config.get("qr_code", {})
    stored_qr_config = association.get_qr_style_config()
    
    if stored_qr_config:
        # Start with defaults and override with stored values
        qr_config = default_qr_config.copy()
        qr_config.update(stored_qr_config)
    else:
        # Use defaults only
        qr_config = default_qr_config

    if counter == 0:
        return render_template("stats.html", url=url, counter=counter, has_data=False, id=id, qr_config=qr_config, has_password=has_password, public_qr_url=public_qr_url)
    elif counter == 1:
        return render_template("stats.html", url=url, counter=counter, has_data=False, date=datetimes[0], id=id, qr_config=qr_config, has_password=has_password, public_qr_url=public_qr_url)

    return render_template("stats.html", url=url, counter=counter, has_data=True, id=id, qr_config=qr_config, has_password=has_password, public_qr_url=public_qr_url)


@admin_pages.route("/qr/<id>/stats/data", methods=["GET"])
@home_pages.route("/qr/<id>/stats/data", methods=["GET"])
def stats_data(id: str) -> Response:
    """
    API endpoint returning impression data as JSON.
    
    Args:
        id: QR code key identifier
        
    Returns:
        Response: JSON response with impression datetimes and count
    """
    stats = Stats.query.filter_by(key=id).first()

    if stats is None:
        return jsonify({"error": "Stats not found"}), 404

    datetimes = [impression.datetime.isoformat() for impression in stats.impressions]
    datetimes.sort()

    return jsonify({
        "datetimes": datetimes,
        "count": len(datetimes)
    })


@admin_pages.route("/qr/<id>/stats/update-style", methods=["POST"])
@home_pages.route("/qr/<id>/stats/update-style", methods=["POST"])
def update_style(id: str) -> Union[str, Response]:
    """
    Update QR code style configuration.
    
    Args:
        id: QR code key identifier
        
    Returns:
        Union[str, Response]: Error page if validation fails, redirect to stats page otherwise
    """
    association = Association.query.filter_by(key=id).first()
    stats = Stats.query.filter_by(key=id).first()

    if association is None or stats is None:
        return render_template("error.html", id=id)

    has_password = stats.password is not None
    received_password = request.form.get("password", None)
    # Normalize empty string to None
    if received_password == "":
        received_password = None
    
    if has_password:
        if received_password is None:
            return render_template("password.html", id=id)
        elif not check_password_hash(stats.password, received_password):
            return render_template("generic_error.html", error_message="Incorrect password! Please try again.")

    # Extract QR styling options from form (same logic as generate function)
    qr_style_config = {}
    
    # Basic options
    if request.form.get("qr_style_width"):
        try:
            qr_style_config["width"] = int(request.form.get("qr_style_width"))
        except ValueError:
            pass
    
    if request.form.get("qr_style_height"):
        try:
            qr_style_config["height"] = int(request.form.get("qr_style_height"))
        except ValueError:
            pass
    
    if request.form.get("qr_style_color_dark"):
        qr_style_config["color_dark"] = request.form.get("qr_style_color_dark")
    
    if request.form.get("qr_style_color_light"):
        qr_style_config["color_light"] = request.form.get("qr_style_color_light")
    
    if request.form.get("qr_style_dot_type"):
        qr_style_config["dot_type"] = request.form.get("qr_style_dot_type")
    
    if request.form.get("qr_style_margin"):
        try:
            qr_style_config["margin"] = int(request.form.get("qr_style_margin"))
        except ValueError:
            pass
    
    # Advanced options
    if request.form.get("qr_style_corner_square_type"):
        qr_style_config["corner_square_type"] = request.form.get("qr_style_corner_square_type")
    
    if request.form.get("qr_style_corner_dot_type"):
        qr_style_config["corner_dot_type"] = request.form.get("qr_style_corner_dot_type")
    
    if request.form.get("qr_style_logo_image", "").strip():
        qr_style_config["logo_image"] = request.form.get("qr_style_logo_image").strip()
    
    if request.form.get("qr_style_logo_size"):
        try:
            qr_style_config["logo_size"] = float(request.form.get("qr_style_logo_size"))
        except ValueError:
            pass
    
    if request.form.get("qr_style_logo_margin"):
        try:
            qr_style_config["logo_margin"] = int(request.form.get("qr_style_logo_margin"))
        except ValueError:
            pass
    
    if request.form.get("qr_style_gradient_type", "").strip():
        qr_style_config["gradient_type"] = request.form.get("qr_style_gradient_type").strip()
        if request.form.get("qr_style_gradient_color_start", "").strip():
            qr_style_config["gradient_color_start"] = request.form.get("qr_style_gradient_color_start").strip()
        if request.form.get("qr_style_gradient_color_end", "").strip():
            qr_style_config["gradient_color_end"] = request.form.get("qr_style_gradient_color_end").strip()
        if request.form.get("qr_style_gradient_rotation"):
            try:
                qr_style_config["gradient_rotation"] = int(request.form.get("qr_style_gradient_rotation"))
            except ValueError:
                pass
    
    if request.form.get("qr_style_background_gradient_type", "").strip():
        qr_style_config["background_gradient_type"] = request.form.get("qr_style_background_gradient_type").strip()
        if request.form.get("qr_style_background_gradient_color_start", "").strip():
            qr_style_config["background_gradient_color_start"] = request.form.get("qr_style_background_gradient_color_start").strip()
        if request.form.get("qr_style_background_gradient_color_end", "").strip():
            qr_style_config["background_gradient_color_end"] = request.form.get("qr_style_background_gradient_color_end").strip()
        if request.form.get("qr_style_background_gradient_rotation"):
            try:
                qr_style_config["background_gradient_rotation"] = int(request.form.get("qr_style_background_gradient_rotation"))
            except ValueError:
                pass
    
    if request.form.get("qr_style_correct_level"):
        qr_style_config["correct_level"] = request.form.get("qr_style_correct_level")

    # Update association with new style config
    if qr_style_config:
        association.qr_style_config = json.dumps(qr_style_config)
    else:
        association.qr_style_config = None
    
    db.session.commit()
    logging.info(f"Updated QR style config for key {id}")

    return redirect(url_for("admin.stats", id=id))


@admin_pages.route("/qr/<id>/stats/reset", methods=["POST"])
@home_pages.route("/qr/<id>/stats/reset", methods=["POST"])
def reset_stats(id: str) -> Union[str, Response]:
    """
    Reset stats by deleting all impressions.
    
    Args:
        id: QR code key identifier
        
    Returns:
        Union[str, Response]: Error page if validation fails, redirect to stats page otherwise
    """
    association = Association.query.filter_by(key=id).first()
    stats = Stats.query.filter_by(key=id).first()

    if association is None or stats is None:
        return render_template("error.html", id=id)

    has_password = stats.password is not None
    received_password = request.form.get("password", None)
    # Normalize empty string to None
    if received_password == "":
        received_password = None
    
    if has_password:
        if received_password is None:
            return render_template("password.html", id=id)
        elif not check_password_hash(stats.password, received_password):
            return render_template("generic_error.html", error_message="Incorrect password! Please try again.")

    # Delete all impressions
    for impression in stats.impressions:
        db.session.delete(impression)
    
    db.session.commit()
    logging.info(f"Reset stats for key {id}")

    return redirect(url_for("admin.stats", id=id))


@admin_pages.route("/qr/<id>/stats/delete", methods=["POST"])
@home_pages.route("/qr/<id>/stats/delete", methods=["POST"])
def delete_entry(id: str) -> Union[str, Response]:
    """
    Delete the entire QR code entry (Association, Stats, and all Impressions).
    
    Args:
        id: QR code key identifier
        
    Returns:
        Union[str, Response]: Error page if validation fails, redirect to home page otherwise
    """
    association = Association.query.filter_by(key=id).first()
    stats = Stats.query.filter_by(key=id).first()

    if association is None or stats is None:
        return render_template("error.html", id=id)

    has_password = stats.password is not None
    received_password = request.form.get("password", None)
    # Normalize empty string to None
    if received_password == "":
        received_password = None
    
    if has_password:
        if received_password is None:
            return render_template("password.html", id=id)
        elif not check_password_hash(stats.password, received_password):
            return render_template("generic_error.html", error_message="Incorrect password! Please try again.")

    # Delete all impressions first (they reference stats)
    for impression in stats.impressions:
        db.session.delete(impression)
    
    # Delete stats (it references association)
    db.session.delete(stats)
    
    # Delete association
    db.session.delete(association)
    
    db.session.commit()
    logging.info(f"Deleted entry for key {id}")

    return redirect(url_for("admin.index"))


@admin_pages.route("/", methods=["POST"])
@home_pages.route("/", methods=["POST"])
def generate() -> Union[str, Response]:
    """
    Generate a new QR code association.
    
    Returns:
        Union[str, Response]: Error page if key exists, redirect to stats page otherwise
    """
    url = request.form["url"]
    key = request.form.get("key", "").strip()
    password = request.form.get("password", None)

    if not key:
        already_exists = True
        valid_chars = key_config["valid_characters"]
        char_set = ""
        if "ascii_lowercase" in valid_chars:
            char_set += string.ascii_lowercase
        if "digits" in valid_chars:
            char_set += string.digits
        if "ascii_uppercase" in valid_chars:
            char_set += string.ascii_uppercase
        key_length = key_config["length"]
        attempts = 0
        max_attempts = 100
        while already_exists and attempts < max_attempts:
            key = "".join(random.choice(char_set) for i in range(key_length))
            already_exists = Association.query.filter_by(key=key).first() is not None
            attempts += 1
        
        if attempts >= max_attempts:
            logging.error("Failed to generate unique key after maximum attempts")
            qr_config = config.get("qr_code", {})
            return render_template("index.html", error="Failed to generate unique key. Please try again.", url=url, qr_config=qr_config)
    else:
        already_exists = Association.query.filter_by(key=key).first() is not None
        if already_exists:
            qr_config = config.get("qr_code", {})
            return render_template("index.html", error="Key already exists.", url=url, qr_config=qr_config)

    # Extract QR styling options from form
    qr_style_config = {}
    default_qr_config = config.get("qr_code", {})
    
    # Basic options
    if request.form.get("qr_style_width"):
        try:
            qr_style_config["width"] = int(request.form.get("qr_style_width"))
        except ValueError:
            pass
    
    if request.form.get("qr_style_height"):
        try:
            qr_style_config["height"] = int(request.form.get("qr_style_height"))
        except ValueError:
            pass
    
    if request.form.get("qr_style_color_dark"):
        qr_style_config["color_dark"] = request.form.get("qr_style_color_dark")
    
    if request.form.get("qr_style_color_light"):
        qr_style_config["color_light"] = request.form.get("qr_style_color_light")
    
    if request.form.get("qr_style_dot_type"):
        qr_style_config["dot_type"] = request.form.get("qr_style_dot_type")
    
    if request.form.get("qr_style_margin"):
        try:
            qr_style_config["margin"] = int(request.form.get("qr_style_margin"))
        except ValueError:
            pass
    
    # Advanced options
    if request.form.get("qr_style_corner_square_type"):
        qr_style_config["corner_square_type"] = request.form.get("qr_style_corner_square_type")
    
    if request.form.get("qr_style_corner_dot_type"):
        qr_style_config["corner_dot_type"] = request.form.get("qr_style_corner_dot_type")
    
    if request.form.get("qr_style_logo_image", "").strip():
        qr_style_config["logo_image"] = request.form.get("qr_style_logo_image").strip()
    
    if request.form.get("qr_style_logo_size"):
        try:
            qr_style_config["logo_size"] = float(request.form.get("qr_style_logo_size"))
        except ValueError:
            pass
    
    if request.form.get("qr_style_logo_margin"):
        try:
            qr_style_config["logo_margin"] = int(request.form.get("qr_style_logo_margin"))
        except ValueError:
            pass
    
    if request.form.get("qr_style_gradient_type", "").strip():
        qr_style_config["gradient_type"] = request.form.get("qr_style_gradient_type").strip()
        if request.form.get("qr_style_gradient_color_start", "").strip():
            qr_style_config["gradient_color_start"] = request.form.get("qr_style_gradient_color_start").strip()
        if request.form.get("qr_style_gradient_color_end", "").strip():
            qr_style_config["gradient_color_end"] = request.form.get("qr_style_gradient_color_end").strip()
        if request.form.get("qr_style_gradient_rotation"):
            try:
                qr_style_config["gradient_rotation"] = int(request.form.get("qr_style_gradient_rotation"))
            except ValueError:
                pass
    
    if request.form.get("qr_style_background_gradient_type", "").strip():
        qr_style_config["background_gradient_type"] = request.form.get("qr_style_background_gradient_type").strip()
        if request.form.get("qr_style_background_gradient_color_start", "").strip():
            qr_style_config["background_gradient_color_start"] = request.form.get("qr_style_background_gradient_color_start").strip()
        if request.form.get("qr_style_background_gradient_color_end", "").strip():
            qr_style_config["background_gradient_color_end"] = request.form.get("qr_style_background_gradient_color_end").strip()
        if request.form.get("qr_style_background_gradient_rotation"):
            try:
                qr_style_config["background_gradient_rotation"] = int(request.form.get("qr_style_background_gradient_rotation"))
            except ValueError:
                pass
    
    if request.form.get("qr_style_correct_level"):
        qr_style_config["correct_level"] = request.form.get("qr_style_correct_level")

    # Only store non-empty config
    qr_style_config_to_store = qr_style_config if qr_style_config else None

    association = Association(key, url, qr_style_config_to_store)
    stats = Stats(key, generate_password_hash(password) if password is not None else None)
    association.stats = stats

    db.session.add(association)
    db.session.add(stats)
    db.session.commit()

    logging.info(f"Generated key {key} for url {url}.")
    
    stats_url = url_for("admin.stats", id=key)
    logging.info(f"Redirecting to: {stats_url}")
    return redirect(stats_url)
