import os
import sys

import click
from dotenv import load_dotenv

from src.server import create_app
from src.server_utils.config import get_config

load_dotenv()


@click.group()
def main():
    """
    QR Code Tracker CLI - Manage QR code tracking application.
    """
    pass


@main.command()
@click.option("--host", default=None, help="Host to bind to")
@click.option("--port", default=None, type=int, help="Port to bind to")
@click.option("--debug/--no-debug", default=None, help="Enable/disable debug mode")
def run(host, port, debug):
    """
    Run the QR code tracker server.
    """
    if "SECRET_KEY" not in os.environ:
        click.echo("Error: SECRET_KEY environment variable must be set", err=True)
        sys.exit(1)
    if "DATABASE_URL" not in os.environ:
        click.echo("Error: DATABASE_URL environment variable must be set", err=True)
        sys.exit(1)

    app = create_app()
    config = get_config()
    server_config = config["server"]

    if host is None:
        host = server_config["host"]
    if port is None:
        port = server_config["port"]
    if debug is None:
        debug = int(os.environ.get("FLASK_DEBUG", "1")) == 1

    if debug:
        app.run(debug=True, host=host, port=port)
    else:
        from waitress import serve
        serve(app, host=host, port=port)


@main.group()
def db():
    """
    Database migration commands.
    """
    pass


@db.command()
def init():
    """
    Initialize database migrations.
    """
    load_dotenv()
    if "DATABASE_URL" not in os.environ:
        click.echo("Error: DATABASE_URL environment variable must be set", err=True)
        sys.exit(1)

    app = create_app()
    from flask_migrate import init

    with app.app_context():
        db_type = "sqlite" if "sqlite" in os.environ["DATABASE_URL"] else "postgres"
        init(directory=f"src/server_utils/migrations_{db_type}")
        click.echo(f"Initialized migrations for {db_type}")


@db.command()
def migrate():
    """
    Create a new migration.
    """
    load_dotenv()
    if "DATABASE_URL" not in os.environ:
        click.echo("Error: DATABASE_URL environment variable must be set", err=True)
        sys.exit(1)

    app = create_app()
    from flask_migrate import migrate

    with app.app_context():
        db_type = "sqlite" if "sqlite" in os.environ["DATABASE_URL"] else "postgres"
        migrate(directory=f"src/server_utils/migrations_{db_type}")
        click.echo(f"Created migration for {db_type}")


@db.command()
def upgrade():
    """
    Apply pending migrations.
    """
    load_dotenv()
    if "DATABASE_URL" not in os.environ:
        click.echo("Error: DATABASE_URL environment variable must be set", err=True)
        sys.exit(1)

    app = create_app()
    from flask_migrate import upgrade

    with app.app_context():
        db_type = "sqlite" if "sqlite" in os.environ["DATABASE_URL"] else "postgres"
        upgrade(directory=f"src/server_utils/migrations_{db_type}")
        click.echo(f"Applied migrations for {db_type}")


if __name__ == "__main__":
    main()
