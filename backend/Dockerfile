# Build context is the repo root (see docker-compose.yml), since
# requirements.txt lives there rather than inside backend/.
FROM python:3.12-slim

WORKDIR /app

# System deps needed to build psycopg2-binary / common wheels
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

ENV FLASK_ENV=production \
    FLASK_APP=app \
    PORT=5000

EXPOSE 5000

# flask db upgrade runs at container start so the image works against
# a fresh database without a manual migration step. flask seed-admin
# creates a first admin login from ADMIN_EMAIL/ADMIN_PASSWORD env vars
# if it doesn't already exist — safe to run on every deploy, and needed
# since shell access isn't available on the free instance type.
CMD ["sh", "-c", "flask db upgrade && flask seed-admin && gunicorn -b 0.0.0.0:${PORT} 'app:create_app()'"]
