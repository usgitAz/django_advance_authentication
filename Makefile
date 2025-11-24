.PHONY: help local localtest dev test prod migrate superuser logs clean build tag

# ====== Variables ======
TAG ?= latest

# ====== Help ======
help:
	@echo "Available commands:"
	@echo "  make local        - Run project locally (python runserver)"
	@echo "  make localtest    - Run local tests"
	@echo "  make dev          - Run project in Docker (development)"
	@echo "  make test         - Run tests inside dev Docker container"
	@echo "  make prod         - Run project in production"
	@echo "  make migrate      - Run migrations inside dev Docker"
	@echo "  make superuser    - Create superuser inside dev Docker"
	@echo "  make logs         - Show logs of all containers"
	@echo "  make clean        - Stop and remove containers & volumes"
	@echo "  make build        - Build Docker image"
	@echo "  make tag          - Create git tag (VERSION=1.0.0 make tag)"

# ====== Local ======
local:
	python3 src/manage.py runserver

localtest:
	DJANGO_ENV=test pytest  --cov-report=xml

# ====== Docker Development ======
dev:
	docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml up --build -d

test:
	docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
	docker compose -f docker-compose.test.yml down -v

migrate:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py migrate

superuser:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py createsuperuser

logs:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f

# ====== Docker Production ======
prod:
	TAG=$(TAG) docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# ====== Clean ======
clean:
	docker compose down -v --remove-orphans

# ====== Build Image ======
build:
	docker compose build

# ====== Git Tag ======
tag:
	git tag $(VERSION)
	git push origin $(VERSION)
