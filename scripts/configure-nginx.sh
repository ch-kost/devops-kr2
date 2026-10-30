#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
variant=${1:?Usage: scripts/configure-nginx.sh VARIANT [--apply]}
case "$variant" in 1|2|3|4) ;; *) echo 'Invalid variant' >&2; exit 2;; esac
source "$ROOT/variants/$variant.env"
if [[ ${2:-} != --apply ]]; then
  sed -e "s/__DOMAIN__/$APP_DOMAIN/g" -e "s/__PORT__/$APP_PORT/g" "$ROOT/nginx/kr2.conf.template"
  echo '# Preview only; pass --apply on the devops VM to install.'
  exit 0
fi
if [[ -e /etc/nginx/sites-available/kr2 || -e /etc/ssl/private/kr2.key || -e /etc/ssl/certs/kr2.crt ]]; then
  echo 'Existing KR2 configuration/certificate found; inspect and back it up explicitly before replacing.' >&2
  exit 2
fi
tmp=$(mktemp)
trap 'rm -f -- "$tmp"' EXIT
sed -e "s/__DOMAIN__/$APP_DOMAIN/g" -e "s/__PORT__/$APP_PORT/g" "$ROOT/nginx/kr2.conf.template" > "$tmp"
sudo openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
  -keyout /etc/ssl/private/kr2.key -out /etc/ssl/certs/kr2.crt \
  -subj "/CN=$APP_DOMAIN" -addext "subjectAltName=DNS:$APP_DOMAIN"
sudo chown root:root /etc/ssl/private/kr2.key
sudo chmod 600 /etc/ssl/private/kr2.key
sudo install -m 644 "$tmp" /etc/nginx/sites-available/kr2
sudo ln -s /etc/nginx/sites-available/kr2 /etc/nginx/sites-enabled/kr2
if ! sudo nginx -t; then
  sudo unlink /etc/nginx/sites-enabled/kr2
  echo 'Validation failed; new site deactivated; existing resources were not reloaded.' >&2
  exit 1
fi
sudo systemctl reload nginx
