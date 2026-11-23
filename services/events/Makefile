# Servicio: events
# Funciona con uv (recomendado) o, si no está instalado, con venv + pip automáticamente.
SERVICE   := events
PORT      ?= 8001
IMAGE     ?= ghcr.io/help-chair/hc-$(SERVICE)
TAG       ?= dev
CONTAINER ?= podman

ifeq ($(OS),Windows_NT)
  MODE      := venv+pip
  PYTHON    := .venv/Scripts/python.exe
  SETUP     := py -3.12 -m venv .venv && .venv/Scripts/python.exe -m pip install -q -r requirements-dev.txt
else
  ifneq ($(shell command -v uv 2>/dev/null),)
    MODE      := uv
		RUN				:= uv run
    PYTHON    := uv run python
    SETUP     := uv sync
  else
    MODE      := venv+pip
    PYTHON    := .venv/bin/python
    SETUP     := python3 -m venv .venv && .venv/bin/python -m pip install -q -r requirements-dev.txt
  endif
endif

.DEFAULT_GOAL := help
.PHONY: help setup run migrate makemigrations test lint format build seed openapi contracts-check lock clean

help: ## Muestra esta ayuda
	@echo "Servicio $(SERVICE) · modo: $(MODE)"
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-15s %s\n", $$1, $$2}'

setup: ## Instala dependencias y crea .env si no existe
ifeq ($(OS),Windows_NT)
	@if not exist .env copy .env.example .env
else
	@test -f .env || cp .env.example .env
endif
	$(SETUP)

run: ## Arranca el servidor de desarrollo
	$(PYTHON) manage.py migrate --noinput
	$(PYTHON) manage.py runserver 0.0.0.0:$(PORT)

migrate: ## Aplica migraciones
	$(PYTHON) manage.py migrate --noinput

makemigrations: ## Genera migraciones
	$(PYTHON) manage.py makemigrations

test: ## Ejecuta pruebas con cobertura
	$(PYTHON) -m pytest

lint: ## ruff: estilo y formato (sin modificar)
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .

format: ## ruff: corrige estilo y formatea
	$(PYTHON) -m ruff check --fix .
	$(PYTHON) -m ruff format .

build: ## Construye con Podman (usa CONTAINER=docker para Docker)
	$(CONTAINER) build -t $(IMAGE):$(TAG) .

seed: ## Siembra la matriz de prioridad y los modificadores por defecto
	$(PYTHON) manage.py migrate --noinput
	$(PYTHON) manage.py seed_priority

openapi: ## Exporta el contrato a contracts/$(SERVICE)/openapi.yaml
	@mkdir -p ../../contracts/$(SERVICE)
	$(PYTHON) manage.py spectacular --file ../../contracts/$(SERVICE)/openapi.yaml --validate

contracts-check:
	$(RUN) openapi-spec-validator ../../contracts/events/openapi.yaml

lock: ## (requiere uv) Actualiza uv.lock y regenera requirements*.txt
	uv lock -q
	uv export -q --no-dev --no-hashes --no-emit-project -o requirements.txt
	uv export -q --no-hashes --no-emit-project -o requirements-dev.txt

clean: ## Borra entorno virtual y cachés
	rm -rf .venv .pytest_cache .ruff_cache .coverage staticfiles
