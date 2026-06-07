COMPOSE = docker compose -p agile-backlog-api

.PHONY: build up down logs test shell clean restart

build:
	$(COMPOSE) build

up:
	$(COMPOSE) up

up-d:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f api

test:
	$(COMPOSE) exec api pytest tests/ -v

test-unit:
	$(COMPOSE) exec api pytest tests/unit/ -v

test-integration:
	$(COMPOSE) exec api pytest tests/integration/ -v

shell:
	$(COMPOSE) exec api bash

clean:
	$(COMPOSE) down -v
	docker system prune -f

restart: down up-d

# Common commands:
# make up     Start with logs
# make up-d   Start in background
# make down   Stop containers
# make logs   Show API logs
# make test   Run tests
# make shell  Open container shell
