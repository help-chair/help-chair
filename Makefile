# Atajos del monorepo. Cada servicio tiene su propio Makefile (cd services/<x> && make help).
PROJECT      := help-chair
COMPOSE_FILE := platform/deploy/local/compose.yaml
COMPOSE      ?= $(shell command -v podman >/dev/null 2>&1 && echo "podman compose" || echo "docker compose")
DC           = $(COMPOSE) -p $(PROJECT) -f $(COMPOSE_FILE)
SERVICES     := events access requests incidents problems knowledge
KUBE_DIR     := platform/deploy/local/kube
CLUSTER_DIR  := platform/deploy/cluster/scripts

# Oculta el aviso "Executing external compose provider" de podman compose
export PODMAN_COMPOSE_WARNING_LOGS ?= false

.PHONY: help up down logs ps build reset health setup-all test-all lint-all hooks \
        kube-build kube-up kube-down kube-reset helm-check testing-up testing-down

help: ## Muestra esta ayuda
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-12s %s\n", $$1, $$2}'

##@ Entorno local (platform/deploy/local/README.md)
up: ## Levanta todo el entorno local (construye las imágenes)
	$(DC) up --build -d

down: ## Detiene el entorno local (conserva los datos de las BD)
	$(DC) down

logs: ## Sigue los logs (make logs S=events)
	$(DC) logs -f $(S)

ps: ## Estado de los contenedores
	$(DC) ps

build: ## Reconstruye las imágenes sin levantar nada
	$(DC) build

reset: ## BORRA contenedores y datos de las BD y levanta de nuevo (pide confirmación; YES=1 la omite)
	@if [ "$(YES)" != "1" ]; then \
	  printf 'Esto borra TODOS los datos locales (volúmenes de las BD). Escribe "si" para continuar: '; \
	  read ans; [ "$$ans" = "si" ] || { echo "Cancelado."; exit 1; }; \
	fi
	$(DC) down -v --remove-orphans
	$(DC) up --build -d

health: ## Consulta /health/ready de cada servicio (requiere make up)
	@for p in 8001:events 8002:access 8003:requests 8004:incidents 8005:problems 8006:knowledge; do \
	  port=$${p%%:*}; name=$${p##*:}; \
	  code=$$(curl -s -o /dev/null -w '%{http_code}' -m 3 http://127.0.0.1:$$port/health/ready || true); \
	  printf '%-10s %s\n' $$name $$code; \
	done

setup-all: ## Instala dependencias de todos los servicios
	@for s in $(SERVICES); do $(MAKE) -C services/$$s setup || exit 1; done

test-all: ## Pruebas de todos los servicios
	@for s in $(SERVICES); do echo "== $$s"; $(MAKE) -C services/$$s test || exit 1; done

lint-all: ## Lint de todos los servicios
	@for s in $(SERVICES); do echo "== $$s"; $(MAKE) -C services/$$s lint || exit 1; done

hooks: ## Instala pre-commit (ruff, secretos, formato)
	pre-commit install

##@ Plan B sin compose: podman kube play (platform/deploy/local/README.md)
kube-build: ## Construye las imágenes locales que usan los manifiestos
	@for s in $(SERVICES); do $(MAKE) -C services/$$s build || exit 1; done
	$(MAKE) -C frontend image

kube-up: ## Levanta los pods con podman kube play (requiere make kube-build)
	@for f in $(KUBE_DIR)/*.yaml; do echo "== $$f"; podman kube play --replace $$f || exit 1; done

kube-down: ## Detiene los pods del plan B (conserva los datos)
	@for f in $(KUBE_DIR)/*.yaml; do podman kube down $$f || true; done

kube-reset: ## Plan B: detiene los pods Y borra sus datos (--force)
	@printf 'Esto borra los datos de los pods. Escribe "si" para continuar: '; read ans; [ "$$ans" = "si" ] || { echo "Cancelado."; exit 1; }
	@for f in $(KUBE_DIR)/*.yaml; do podman kube down --force $$f || true; done

##@ Helm y clúster de testing (platform/deploy/helm, platform/deploy/cluster)
helm-check: ## helm lint + helm template de cada ambiente (y kubeconform si está instalado)
	./platform/deploy/helm/check.sh

testing-down: ## Apaga la VM de testing para no gastar crédito (GCP)
	$(CLUSTER_DIR)/50-cluster-down.sh

testing-up: ## Enciende la VM de testing y espera a que el nodo esté Ready
	$(CLUSTER_DIR)/51-cluster-up.sh
