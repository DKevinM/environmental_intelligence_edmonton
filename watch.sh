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

# Publish docs/watch_status.json when it changed. Uses the same git lock as
# run_and_publish.sh (not the watch-only lock above) so the two scripts
# never run git commands against this repo concurrently.
GITLOCK="/opt/airquality/locks/edmonton_folk_fest_git.lock"
(
  flock -w 30 200 || { echo "Could not get git lock within 30s; skipping status publish this cycle."; exit 0; }

  git add docs/watch_status.json
  if git diff --cached --quiet; then
      exit 0
  fi

  git commit -m "chore: live watch status $(date -u +%Y-%m-%dT%H:%M:%SZ)" -q
  for attempt in 1 2 3; do
      if git push origin main; then
          break
      fi
      git pull --rebase origin main
  done
) 200>"$GITLOCK"
