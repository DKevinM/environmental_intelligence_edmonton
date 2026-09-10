import time
import requests
from core.geometry import point_in_geometry
BASE='https://api.weather.gc.ca/collections/weather-alerts/items'
ACTIVE_STATUSES=('issued','continued')
# api.weather.gc.ca has real intermittent flakiness (confirmed directly:
# alternating fast-success/hard-timeout on a single stable IP, not a full
# outage) - a bare 1-shot request fails roughly half the time it hits a bad
# window. 3 attempts with a short gap absorbs that without a long timeout.
ATTEMPTS=3
RETRY_DELAY_S=3
def load_weather_alerts(cfg,buffer_deg=0.6,timeout=15):
    lat=float(cfg['event']['latitude']); lon=float(cfg['event']['longitude'])
    bbox=f'{lon-buffer_deg},{lat-buffer_deg},{lon+buffer_deg},{lat+buffer_deg}'
    last_ex=None
    for attempt in range(1,ATTEMPTS+1):
        try:
            r=requests.get(BASE,params={'f':'json','bbox':bbox,'limit':100},timeout=timeout)
            r.raise_for_status()
            rows=r.json().get('features',[])
            last_ex=None
            break
        except Exception as ex:
            last_ex=ex
            if attempt<ATTEMPTS:time.sleep(RETRY_DELAY_S)
    if last_ex is not None:
        return {'status':'error','error':f'{type(last_ex).__name__}: {last_ex}'}
    hits=[]
    for f in rows:
        p=f.get('properties') or {}
        if p.get('status_en') not in ACTIVE_STATUSES:continue
        if not point_in_geometry(lat,lon,f.get('geometry')):continue
        hits.append({
            'name':p.get('alert_name_en'),
            'short_name':p.get('alert_short_name_en'),
            'risk_colour':p.get('risk_colour_en'),
            'region':p.get('feature_name_en'),
            'status':p.get('status_en'),
            'published_at':p.get('publication_datetime'),
            'expires_at':p.get('expiration_datetime'),
            'text':p.get('alert_text_en'),
        })
    seen=set(); dedup=[]
    for h in hits:
        k=(h['name'],h['region'])
        if k in seen:continue
        seen.add(k); dedup.append(h)
    return {'status':'ok','count':len(dedup),'alerts':dedup}
