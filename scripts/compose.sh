#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
variant=${1:?Usage: scripts/compose.sh VARIANT compose-arguments...}
shift
case "$variant" in 1|2|3|4) ;; *) echo 'Variant must be 1, 2, 3 or 4' >&2; exit 2;; esac
test -f "$ROOT/.env" || { echo 'Run python3 scripts/init_env.py on the server first' >&2; exit 2; }
# Keep interpolation and env_file consistent, even if the invoking shell exported it.
unset REDIS_PASSWORD APP_PORT APP_DOMAIN
exec docker compose --project-directory "$ROOT" --env-file "$ROOT/.env" \
  --env-file "$ROOT/variants/$variant.env" -f "$ROOT/docker-compose.yml" "$@"
