import os,csv,io,requests
from core.geometry import haversine_km,bearing_deg,compass
CONF_MAP={'l':0.3,'n':0.6,'h':0.9}
def num(v):
    try:return float(v)
    except:return None
def confidence_value(v):
    if v in CONF_MAP:return CONF_MAP[v]
    n=num(v)
    return n/100 if n is not None else None
def bbox_for(lat,lon,radius_km):
    dlat=radius_km/111.0
    from math import cos,radians
    dlon=radius_km/(111.0*max(cos(radians(lat)),0.01))
    return lon-dlon,lat-dlat,lon+dlon,lat+dlat
def load_hotspots(cfg):
    fc=cfg.get('firms',{}) or {}; key=os.environ.get('FIRMS_API_KEY')
    if not key:return {'status':'missing','reason':'FIRMS_API_KEY not set in environment'}
    e=cfg['event']; lat,lon=float(e['latitude']),float(e['longitude'])
    radius_km=float(fc.get('radius_km',300)); cluster_km=float(fc.get('cluster_km',10)); min_conf=float(fc.get('min_confidence',0.30))
    base=fc.get('base_url','https://firms.modaps.eosdis.nasa.gov'); source=fc.get('source','VIIRS_SNPP_NRT'); day_range=int(fc.get('day_range',2))
    w,s,eas,n=bbox_for(lat,lon,radius_km)
    url=f"{base}/api/area/csv/{key}/{source}/{w:.4f},{s:.4f},{eas:.4f},{n:.4f}/{day_range}"
    try:
        r=requests.get(url,timeout=float(fc.get('timeout_seconds',20))); r.raise_for_status()
        rows=list(csv.DictReader(io.StringIO(r.text)))
    except Exception as ex:
        return {'status':'error','error':f'{type(ex).__name__}: {ex}'}
    cand=[]
    for row in rows:
        rlat,rlon=num(row.get('latitude')),num(row.get('longitude'))
        if rlat is None or rlon is None:continue
        cv=confidence_value(row.get('confidence'))
        if cv is not None and cv<min_conf:continue
        d=haversine_km(lat,lon,rlat,rlon)
        if d>radius_km:continue
        cand.append({'lat':rlat,'lon':rlon,'distance_km':d,'frp':num(row.get('frp')),'confidence':row.get('confidence'),'acq_date':row.get('acq_date'),'acq_time':row.get('acq_time'),'daynight':row.get('daynight')})
    cand.sort(key=lambda x:x['distance_km'])
    clustered=[]
    for c in cand:
        if any(haversine_km(c['lat'],c['lon'],k['lat'],k['lon'])<=cluster_km for k in clustered):continue
        b=bearing_deg(lat,lon,c['lat'],c['lon'])
        c['direction']=compass(b); c['bearing_deg']=round(b,1); c['distance_km']=round(c['distance_km'],1)
        clustered.append(c)
    if not clustered:return {'status':'ok','count':0,'hotspots':[],'nearest':None}
    return {'status':'ok','count':len(clustered),'hotspots':clustered[:20],'nearest':clustered[0]}
