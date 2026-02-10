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

5. Build and start the containers:

```bash
docker-compose up -d
```

The application runs two services:
- **Public service** (port 8082): Handles QR code redirects - accessible from the internet
- **Admin service** (port 6063): Handles QR code creation and management - should be VPN-only

Both services share the same database and are available at their respective ports.

#### Docker Commands

- View logs for both services: `docker-compose logs -f`
- View logs for a specific service: `docker-compose logs -f qr-tracker-public` or `docker-compose logs -f qr-tracker-admin`
- Stop all containers: `docker-compose down`
- Restart all containers: `docker-compose restart`
- Restart a specific service: `docker-compose restart qr-tracker-public` or `docker-compose restart qr-tracker-admin`
- Rebuild after code changes: `docker-compose up -d --build`

#### Database Migrations with Docker

Run migrations inside either container (both share the same database):

```bash
docker-compose exec qr-tracker-admin uv run qr-tracker db upgrade
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

3. Optional: Edit `config.toml` to customize application settings:
   - `server.public_port`: Port for the public redirect service (default: 8082)
   - `server.admin_port`: Port for the admin management service (default: 6063)
   - Other settings: key generation, QR code settings, etc.

### Running the Application

#### Using the CLI (Recommended)

Run both services (public and admin) simultaneously:

```bash
uv run qr-tracker run
```

Or run a specific mode:

```bash
# Public service only (redirect endpoint)
uv run qr-tracker run --mode public --port 8082

# Admin service only (management endpoints)
uv run qr-tracker run --mode admin --port 6063

# Both services (default)
uv run qr-tracker run --mode both
```

With custom options:

```bash
uv run qr-tracker run --host 127.0.0.1 --port 8080 --debug --mode admin
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

Navigate to `localhost:6063` (admin port) in your web browser to generate a QR code. The public redirect endpoint is available on port 8082.

## Deployment

### Docker (Self-Hosted)

See the [Docker Deployment](#docker-deployment-recommended-for-self-hosting) section above for instructions on deploying with Docker.

### Manual Deployment

For production deployment without Docker:

1. Set `FLASK_DEBUG=0` in your `.env` file
2. Use a production WSGI server (the app uses Waitress when `FLASK_DEBUG=0`)
3. Run both services: `uv run qr-tracker run --mode both`
4. Consider using a reverse proxy (nginx, Caddy, etc.) in front of the application
5. Set up proper SSL/TLS certificates
6. Configure firewall rules to only expose necessary ports

### Firewall and VPN Setup

The application uses a two-port architecture for security:

- **Port 8082 (Public)**: Handles QR code redirects (`/qr/<id>`). This port should be accessible from the internet.
- **Port 6063 (Admin)**: Handles all management endpoints (create QR codes, view stats, delete entries). This port should be **blocked from public access** and only accessible via VPN (e.g., Tailscale).

#### Tailscale Firewall Rules Example

If using Tailscale, configure firewall rules to:
- Allow inbound traffic to port 8082 from any source (for QR redirects)
- Block inbound traffic to port 6063 from non-Tailscale sources
- Allow inbound traffic to port 6063 only from Tailscale network

This ensures that:
- QR code redirects work for anyone scanning the code
- Management functions are only accessible when connected to your VPN

## Usage

On the web form, enter the following details:
- `URL`: The URL you would like to associate with the QR code.
- `Key`: The key you would like to use to associate views with the QR code.

Pressing "Generate" will create a QR code that routes to an intermediary website where views are recorded and plotted over time. 

## Credits

This project was created by Michael Tanzer and is available for free use under the MIT license. Please feel free to contribute to this repo to help improve it.

## Online Version

An online version of this project is available at [https://michaeltanzer.pythonanywhere.com/](https://michaeltanzer.pythonanywhere.com/).