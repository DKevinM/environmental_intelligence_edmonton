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

# Publish docs/watch_status.json to the git-backed (GitHub Pages) copy —
# but only every PUBLISH_INTERVAL_SECONDS at most, regardless of how often
# it changed. watch.py now writes it fresh every run for real-time serving
# via the Cloudflare Tunnel (status.krmenvironmental.com), which involves
# no git/Pages build at all; this git copy is just a slower-but-durable
# backup, so there's no reason to push it at the same cadence, and pushing
# it that often is exactly what caused the earlier Pages build failures.
# Uses the same git lock as run_and_publish.sh (not the watch-only lock
# above) so the two scripts never run git commands against this repo
# concurrently.
GITLOCK="/opt/airquality/locks/edmonton_folk_fest_git.lock"
PUBLISH_STAMP="/opt/airquality/locks/edmonton_folk_fest_watch_publish.stamp"
PUBLISH_INTERVAL_SECONDS=300
(
  flock -w 30 200 || { echo "Could not get git lock within 30s; skipping status publish this cycle."; exit 0; }

  git add docs/watch_status.json
  if git diff --cached --quiet; then
      exit 0
  fi

  now_epoch=$(date +%s)
  last_epoch=$(cat "$PUBLISH_STAMP" 2>/dev/null || echo 0)
  if [ $((now_epoch - last_epoch)) -lt "$PUBLISH_INTERVAL_SECONDS" ]; then
      exit 0
  fi

  git commit -m "chore: live watch status $(date -u +%Y-%m-%dT%H:%M:%SZ)" -q
  for attempt in 1 2 3; do
      if git push origin main; then
          break
      fi
      git pull --rebase origin main
  done
  echo "$now_epoch" > "$PUBLISH_STAMP"
) 200>"$GITLOCK"
