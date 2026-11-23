# Servicio: access
# Funciona con uv (recomendado) o, si no está instalado, con venv + pip automáticamente.
SERVICE   := access
PORT      ?= 8002
IMAGE     ?= ghcr.io/help-chair/hc-$(SERVICE)
TAG       ?= dev
CONTAINER ?= $(shell command -v podman >/dev/null 2>&1 && echo podman || echo docker)

ifneq ($(shell command -v uv 2>/dev/null),)
  MODE  := uv
  RUN   := uv run
  SETUP := uv sync
else
  MODE  := venv+pip
  RUN   :=
  SETUP := python3 -m venv .venv && .venv/bin/pip install -q -r requirements-dev.txt
  export PATH := $(CURDIR)/.venv/bin:$(PATH)
endif

.DEFAULT_GOAL := help
.PHONY: help setup run migrate makemigrations test lint format build seed openapi lock clean

help: ## Muestra esta ayuda
	@echo "Servicio $(SERVICE) · modo: $(MODE)"
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-15s %s\n", $$1, $$2}'

setup: ## Instala dependencias y crea .env si no existe
	@test -f .env || cp .env.example .env
	$(SETUP)

run: ## Arranca el servidor de desarrollo
	$(RUN) python manage.py migrate --noinput
	$(RUN) python manage.py runserver 0.0.0.0:$(PORT)

migrate: ## Aplica migraciones
	$(RUN) python manage.py migrate --noinput

makemigrations: ## Genera migraciones
	$(RUN) python manage.py makemigrations

test: ## Ejecuta pruebas con cobertura
	$(RUN) pytest

lint: ## ruff: estilo y formato (sin modificar)
	$(RUN) ruff check .
	$(RUN) ruff format --check .

format: ## ruff: corrige estilo y formatea
	$(RUN) ruff check --fix .
	$(RUN) ruff format .

build: ## Construye la imagen OCI (Podman o Docker)
	$(CONTAINER) build -t $(IMAGE):$(TAG) .

seed: ## Carga el catálogo de roles (idempotente)
	$(RUN) python manage.py seed

openapi: ## Genera el esquema a build/ y lo compara con el contrato (nunca lo sobreescribe)
	@mkdir -p build
	$(RUN) python manage.py spectacular --file build/openapi.generado.yaml --validate
	@echo
	$(RUN) python tools/reconcilia_contrato.py \
		build/openapi.generado.yaml ../../contracts/$(SERVICE)/openapi.yaml

lock: ## (requiere uv) Actualiza uv.lock y regenera requirements*.txt
	uv lock -q
	uv export -q --no-dev --no-hashes --no-emit-project -o requirements.txt
	uv export -q --no-hashes --no-emit-project -o requirements-dev.txt

clean: ## Borra entorno virtual y cachés
	rm -rf .venv .pytest_cache .ruff_cache .coverage staticfiles
