from datetime import datetime
from zoneinfo import ZoneInfo
def localize(value,tz_name):
    if not value:return None
    try:dt=datetime.fromisoformat(value)
    except ValueError:return None
    return dt.replace(tzinfo=ZoneInfo(tz_name)) if dt.tzinfo is None else dt.astimezone(ZoneInfo(tz_name))
# Alberta stays on UTC-6 year-round from 2026-11-01; tzdata labels that CST, locally it's MDT
_LABELS={'America/Edmonton':{'CST':'MDT'}}
def _abbrev(dt,tz_name):
    z=dt.strftime('%Z'); return _LABELS.get(tz_name,{}).get(z,z)
def format_long(value,tz_name):
    dt=localize(value,tz_name); return dt.strftime('%a, %b %-d, %Y · %-I:%M %p ')+_abbrev(dt,tz_name) if dt else 'unavailable'
def format_short(value,tz_name):
    dt=localize(value,tz_name); return dt.strftime('%a %-I:%M %p') if dt else None
def tz_abbrev(tz_name):
    return _abbrev(datetime.now(ZoneInfo(tz_name)),tz_name)
