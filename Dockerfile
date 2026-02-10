FROM python:3.11-slim

WORKDIR /app

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Create directory for database and logs with proper permissions
RUN mkdir -p /app/data /app/logs && \
    chmod 755 /app/data /app/logs

# Expose port
EXPOSE 6063

# Set environment variables for production
ENV FLASK_DEBUG=0
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["uv", "run", "qr-tracker", "run", "--host", "0.0.0.0", "--port", "6063"]
