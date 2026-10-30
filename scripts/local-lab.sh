#!/usr/bin/env bash
set -euo pipefail
cd /work
variant=${KR2_VARIANT:-1}
export COMPOSE_PROJECT_NAME=kr2-chugunov-local
unset REDIS_PASSWORD APP_PORT APP_DOMAIN
compose=(docker compose -p kr2-chugunov-local --project-directory /work --env-file /work/.env --env-file "/work/variants/$variant.env" -f /work/docker-compose.yml -f /work/docker-compose.local-test.yml)
case "${1:-start}" in
  audit-negative)
    restore() { "${compose[@]}" up -d --wait app; }
    trap restore EXIT
    "${compose[@]}" -f /work/docker-compose.audit-negative.yml up -d --wait app
    set +e
    KR2_CERT_PATH=/certs/kr2.crt KR2_SITE_LINK=/certs/kr2-enabled KR2_SITE_CONFIG=/certs/nginx.conf bash scripts/audit-kr2.sh "$variant"
    rc=$?
    set -e
    echo "Actual local audit with wrong loopback IP 127.0.0.2 exit=$rc (expected 1)"
    [[ $rc == 1 ]] || exit 1
    restore
    trap - EXIT
    KR2_CERT_PATH=/certs/kr2.crt KR2_SITE_LINK=/certs/kr2-enabled KR2_SITE_CONFIG=/certs/nginx.conf bash scripts/audit-kr2.sh "$variant"
    echo 'Actual local audit after restoring 127.0.0.1 exit=0'
    ;;
  audit)
    KR2_CERT_PATH=/certs/kr2.crt KR2_SITE_LINK=/certs/kr2-enabled KR2_SITE_CONFIG=/certs/nginx.conf bash scripts/audit-kr2.sh "$variant"
    ;;
  secret-check)
    python3 scripts/check-secrets.py --delivered-only
    stat -c 'Linux .env mode=%a uid=%u' .env
    ;;
  audit-selftest)
    python3 scripts/audit-selftest.py
    ;;
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
