# Atajos del monorepo. Cada servicio tiene su propio Makefile (cd services/<x> && make help).
COMPOSE ?= $(shell command -v podman >/dev/null 2>&1 && echo "podman compose" || echo "docker compose")
COMPOSE_FILE := platform/deploy/local/compose.yaml
SERVICES := events access requests incidents problems knowledge

.PHONY: help up down logs ps setup-all test-all lint-all hooks
help: ## Muestra esta ayuda
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-10s %s\n", $$1, $$2}'

up: ## Levanta todo el entorno local (construye imágenes)
	$(COMPOSE) -f $(COMPOSE_FILE) up --build -d

down: ## Detiene el entorno local
	$(COMPOSE) -f $(COMPOSE_FILE) down

logs: ## Sigue los logs (make logs S=events)
	$(COMPOSE) -f $(COMPOSE_FILE) logs -f $(S)

ps: ## Estado de los contenedores
	$(COMPOSE) -f $(COMPOSE_FILE) ps

setup-all: ## Instala dependencias de todos los servicios
	@for s in $(SERVICES); do $(MAKE) -C services/$$s setup || exit 1; done

test-all: ## Pruebas de todos los servicios
	@for s in $(SERVICES); do echo "== $$s"; $(MAKE) -C services/$$s test || exit 1; done

lint-all: ## Lint de todos los servicios
	@for s in $(SERVICES); do echo "== $$s"; $(MAKE) -C services/$$s lint || exit 1; done

hooks: ## Instala pre-commit (ruff, secretos, formato)
	pre-commit install
