# Servicio: problems
# Funciona con uv (recomendado) o, si no está instalado, con venv + pip automáticamente.
SERVICE   := problems
PORT      ?= 8005
IMAGE     ?= ghcr.io/help-chair/hc-$(SERVICE)
TAG       ?= dev
export OPENAPI_OUTPUT
CONTAINER ?= $(shell command -v podman >/dev/null 2>&1 && echo podman || echo docker)

ifneq ($(shell command -v uv 2>/dev/null),)
  MODE  := uv
  RUN   := uv run --frozen
  SETUP := uv sync --frozen
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

setup: ## Instala dependencias; la configuración procede del entorno del proceso
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

seed: ## Datos sintéticos idempotentes; requiere CONFIRM_DEMO=1
	@test "$(CONFIRM_DEMO)" = "1" || { echo "Seed desactivado: requiere CONFIRM_DEMO=1 y BD de ensayo."; exit 2; }
	$(RUN) python manage.py seed_demo --confirm-demo

openapi: ## Exporta solo el esquema runtime; requiere OPENAPI_OUTPUT fuera de contracts/
	$(RUN) python scripts/export_schema.py

lock: ## (requiere uv) Actualiza uv.lock y regenera requirements*.txt
	uv lock -q
	uv export -q --no-dev --no-hashes --no-emit-project -o requirements.txt
	uv export -q --no-hashes --no-emit-project -o requirements-dev.txt

clean: ## Borra entorno virtual y cachés
	rm -rf .venv .pytest_cache .ruff_cache .coverage staticfiles
