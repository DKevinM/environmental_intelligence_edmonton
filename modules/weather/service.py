import json
from core.config import resolve_path
from .open_meteo import fetch
def load_weather(cfg):
    mode=str(cfg.get('data_mode','auto')).lower(); e=cfg['event']; w=cfg.get('weather',{}); err=None
    if mode in ('auto','live'):
        try:return fetch(float(e['latitude']),float(e['longitude']),cfg['project'].get('timezone','America/Edmonton'),int(w.get('forecast_hours',24)),int(w.get('timeout_seconds',20)))
        except Exception as ex:
            if mode=='live':raise
            err=f'{type(ex).__name__}: {ex}'
    data=json.loads(resolve_path(cfg,'data/sample/weather.json').read_text()); data['fallback_reason']=err or 'sample mode selected'; return data
