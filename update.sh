#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${PROJECT_DIR}"

if docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD=(docker-compose)
else
  echo "Error: docker compose/docker-compose not found."
  exit 1
fi

SERVICE="${UPDATE_SERVICE:-rustdesk-api-server}"
UPDATE_ALL_SERVICES="${UPDATE_ALL_SERVICES:-false}"

echo "Using compose command: ${COMPOSE_CMD[*]}"

if [ "${UPDATE_ALL_SERVICES}" = "true" ]; then
  echo "Updating all services..."
  "${COMPOSE_CMD[@]}" pull
  "${COMPOSE_CMD[@]}" up -d
else
  echo "Updating service: ${SERVICE}"
  # --no-deps avoids touching hbbs/hbbr during API-only rollout.
  "${COMPOSE_CMD[@]}" pull "${SERVICE}"
  "${COMPOSE_CMD[@]}" up -d --no-deps "${SERVICE}"
fi

echo "Current stack status:"
"${COMPOSE_CMD[@]}" ps
