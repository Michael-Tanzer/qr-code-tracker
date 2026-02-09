import logging
import os
from logging.config import dictConfig

from dotenv import load_dotenv
from flask import Flask, request, session
from flask_migrate import Migrate, init, migrate, upgrade

from src.server_utils.config import get_config
from src.server_utils.home import home_pages

load_dotenv()

config = get_config()
log_config = config["logging"]

dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": log_config["format"],
                "datefmt": log_config["date_format"],
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
            },
            "file": {
                "class": "logging.FileHandler",
                "filename": log_config["filename"],
                "formatter": "default",
            },
        },
        "root": {"level": log_config["level"], "handlers": ["console", "file"]},
    }
)


def create_app():
    """
    Create and configure the Flask application.
    
    Returns:
        Flask: Configured Flask application instance
    """
    assert "SECRET_KEY" in os.environ

    app = Flask(__name__)

    app.config['DEBUG'] = True
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url and database_url.startswith('sqlite:///'):
        db_path = database_url.replace('sqlite:///', '')
        if not os.path.isabs(db_path):
            project_root = os.path.dirname(os.path.dirname(__file__))
            db_path = os.path.join(project_root, db_path)
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        database_url = f'sqlite:///{db_path}'
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
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
                init(directory=f"src/server_utils/migrations_{'sqlite' if 'sqlite' in os.environ['DATABASE_URL'] else 'postgres'}")
                exit(0)
            elif command == "migrate":
                logging.info("Migrating database")
                migrate(directory=f"src/server_utils/migrations_{'sqlite' if 'sqlite' in os.environ['DATABASE_URL'] else 'postgres'}")
                exit(0)
            elif command == "upgrade":
                logging.info("Upgrading database")
                upgrade(directory=f"src/server_utils/migrations_{'sqlite' if 'sqlite' in os.environ['DATABASE_URL'] else 'postgres'}")
                exit(0)
            else:
                raise ValueError(f"Unknown migration command: {command}")

    @app.before_request
    def log_before_request():
        """
        Log request details before processing.
        """
        app.logger.info(
            f"path: {request.path} | method: {request.method} | session: {session}"
        )

    @app.after_request
    def log_after_request(response):
        """
        Log response details after processing.
        
        Args:
            response: Flask response object
            
        Returns:
            Response: The response object
        """
        app.logger.info(
            f"path: {request.path} | "
            f"method: {request.method} | "
            f"status: {response.status} | "
            f"size:{response.content_length} | "
            f"session: {session}",
        )

        return response

    server_config = config["server"]
    if int(os.environ.get("FLASK_DEBUG", "1")):
        app.run(debug=True, host=server_config["host"])
    else:
        from waitress import serve
        serve(app, host=server_config["host"], port=server_config["port"])
