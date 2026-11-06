#!/usr/bin/env bash
# =============================================================================
# Help Chair — Publica el monorepo en GitHub y configura equipos y protecciones
# Publishes the monorepo to GitHub and configures teams and protections
#
# Uso / Usage (desde la raíz del repo / from the repo root):
#   ./scripts/setup-github.sh <ORG> [--public|--private] [--dry-run]
#
# Requisitos / Requirements: git y GitHub CLI (gh) autenticado con permisos de
# administrador de la organización (scopes: repo, admin:org).
# =============================================================================
set -euo pipefail

ORG="${1:?Uso: $0 <ORG> [--public|--private] [--dry-run]}"
VIS="${2:---public}"
DRY="${3:-}"
REPO="help-chair"
DESC="Help Chair — help desk multiempresa alineado a ITIL v4 (monorepo)"
cd "$(cd "$(dirname "$0")/.." && pwd)"

run() { if [[ "$DRY" == "--dry-run" ]]; then echo "[dry-run] $*"; else "$@"; fi; }

TEAMS=(
  "team-events|Gestión de Eventos"
  "team-access|Gestión de Accesos"
  "team-requests|Gestión de Peticiones"
  "team-incidents|Gestión de Incidencias"
  "team-problems|Gestión de Problemas y Base de Conocimiento"
  "team-frontend|Frontend"
  "team-platform|Plataforma (gateway, tenants, Kubernetes)"
)

echo "==> 1/6 Ajustando CODEOWNERS a la organización '$ORG'"
sed -i "s|@help-chair/|@$ORG/|g" .github/CODEOWNERS

echo "==> 2/6 Creando teams"
for t in "${TEAMS[@]}"; do
  IFS='|' read -r slug name <<<"$t"
  if [[ "$DRY" == "--dry-run" ]]; then echo "[dry-run] crear team $slug"; else
    gh api -X POST "orgs/$ORG/teams" -f name="$slug" -f description="$name" -f privacy=closed >/dev/null 2>&1 \
      && echo "   creado: $slug" || echo "   (ya existe o sin permisos: $slug)"
  fi
done

echo "==> 3/6 Creando el repositorio $ORG/$REPO y subiendo main"
if [[ "$DRY" == "--dry-run" ]]; then
  echo "[dry-run] git init -b main; git add -A; git commit; gh repo create $ORG/$REPO $VIS --push; crear rama develop"
else
  [[ -d .git ]] || git init -q -b main
  git add -A
  git diff --cached --quiet || git commit -q -m "chore(repo): initial monorepo structure"
  git branch -M main
  gh repo create "$ORG/$REPO" "$VIS" --description "$DESC" --source=. --remote=origin --push
  echo "==> 4/6 Creando rama develop y fijándola como predeterminada"
  git switch -q -c develop
  git push -q -u origin develop
  gh repo edit "$ORG/$REPO" --default-branch develop --delete-branch-on-merge --enable-issues \
    --enable-squash-merge --enable-merge-commit --enable-rebase-merge=false
  gh api -X PATCH "repos/$ORG/$REPO" -f squash_merge_commit_title=PR_TITLE \
    -f squash_merge_commit_message=PR_BODY >/dev/null
fi

protect() { # rama
  run gh api -X PUT "repos/$ORG/$REPO/branches/$1/protection" --input - <<JSON
{
  "required_status_checks": null,
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true
  },
  "restrictions": null,
  "required_conversation_resolution": true,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON
}

echo "==> 5/6 Protegiendo main y develop"
protect main    || echo "   ⚠ No se pudo proteger main (¿repo privado en plan gratuito?)"
protect develop || echo "   ⚠ No se pudo proteger develop"

echo "==> 6/6 Dando permisos de escritura a cada team"
for t in "${TEAMS[@]}"; do
  IFS='|' read -r slug _ <<<"$t"
  if [[ "$DRY" == "--dry-run" ]]; then echo "[dry-run] permiso push a $slug"; else
    gh api -X PUT "orgs/$ORG/teams/$slug/repos/$ORG/$REPO" -f permission=push >/dev/null || echo "   ⚠ permiso falló: $slug"
  fi
done

echo "✔ Listo / Done. Agrega integrantes a cada team: https://github.com/orgs/$ORG/teams"
