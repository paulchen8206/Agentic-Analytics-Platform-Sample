SHELL := /bin/bash

.DEFAULT_GOAL := help

DOCKER_COMPOSE ?= docker compose

.PHONY: help start stop restart logs ps build pull test clean prune docker-up docker-down docker-logs docker-ps docker-build

help: ## Show available procedures
	@echo "Agentic Analytics Platform procedures"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-16s %s\n", $$1, $$2}'

start: ## Start full stack in Docker (detached)
	$(DOCKER_COMPOSE) up --build -d

stop: ## Stop Docker stack
	$(DOCKER_COMPOSE) down

restart: stop start ## Restart Docker stack

logs: ## Tail Docker logs
	$(DOCKER_COMPOSE) logs -f --tail=200

ps: ## Show Docker service status
	$(DOCKER_COMPOSE) ps

build: ## Build all Docker images
	$(DOCKER_COMPOSE) build

pull: ## Pull latest upstream images
	$(DOCKER_COMPOSE) pull

test: ## Run tests in Docker test container
	$(DOCKER_COMPOSE) run --rm tests

clean: ## Stop stack and remove volumes/orphans
	$(DOCKER_COMPOSE) down --volumes --remove-orphans

prune: clean ## Cleanup dangling Docker images
	docker image prune -f

docker-up: start ## Alias for start

docker-down: stop ## Alias for stop

docker-logs: logs ## Alias for logs

docker-ps: ps ## Alias for ps

docker-build: build ## Alias for build
