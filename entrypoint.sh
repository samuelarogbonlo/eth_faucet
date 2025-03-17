#!/bin/bash

# Wait for PostgreSQL to be available
echo "Waiting for PostgreSQL..."
python -c "
import time
import psycopg2
import os

host = os.environ.get('POSTGRES_HOST', 'db')
port = os.environ.get('POSTGRES_PORT', '5432')
user = os.environ.get('POSTGRES_USER', 'postgres')
password = os.environ.get('POSTGRES_PASSWORD', 'postgres')
dbname = os.environ.get('POSTGRES_DB', 'eth_faucet')

while True:
    try:
        conn = psycopg2.connect(
            f'dbname={dbname} user={user} password={password} host={host} port={port}'
        )
        conn.close()
        break
    except psycopg2.OperationalError:
        print('PostgreSQL not available yet. Waiting...')
        time.sleep(1)
"

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn server
echo "Starting Gunicorn server..."
gunicorn eth_faucet.wsgi:application --bind 0.0.0.0:8000