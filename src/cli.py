import os
import sys
import threading

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
@click.option("--mode", type=click.Choice(["public", "admin", "both"], case_sensitive=False), default="both", help="Server mode: public (redirect only), admin (management only), or both (default)")
def run(host, port, debug, mode):
    """
    Run the QR code tracker server.
    """
    if "SECRET_KEY" not in os.environ:
        click.echo("Error: SECRET_KEY environment variable must be set", err=True)
        sys.exit(1)
    if "DATABASE_URL" not in os.environ:
        click.echo("Error: DATABASE_URL environment variable must be set", err=True)
        sys.exit(1)

    config = get_config()
    server_config = config["server"]

    if host is None:
        host = server_config["host"]
    if debug is None:
        debug = int(os.environ.get("FLASK_DEBUG", "1")) == 1

    if mode == "both":
        public_port = server_config.get("public_port", 8082)
        admin_port = server_config.get("admin_port", 6063)
        
        if port is not None:
            click.echo("Warning: --port option ignored when --mode=both. Using public_port and admin_port from config.", err=True)
        
        def run_public():
            app_public = create_app(mode="public")
            if debug:
                app_public.run(debug=False, host=host, port=public_port, use_reloader=False)
            else:
                from waitress import serve
                serve(app_public, host=host, port=public_port)
        
        def run_admin():
            app_admin = create_app(mode="admin")
            if debug:
                app_admin.run(debug=debug, host=host, port=admin_port, use_reloader=False)
            else:
                from waitress import serve
                serve(app_admin, host=host, port=admin_port)
        
        click.echo(f"Starting public server on port {public_port}...")
        click.echo(f"Starting admin server on port {admin_port}...")
        
        thread_public = threading.Thread(target=run_public, daemon=True)
        thread_admin = threading.Thread(target=run_admin, daemon=True)
        
        thread_public.start()
        thread_admin.start()
        
        try:
            thread_public.join()
            thread_admin.join()
        except KeyboardInterrupt:
            click.echo("\nShutting down servers...")
            sys.exit(0)
    else:
        app = create_app(mode=mode)
        
        if port is None:
            if mode == "public":
                port = server_config.get("public_port", 8082)
            else:
                port = server_config.get("admin_port", 6063)

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
