"""Runs every minute via cron (see crontab) — deliberately separate from
run_demo.py, which is too slow (weasyprint, Playwright, wind trajectory
modeling) for that cadence. Only checks the handful of signals that can
change meaningfully minute-to-minute: lightning proximity, radar echo,
and Environment Canada severe weather alerts. Alerts only on NEW or
escalating conditions, not on steady-state, to avoid spamming the log.
"""
import json
import traceback
from datetime import datetime, timezone
from pathlib import Path

from core.config import load_config, ROOT
from modules.alerts.service import load_weather_alerts
from modules.intelligence.fast_watch import check_lightning, check_radar_echo

ALERT_LOG = Path('/opt/airquality/logs/sitrep_alerts.log')
STATUS_FILE = Path('/opt/airquality/logs/folk_fest_watch_status.txt')
STATE_FILE = ROOT / 'output' / 'watch_state.json'
# Deliberately NOT inside docs/ (the git-tracked, GitHub-Pages-served
# folder) — this gets written every single minute, and a file that changes
# that often inside the repo left an uncommitted change sitting in the
# working tree most of the time (watch.sh only commits it every 5 min),
# which then blocked run_and_publish.sh's own `git pull --rebase` whenever
# its 30-minute cycle landed mid-window. Writing here instead means git
# never sees these per-minute writes at all. Served in real time by nginx
# directly (see /etc/nginx/sites-available/dashboard-mirror.conf) via the
# Cloudflare Tunnel; watch.sh separately copies this into docs/ on its own
# throttled schedule for the git-backed/GitHub-Pages fallback copy.
PUBLIC_STATUS_FILE = Path('/opt/airquality/live-status/edmonton_folk_fest_watch_status.json')

LIGHTNING_SHELTER_KM = 10  # the "30-30 rule" shelter threshold
LIGHTNING_WATCH_KM = 25
SEVERITY = {'CLEAR': 0, 'DETECTED_FAR': 1, 'WATCH': 2, 'SHELTER': 3}


def lightning_band(km):
    if km is None:
        return 'CLEAR'
    if km <= LIGHTNING_SHELTER_KM:
        return 'SHELTER'
    if km <= LIGHTNING_WATCH_KM:
        return 'WATCH'
    return 'DETECTED_FAR'


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {'lightning_band': 'CLEAR', 'alert_names': []}


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state))


def radar_bucket(km, prev_bucket=None):
    """<10km/>=10km/none, with hysteresis: a reading has to clearly cross
    (8km one way, 12km the other) to flip, not just brush the 10km line —
    otherwise noise right at the boundary flips the bucket back and forth,
    and each flip counts as a 'real' change worth publishing."""
    if km is None:
        return 'none'
    if prev_bucket == 'near' and km < 12:
        return 'near'
    if prev_bucket == 'far' and km >= 8:
        return 'far'
    return 'near' if km < 10 else 'far'


def load_published():
    if PUBLIC_STATUS_FILE.exists():
        try:
            return json.loads(PUBLIC_STATUS_FILE.read_text())
        except Exception:
            pass
    return None


def log_alert(msg):
    now = datetime.now(timezone.utc).isoformat(timespec='seconds')
    with ALERT_LOG.open('a') as f:
        f.write(f'{now} ALERT edmonton_folk_fest: {msg}\n')


def main():
    cfg = load_config()
    prev = load_state()
    alerts_fired = []

    lightning = check_lightning(cfg)
    radar = check_radar_echo(cfg)
    wx = load_weather_alerts(cfg)

    new_band = lightning_band(lightning.get('nearest_km')) if lightning.get('status') == 'ok' else prev.get('lightning_band', 'CLEAR')
    old_band = prev.get('lightning_band', 'CLEAR')
    if SEVERITY[new_band] > SEVERITY[old_band]:
        alerts_fired.append(f"lightning now {new_band} ({lightning.get('nearest_km')} km from venue, was {old_band})")
    elif SEVERITY[new_band] < SEVERITY[old_band] and SEVERITY[old_band] >= SEVERITY['WATCH']:
        alerts_fired.append(f"lightning downgraded to {new_band} (was {old_band}) — stand-down")

    current_alert_names = sorted(set(a.get('name', '') for a in (wx.get('alerts') or []))) if wx.get('status') == 'ok' else prev.get('alert_names', [])
    prev_alert_names = set(prev.get('alert_names', []))
    for name in current_alert_names:
        if name not in prev_alert_names:
            alerts_fired.append(f"new Environment Canada alert: {name}")
    for name in prev_alert_names:
        if name not in current_alert_names:
            alerts_fired.append(f"Environment Canada alert cleared: {name}")

    for msg in alerts_fired:
        log_alert(msg)

    now = datetime.now(timezone.utc).isoformat(timespec='seconds')
    radar_note = f"{radar.get('nearest_km')} km" if radar.get('status') == 'ok' and radar.get('nearest_km') is not None else 'none within 40km'
    STATUS_FILE.write_text(
        f'Checked {now}\n'
        f'Lightning: {new_band} ({lightning.get("nearest_km")} km from venue)\n'
        f'Radar echo: {radar_note}\n'
        f'Active EC alerts: {", ".join(current_alert_names) or "none"}\n'
    )

    # Always write fresh — this file is served in real time via the
    # Kamatera Cloudflare Tunnel (status.krmenvironmental.com/folk-fest/),
    # which involves no git commit and no GitHub Pages build at all, so
    # there's no reason to throttle the write itself. GitHub Pages
    # protection (see watch.sh) is a separate, coarser gate applied only to
    # when this same file gets committed/pushed to the git-backed copy —
    # that's what caused the earlier Pages build failures, not this write.
    prev_published = load_published()
    prev_radar_bucket = (prev_published or {}).get('radar', {}).get('bucket')
    new_radar_bucket = radar_bucket(radar.get('nearest_km'), prev_radar_bucket)

    PUBLIC_STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PUBLIC_STATUS_FILE.write_text(json.dumps({
        'checked_at_utc': now,
        'lightning': {'band': new_band, 'nearest_km': lightning.get('nearest_km')},
        'radar': {'nearest_km': radar.get('nearest_km'), 'bucket': new_radar_bucket},
        'ec_alerts': current_alert_names,
    }))

    save_state({'lightning_band': new_band, 'alert_names': current_alert_names})


if __name__ == '__main__':
    try:
        main()
    except Exception:
        with ALERT_LOG.open('a') as f:
            f.write(f'{datetime.now(timezone.utc).isoformat(timespec="seconds")} ALERT edmonton_folk_fest: watch.py crashed:\n{traceback.format_exc()}\n')
        raise SystemExit(1)
