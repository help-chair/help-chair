# Frontend (React + Vite + TypeScript)
IMAGE     ?= ghcr.io/help-chair/hc-frontend
TAG       ?= dev
CONTAINER ?= $(shell command -v podman >/dev/null 2>&1 && echo podman || echo docker)

.DEFAULT_GOAL := help
.PHONY: help setup run test lint format build image seed clean

help: ## Muestra esta ayuda
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-10s %s\n", $$1, $$2}'

setup: ## Instala dependencias (npm ci) y crea .env si no existe
	@test -f .env || cp .env.example .env
	npm ci

run: ## Servidor de desarrollo en http://localhost:5173
	npm run dev

test: ## Pruebas (Vitest)
	npm test

lint: ## ESLint + Prettier + TypeScript (sin modificar)
	npm run lint
	npm run format:check
	npm run typecheck

format: ## Formatea con Prettier
	npm run format

build: ## Build de producción en dist/
	npm run build

image: ## Construye la imagen OCI (Podman o Docker)
	$(CONTAINER) build -t $(IMAGE):$(TAG) .

seed: ## No aplica al frontend (los datos viven en los servicios)
	@echo "El frontend no tiene datos propios; usa 'make seed' en los servicios."

clean: ## Borra node_modules y dist
	rm -rf node_modules dist coverage
