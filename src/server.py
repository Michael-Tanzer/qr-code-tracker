import logging
import os
from logging.config import dictConfig

from flask import Flask, request, session
from flask_migrate import Migrate, init, migrate, upgrade

from src.server_utils.home import home_pages


dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] [%(levelname)s] %(message)s",
                "datefmt": "%B %d, %Y %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
            },
            "file": {
                "class": "logging.FileHandler",
                "filename": "logs.log",
                "formatter": "default",
            },
        },
        "root": {"level": "DEBUG", "handlers": ["console", "file"]},
    }
)


def create_app():
    assert "SECRET_KEY" in os.environ

    app = Flask(__name__)

    app.config['DEBUG'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config["SECRET_KEY"] = os.environ.get('SECRET_KEY', 'dev')

    from src.server_utils.shared import db

    db.init_app(app)
    with app.app_context():
        db.create_all()

    migrate = Migrate(app, db)

    app.register_blueprint(home_pages)
    return app


if __name__ == '__main__':
    assert "FLASK_DEBUG" in os.environ

    app = create_app()

    if "MIGRATE_CMD" in os.environ:
        command = os.environ["MIGRATE_CMD"]
        with app.app_context():
            if command == "init":
                logging.info("Initializing database")
                init(directory=f"server_utils/migrations_{'sqlite' if 'sqlite' in os.environ['DATABASE_URL'] else 'postgres'}")
                exit(0)
            elif command == "migrate":
                logging.info("Migrating database")
                migrate(directory=f"server_utils/migrations_{'sqlite' if 'sqlite' in os.environ['DATABASE_URL'] else 'postgres'}")
                exit(0)
            elif command == "upgrade":
                logging.info("Upgrading database")
                upgrade(directory=f"server_utils/migrations_{'sqlite' if 'sqlite' in os.environ['DATABASE_URL'] else 'postgres'}")
                exit(0)
            else:
                raise ValueError(f"Unknown migration command: {command}")

    @app.before_request
    def log_before_request():
        app.logger.info(
            f"path: {request.path} | method: {request.method} | session: {session}"
        )

    @app.after_request
    def log_after_request(response):
        app.logger.info(
            f"path: {request.path} | "
            f"method: {request.method} | "
            f"status: {response.status} | "
            f"size:{response.content_length} | "
            f"session: {session}",
        )

        return response

    if int(os.environ.get("FLASK_DEBUG", "1")):
        app.run(debug=True, host="0.0.0.0")
    else:
        from waitress import serve
        serve(app, host="0.0.0.0", port=5000)
