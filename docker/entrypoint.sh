#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="/app"
DEFAULT_WORKSPACE="/workspace"

mkdir -p /root/mla_v3

if [[ -n "${HOST_PWD:-}" && -d "/workspace${HOST_PWD}" ]]; then
  export WORKSPACE_ROOT="${WORKSPACE_ROOT:-/workspace${HOST_PWD}}"
elif [[ -d "${DEFAULT_WORKSPACE}" ]]; then
  export WORKSPACE_ROOT="${WORKSPACE_ROOT:-${DEFAULT_WORKSPACE}}"
else
  mkdir -p "${DEFAULT_WORKSPACE}"
  export WORKSPACE_ROOT="${WORKSPACE_ROOT:-${DEFAULT_WORKSPACE}}"
fi

export MLA_USER_DATA_ROOT="${MLA_USER_DATA_ROOT:-/root/mla_v3}"
export WEB_UI_USERS_FILE="${WEB_UI_USERS_FILE:-/root/mla_v3/web_ui_users.yaml}"
export WEB_UI_USER_DATA_ROOT="${WEB_UI_USER_DATA_ROOT:-/root/mla_v3/web_users}"
export PORT="${PORT:-4242}"

cd "${APP_ROOT}"

mode="${1:-webui}"
shift || true

case "${mode}" in
  webui)
    echo "[docker] starting webui on 0.0.0.0:${PORT}"
    echo "[docker] workspace root: ${WORKSPACE_ROOT}"
    exec python web_ui/server/server.py "$@"
    ;;
  cli)
    echo "[docker] starting cli in workspace: ${WORKSPACE_ROOT}"
    cd "${WORKSPACE_ROOT}"
    exec python /app/start.py --cli "$@"
    ;;
  bash|sh)
    exec "${mode}" "$@"
    ;;
  *)
    exec "${mode}" "$@"
    ;;
esac
