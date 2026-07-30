#!/bin/bash
set -e

cd /opt/airquality/github/edmonton_folk_fest
source .venv/bin/activate
set -a
source /opt/airquality/config/intelligence.env
set +a

LOCKFILE="/opt/airquality/locks/edmonton_folk_fest_git.lock"
mkdir -p "$(dirname "$LOCKFILE")"

(
  flock -w 120 200
  git fetch origin
  git pull --rebase origin main
) 200>"$LOCKFILE"

python run_demo.py

cp output/dashboard.html docs/index.html
cp output/sitrep.pdf docs/sitrep.pdf

(
  flock -w 120 200

  git add docs/index.html docs/sitrep.pdf

  if git diff --cached --quiet; then
      echo "No changes to commit."
      exit 0
  fi

  git commit -m "chore: refresh sit-rep $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  for attempt in 1 2 3; do
      if git push origin main; then
          break
      fi
      echo "push rejected (attempt $attempt/3); rebasing onto latest and retrying..."
      git pull --rebase origin main
  done
) 200>"$LOCKFILE"
