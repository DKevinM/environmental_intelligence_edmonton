import json
from pathlib import Path

# Hazards whose 'indicator' isn't a plain "bigger delta = worse" numeric
# reading — aqhi_rate_of_change is already itself a rate (diffing it again
# is not meaningful), thunderstorm's indicator is a formatted time string.
TREND_EXCLUDED_HAZARDS = {'aqhi_rate_of_change', 'thunderstorm'}


def load_previous(path):
    """Reads the dashboard_data.json written by the *last* run, before this
    run overwrites it. Returns None on first run or any read failure —
    trends are best-effort, never worth failing the report over."""
    p = Path(path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return None


def compute_hazard_trends(current_hazards, previous_data):
    """Diffs each hazard's numeric indicator against the previous run.
    Returns {hazard_key: delta}; a hazard is omitted if it's excluded,
    either indicator is missing, or either indicator isn't numeric."""
    trends = {}
    if not previous_data:
        return trends
    previous_hazards = ((previous_data.get('assessment') or {}).get('hazards')) or {}
    for key, cur in current_hazards.items():
        if key in TREND_EXCLUDED_HAZARDS:
            continue
        prev = previous_hazards.get(key)
        if not prev:
            continue
        cv, pv = cur.get('indicator'), prev.get('indicator')
        if cv is None or pv is None:
            continue
        try:
            trends[key] = round(float(cv) - float(pv), 1)
        except (TypeError, ValueError):
            continue
    return trends
