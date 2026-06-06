.PHONY: build up down logs test shell clean

build:
	docker-compose build

up:
	docker-compose up

up-d:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f api

test:
	docker-compose exec api pytest tests/ -v

test-unit:
	docker-compose exec api pytest tests/unit/ -v

test-integration:
	docker-compose exec api pytest tests/integration/ -v

shell:
	docker-compose exec api bash

clean:
	docker-compose down -v
	docker system prune -f

restart: down up-d

# Usage:
# make build  - Build the image
# make up     - Start with logs
# make up-d   - Start in background
# make test   - Run all tests
# make shell  - Get shell in container
# make down   - Stop container