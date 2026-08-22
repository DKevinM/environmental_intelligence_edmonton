import json,os,subprocess,datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from core.geometry import haversine_km,bearing_deg,compass
def load_trajectory(cfg):
    tc=cfg.get('wind_trajectory',{}) or {}
    ab_winds_dir=tc.get('ab_winds_dir','/opt/airquality/github/AB_winds')
    python_bin=tc.get('python_bin','/opt/airquality/venv/bin/python3')
    hours=float(tc.get('hours',6)); timeout=float(tc.get('timeout_seconds',120))
    e=cfg['event']; tz=cfg['project'].get('timezone','America/Edmonton')
    now_local=datetime.datetime.now(ZoneInfo(tz)).replace(minute=0,second=0,microsecond=0)
    outdir=Path(cfg['_root'])/'output'/'wind_trajectory'; outdir.mkdir(parents=True,exist_ok=True)
    env=dict(os.environ); env.update({'LAT':str(e['latitude']),'LON':str(e['longitude']),'TIME_LOCAL':now_local.strftime('%Y-%m-%dT%H:%M:%S'),'HOURS':str(hours),'OUTDIR':str(outdir)})
    try:
        r=subprocess.run([python_bin,'odour/backtraj_core.py'],cwd=ab_winds_dir,env=env,capture_output=True,text=True,timeout=timeout)
    except Exception as ex:
        return {'status':'error','error':f'{type(ex).__name__}: {ex}'}
    if r.returncode!=0:
        return {'status':'error','error':(r.stderr or 'unknown error')[-2000:]}
    try:
        centerlines=json.loads((outdir/'backtraj_centerlines.geojson').read_text())
        density=json.loads((outdir/'backtraj_density.geojson').read_text())
    except Exception as ex:
        return {'status':'error','error':f'output files missing: {ex}'}
    origin=None
    if centerlines.get('features'):
        coords=centerlines['features'][0]['geometry']['coordinates']
        if coords:
            olon,olat=coords[-1]
            d=haversine_km(float(e['latitude']),float(e['longitude']),olat,olon); b=bearing_deg(float(e['latitude']),float(e['longitude']),olat,olon)
            origin={'lat':olat,'lon':olon,'distance_km':round(d,1),'direction':compass(b)}
    return {'status':'ok','hours':hours,'valid_time_local':now_local.isoformat(),'centerlines':centerlines,'density':density,'origin':origin}
def nearest_fire_on_path(centerlines,fire_hotspots):
    if not centerlines or not centerlines.get('features') or not fire_hotspots:return None
    coords=centerlines['features'][0]['geometry']['coordinates']
    if len(coords)<2:return None
    vlon,vlat=coords[0]  # track_center[0] in backtraj_core.py is t=0, i.e. the venue itself
    best=None
    for h in fire_hotspots:
        fire_dist_from_venue=haversine_km(h['lat'],h['lon'],vlat,vlon)
        # Only count path points that have travelled at least as far from the
        # venue as the fire itself sits. Without this, a fire that merely
        # happens to be near the venue - in any direction, including the
        # opposite direction from where the trajectory actually heads -
        # trivially "passes near" the path's own starting point, producing a
        # false "smoke transport plausible" match (e.g. air arriving from the
        # S reported as plausibly carrying smoke from a fire to the NE).
        candidates=[(clat,clon) for clon,clat in coords if haversine_km(vlat,vlon,clat,clon)>=fire_dist_from_venue]
        if not candidates:continue
        m=min(haversine_km(h['lat'],h['lon'],clat,clon) for clat,clon in candidates)
        if best is None or m<best[0]:best=(m,h)
    if best is None:return None
    dist,hotspot=best
    return {'hotspot':hotspot,'min_distance_to_path_km':round(dist,1)}
