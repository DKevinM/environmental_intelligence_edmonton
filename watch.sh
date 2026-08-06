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

# Copy the real-time status (written every minute, outside the repo — see
# watch.py) into the git-tracked docs/watch_status.json as a durable
# GitHub-Pages-served fallback — but only every PUBLISH_INTERVAL_SECONDS at
# most, and the throttle is checked BEFORE touching the working tree at
# all, so between publishes the repo stays completely clean. Previously
# watch.py wrote directly into docs/, which left an uncommitted change
# sitting in the working tree most of the time (this step only committed
# every 5 min) and blocked run_and_publish.sh's own `git pull --rebase`
# whenever its 30-minute cycle landed mid-window — that's what stalled the
# main sit-rep for over an hour on 2026-08-06. Uses the same git lock as
# run_and_publish.sh (not the watch-only lock above) so the two scripts
# never run git commands against this repo concurrently.
LIVE_STATUS_FILE="/opt/airquality/live-status/edmonton_folk_fest_watch_status.json"
GITLOCK="/opt/airquality/locks/edmonton_folk_fest_git.lock"
PUBLISH_STAMP="/opt/airquality/locks/edmonton_folk_fest_watch_publish.stamp"
PUBLISH_INTERVAL_SECONDS=300
(
  flock -w 30 200 || { echo "Could not get git lock within 30s; skipping status publish this cycle."; exit 0; }

  now_epoch=$(date +%s)
  last_epoch=$(cat "$PUBLISH_STAMP" 2>/dev/null || echo 0)
  if [ $((now_epoch - last_epoch)) -lt "$PUBLISH_INTERVAL_SECONDS" ]; then
      exit 0
  fi

  [ -f "$LIVE_STATUS_FILE" ] || exit 0
  cp "$LIVE_STATUS_FILE" docs/watch_status.json
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
  echo "$now_epoch" > "$PUBLISH_STAMP"
) 200>"$GITLOCK"
