.PHONY: setup build start stop restart logs test migrate create-superuser clean help collectstatic rebuild-all

help:
	@echo "Sepolia ETH Faucet Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make setup         - Create .env file from .env.example"
	@echo "  make build         - Build Docker containers"
	@echo "  make start         - Start the application"
	@echo "  make stop          - Stop the application"
	@echo "  make restart       - Restart the application"
	@echo "  make logs          - View application logs"
	@echo "  make test          - Run tests"
	@echo "  make migrate       - Apply database migrations"
	@echo "  make makemigrations - Create database migrations"
	@echo "  make superuser     - Create a superuser"
	@echo "  make collectstatic - Collect static files"
	@echo "  make rebuild-all   - Complete rebuild of the application"
	@echo "  make clean         - Remove all containers and volumes"
	@echo ""

setup:
	@echo "Creating .env file from .env.example..."
	@if [ ! -f .env ]; then cp .env.example .env && echo ".env file created. Please update it with your credentials."; else echo ".env file already exists."; fi

build:
	@echo "Building Docker containers..."
	docker-compose build

start:
	@echo "Starting the application..."
	docker-compose up -d
	@echo "Application is running at http://localhost:8000/"
	@echo "Admin interface available at http://localhost:8000/admin/"

stop:
	@echo "Stopping the application..."
	docker-compose down

restart: stop start

logs:
	@echo "Showing application logs..."
	docker-compose logs -f

test:
	@echo "Running tests..."
	docker-compose exec web python manage.py test

migrate:
	@echo "Applying database migrations..."
	docker-compose exec web python manage.py migrate

makemigrations:
	@echo "Creating database migrations..."
	docker-compose exec web python manage.py makemigrations faucet

superuser:
	@echo "Creating a superuser..."
	docker-compose exec web python manage.py createsuperuser

collectstatic:
	@echo "Collecting static files..."
	docker-compose exec web python manage.py collectstatic --noinput

clean:
	@echo "Removing all containers and volumes..."
	docker-compose down -v
	@echo "Containers and volumes removed."

rebuild-all: clean
	@echo "Performing complete rebuild..."
	docker-compose build --no-cache
	docker-compose up -d
	docker-compose exec web python manage.py migrate
	docker-compose exec web python manage.py collectstatic --noinput
	@echo "Rebuild complete. Admin interface available at http://localhost:8000/admin/"

all: setup build start