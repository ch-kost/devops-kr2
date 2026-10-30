#!/usr/bin/env bash
set -euo pipefail
cd /work
variant=${KR2_VARIANT:-1}
unset REDIS_PASSWORD APP_PORT APP_DOMAIN
compose=(docker compose -p kr2-chugunov-local --project-directory /work --env-file /work/.env --env-file "/work/variants/$variant.env" -f /work/docker-compose.yml -f /work/docker-compose.local-test.yml)
case "${1:-start}" in
  start|sync)
    tar -C /src --exclude=.git --exclude=.env --exclude=.venv --exclude=evidence --exclude=.runtime -cf - . | tar -xf -
    python3 scripts/prepare_local.py "$variant"
    if [[ ${1:-start} == start ]]; then
      "${compose[@]}" up -d --build --wait --wait-timeout 120
    fi
    ;;
  *)
    "${compose[@]}" "$@"
    ;;
esac
