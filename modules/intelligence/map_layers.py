from core.config import resolve_path
from core.geometry import haversine_km
from core.io import read_structured_source
def num(v):
    try:return float(v)
    except:return None
def in_bbox(ring,lat,lon,half):
    lons=[c[0] for c in ring]; lats=[c[1] for c in ring]
    return max(lons)>=lon-half and min(lons)<=lon+half and max(lats)>=lat-half and min(lats)<=lat+half
def load_firesmoke(cfg):
    path=cfg.get('air_quality',{}).get('firesmoke_current_file')
    if not path:return None
    try:data=read_structured_source(str(resolve_path(cfg,path)))
    except Exception:return None
    e=cfg['event']; lat,lon=float(e['latitude']),float(e['longitude']); half=float(cfg.get('map',{}).get('half_degree_bbox',0.6))
    out=[]
    for f in data.get('features',[]):
        g=f.get('geometry') or {}
        if g.get('type')!='Polygon':continue
        if in_bbox(g['coordinates'][0],lat,lon,half):
            p=f.get('properties') or {}
            out.append({'type':'Feature','geometry':g,'properties':{'pm25':p.get('pm25'),'timestamp':p.get('timestamp')}})
    return {'type':'FeatureCollection','features':out}
def load_aqhi_grid(cfg):
    path=cfg.get('air_quality',{}).get('blend_grid_file')
    if not path:return None
    try:data=read_structured_source(str(resolve_path(cfg,path)))
    except Exception:return None
    e=cfg['event']; lat,lon=float(e['latitude']),float(e['longitude']); half=float(cfg.get('map',{}).get('half_degree_bbox',0.6))
    out=[]
    for f in data.get('features',[]):
        g=f.get('geometry') or {}
        if g.get('type')!='Polygon':continue
        if in_bbox(g['coordinates'][0],lat,lon,half):
            p=f.get('properties') or {}
            out.append({'type':'Feature','geometry':g,'properties':{'value':p.get('value'),'color':p.get('color'),'confidence':p.get('confidence'),'n_points':p.get('n_points')}})
    return {'type':'FeatureCollection','features':out}
def load_purpleair_points(cfg):
    path=cfg.get('air_quality',{}).get('purpleair_source')
    if not path:return []
    try:rows=read_structured_source(str(resolve_path(cfg,path)))
    except Exception:return []
    e=cfg['event']; lat,lon=float(e['latitude']),float(e['longitude']); radius=float(cfg.get('map',{}).get('purpleair_radius_km',25))
    out=[]
    for r in rows:
        if not r.get('use_for_map'):continue
        la,lo=r.get('latitude'),r.get('longitude')
        if la is None or lo is None:continue
        d=haversine_km(lat,lon,la,lo)
        if d>radius:continue
        pm=r.get('pm_corr') if r.get('pm_corr') is not None else r.get('pm2.5_atm')
        out.append({'name':r.get('name'),'lat':la,'lon':lo,'pm25':round(pm,1) if pm is not None else None,'distance_km':round(d,2),'quality_flag':r.get('quality_flag')})
    return out
def load_station_points(cfg):
    path=cfg.get('air_quality',{}).get('current_source')
    if not path:return []
    try:rows=read_structured_source(str(resolve_path(cfg,path)))
    except Exception:return []
    e=cfg['event']; lat,lon=float(e['latitude']),float(e['longitude']); radius=float(cfg.get('map',{}).get('station_radius_km',40))
    out=[]
    for r in rows:
        la,lo=num(r.get('Latitude')),num(r.get('Longitude'))
        if la is None or lo is None:continue
        d=haversine_km(lat,lon,la,lo)
        if d>radius:continue
        out.append({'name':r.get('StationName'),'lat':la,'lon':lo,'aqhi':num(r.get('AQHI')),'aqhi_3h':num(r.get('AQHI_forecast_3h')),'distance_km':round(d,2)})
    return out
def build(cfg):
    return {'firesmoke':load_firesmoke(cfg),'aqhi_grid':load_aqhi_grid(cfg),'purpleair':load_purpleair_points(cfg),'stations':load_station_points(cfg)}
