# QR Code Views Tracker

QR Code Views Tracker is a simple web tool that allows you to generate a QR code that routes to an intermediary website where views are recorded and plotted over time.

![preview.png](preview.png)

## Setup

### Docker Deployment (Recommended for Self-Hosting)

#### Prerequisites

- Docker and Docker Compose installed on your server

#### Quick Start

1. Clone the repository and navigate to the project directory:

```bash
git clone <repository-url>
cd qr-code-tracker
```

2. Create a `.env` file:

```bash
cp .env.example .env
```

3. Edit `.env` and set the required environment variables:

- `DATABASE_URL`: For SQLite (default): `sqlite:///data/main_db.db`. For PostgreSQL: `postgresql://user:password@postgres:5432/qr_tracker`
- `FLASK_DEBUG`: Set to `0` for production
- `SECRET_KEY`: Generate a secure random key (e.g., `openssl rand -hex 32`)

4. Optional: Edit `config.toml` to customize application settings

5. Build and start the container:

```bash
docker-compose up -d
```

The application will be available at `http://localhost:5000` (or your server's IP address).

#### Docker Commands

- View logs: `docker-compose logs -f`
- Stop the container: `docker-compose down`
- Restart the container: `docker-compose restart`
- Rebuild after code changes: `docker-compose up -d --build`

#### Database Migrations with Docker

Run migrations inside the container:

```bash
docker-compose exec qr-tracker uv run qr-tracker db upgrade
```

#### Data Persistence

The Docker setup uses volumes to persist:
- Database files: `./data` directory
- Log files: `./logs` directory
- Configuration: `config.toml` (mounted as read-only)

### Local Development Setup

#### Prerequisites

- Python 3.8 or higher
- [UV](https://github.com/astral-sh/uv) package manager

#### Installation

1. Install dependencies using UV:

```bash
uv sync
```

This will install all required dependencies from `pyproject.toml`.

### Configuration

1. Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

2. Edit `.env` and set the required environment variables:

- `DATABASE_URL`: Path or URL to the database (e.g., `sqlite:///src/main_db.db` for SQLite or `postgresql://user:password@localhost/dbname` for PostgreSQL)
- `FLASK_DEBUG`: Set to `1` for development (uses Flask debug server) or `0` for production (uses waitress server)
- `SECRET_KEY`: Secret key for Flask sessions (generate a secure random key for production)

3. Optional: Edit `config.toml` to customize application settings (server host/port, key generation, QR code settings, etc.)

### Running the Application

#### Using the CLI (Recommended)

Run the server using the CLI command:

```bash
uv run qr-tracker run
```

Or with custom options:

```bash
uv run qr-tracker run --host 127.0.0.1 --port 8080 --debug
```

#### Database Migrations

Initialize migrations:

```bash
uv run qr-tracker db init
```

Create a new migration:

```bash
uv run qr-tracker db migrate
```

Apply migrations:

```bash
uv run qr-tracker db upgrade
```

#### Alternative: Direct Python Execution

You can also run the server directly:

```bash
uv run python src/server.py
```

Navigate to `localhost:5000` (or your configured port) in your web browser to generate a QR code.

## Deployment

### Docker (Self-Hosted)

See the [Docker Deployment](#docker-deployment-recommended-for-self-hosting) section above for instructions on deploying with Docker.

### Manual Deployment

For production deployment without Docker:

1. Set `FLASK_DEBUG=0` in your `.env` file
2. Use a production WSGI server (the app uses Waitress when `FLASK_DEBUG=0`)
3. Consider using a reverse proxy (nginx, Caddy, etc.) in front of the application
4. Set up proper SSL/TLS certificates
5. Configure firewall rules to only expose necessary ports

## Usage

On the web form, enter the following details:
- `URL`: The URL you would like to associate with the QR code.
- `Key`: The key you would like to use to associate views with the QR code.

Pressing "Generate" will create a QR code that routes to an intermediary website where views are recorded and plotted over time. 

## Credits

This project was created by Michael Tanzer and is available for free use under the MIT license. Please feel free to contribute to this repo to help improve it.

## Online Version

An online version of this project is available at [https://michaeltanzer.pythonanywhere.com/](https://michaeltanzer.pythonanywhere.com/).