#!/usr/bin/env bash
# Standalone section [6]; source this body into the pre-existing audit if desired.
set -uo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
variant=${1:?Usage: scripts/audit-kr2.sh VARIANT}
case "$variant" in 1|2|3|4) ;; *) exit 2;; esac
source "$ROOT/variants/$variant.env"
status=0
check() { local name=$1; shift; if "$@"; then printf '[OK] %s\n' "$name"; else printf '[FAIL] %s\n' "$name"; status=1; fi; }
redis_healthy() {
  local id
  id=$("$ROOT/scripts/compose.sh" "$variant" ps -q redis) || return 1
  [[ -n "$id" ]] && [[ $(docker inspect -f '{{.State.Health.Status}}' "$id") == healthy ]]
}
port_loopback() {
  [[ $("$ROOT/scripts/compose.sh" "$variant" port app "$APP_PORT") == "127.0.0.1:$APP_PORT" ]]
}
env_private() { [[ $(stat -c '%a' "$ROOT/.env") == 600 ]]; }
cert_lifetime() { openssl x509 -checkend 2592000 -noout -in /etc/ssl/certs/kr2.crt; }
site_enabled() {
  [[ -L /etc/nginx/sites-enabled/kr2 ]] && [[ $(readlink -f /etc/nginx/sites-enabled/kr2) == /etc/nginx/sites-available/kr2 ]]
}
printf '[6] Контрольная работа № 2\n'
check 'Redis healthy' redis_healthy
check 'Application published only on loopback' port_loopback
check 'Server .env permissions are 600' env_private
check 'KR2 certificate valid for at least 30 more days' cert_lifetime
check 'Separate KR2 nginx site enabled' site_enabled
exit "$status"
