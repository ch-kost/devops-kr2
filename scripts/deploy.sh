#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
target=${1:-devops}
case "$target" in *[!a-zA-Z0-9_.@-]*|'') echo 'Use an SSH host alias or user@host' >&2; exit 2;; esac
# Destination is fixed to the assignment directory, never a broad home/root path.
opts=(-avz --delete --exclude=.env --exclude=.git --exclude=.venv --exclude=evidence --exclude=.runtime)
rsync "${opts[@]}" --dry-run "$ROOT/" "$target:kr2/"
if [[ ${2:-} != --apply ]]; then
  echo 'Dry run only. Inspect changes; rerun with --apply to deliver.'
  exit 0
fi
rsync "${opts[@]}" "$ROOT/" "$target:kr2/"
