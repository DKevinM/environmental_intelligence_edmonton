#!/bin/bash
set -e
cd /opt/airquality/github/edmonton_folk_fest
source .venv/bin/activate

LOCKFILE="/opt/airquality/locks/edmonton_folk_fest_watch.lock"
mkdir -p "$(dirname "$LOCKFILE")"
(
  flock -n 200 || exit 0  # previous run still going (shouldn't happen, runs take <1s) — skip rather than pile up
  python3 watch.py
) 200>"$LOCKFILE"
