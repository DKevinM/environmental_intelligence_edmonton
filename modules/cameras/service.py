import hashlib,json,time
import requests
from core.config import ROOT
from core.geometry import haversine_km,bearing_deg,compass
STATE_FILE=ROOT/'output'/'.camera_freshness.json'
def load_state():
    try:return json.loads(STATE_FILE.read_text())
    except Exception:return {}
def save_state(state):
    STATE_FILE.parent.mkdir(parents=True,exist_ok=True); STATE_FILE.write_text(json.dumps(state))
def image_hash(url,timeout):
    try:
        r=requests.get(url,timeout=timeout); r.raise_for_status(); return hashlib.md5(r.content).hexdigest()
    except Exception:
        return None
def load_nearby_cameras(cfg):
    cc=cfg.get('cameras',{}) or {}
    base=cc.get('base_url','https://511.alberta.ca/api/v2/get/cameras'); radius_km=float(cc.get('radius_km',15)); max_cameras=int(cc.get('max_cameras',4))
    candidate_pool=int(cc.get('candidate_pool',10)); stale_after_hours=float(cc.get('stale_after_hours',2)); timeout=float(cc.get('timeout_seconds',20))
    e=cfg['event']; lat,lon=float(e['latitude']),float(e['longitude'])
    try:
        r=requests.get(base,params={'format':'json'},timeout=timeout); r.raise_for_status()
        rows=r.json()
    except Exception as ex:
        return {'status':'error','error':f'{type(ex).__name__}: {ex}'}
    cand=[]
    for c in rows:
        clat,clon=c.get('Latitude'),c.get('Longitude')
        if clat is None or clon is None:continue
        d=haversine_km(lat,lon,clat,clon)
        if d>radius_km:continue
        views=[v for v in (c.get('Views') or []) if v.get('Status')=='Enabled' and v.get('Url')]
        if not views:continue
        b=bearing_deg(lat,lon,clat,clon)
        cand.append({'id':c.get('Id'),'name':c.get('Location') or c.get('Roadway') or f"Camera {c.get('Id')}",'roadway':c.get('Roadway'),'distance_km':round(d,2),'direction':compass(b),'image_url':views[0]['Url']})
    cand.sort(key=lambda x:x['distance_km'])
    if not cand:return {'status':'ok','count':0,'cameras':[]}
    pool=cand[:candidate_pool]; state=load_state(); now=time.time(); fresh=[]; stale_count=0
    for c in pool:
        cid=str(c['id']); h=image_hash(c['image_url'],timeout); prev=state.get(cid)
        if h is None:continue
        unchanged_since=prev.get('unchanged_since',now) if (prev and prev.get('hash')==h) else now
        state[cid]={'hash':h,'unchanged_since':unchanged_since,'last_checked':now}
        age_hours=(now-unchanged_since)/3600
        if age_hours>=stale_after_hours:
            stale_count+=1; continue
        fresh.append(c)
        if len(fresh)>=max_cameras:break
    save_state(state)
    return {'status':'ok','count':len(fresh),'cameras':fresh,'excluded_stale':stale_count}
