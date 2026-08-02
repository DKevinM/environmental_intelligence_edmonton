import os,gzip,json,requests
from math import atan2,degrees,hypot
from datetime import datetime,timezone
def _num(v):
    try:return float(v)
    except:return None
def _parse(t):return datetime.fromisoformat(t.replace('Z','+00:00'))
def load_wind_shear(cfg,low_m=10,high_m=120):
    sc=cfg.get('wind_shear',{}) or {}
    base=os.environ.get('SUPABASE_URL'); key=os.environ.get('SUPABASE_SERVICE_KEY')
    if not base or not key:return {'status':'missing','reason':'SUPABASE_URL/SUPABASE_SERVICE_KEY not set'}
    e=cfg['event']; lat,lon=float(e['latitude']),float(e['longitude']); timeout=float(sc.get('timeout_seconds',20))
    headers={'apikey':key,'Authorization':f'Bearer {key}'}
    try:
        url=f"{base}/rest/v1/wind_files?select=run_time,forecast_hour,valid_time,file_path&model=eq.HRDPS&order=run_time.desc,forecast_hour.asc&limit=40"
        r=requests.get(url,headers=headers,timeout=timeout); r.raise_for_status(); rows=[x for x in r.json() if x.get('valid_time')]
    except Exception as ex:
        return {'status':'error','error':f'{type(ex).__name__}: {ex}'}
    if not rows:return {'status':'missing','reason':'no HRDPS files recorded'}
    now=datetime.now(timezone.utc)
    row=min(rows,key=lambda x:abs((_parse(x['valid_time'])-now).total_seconds()))
    try:
        obj=requests.get(f"{base}/storage/v1/object/public/winds/{row['file_path']}",headers=headers,timeout=timeout)
        obj.raise_for_status(); data=json.loads(gzip.decompress(obj.content))
    except Exception as ex:
        return {'status':'error','error':f'{type(ex).__name__}: {ex}'}
    g=data.get('grid') or {}; lo1,la1,dx,dy,nx,ny=g.get('lo1'),g.get('la1'),g.get('dx'),g.get('dy'),g.get('nx'),g.get('ny')
    if None in (lo1,la1,dx,dy,nx,ny):return {'status':'error','error':'grid metadata missing from stored file'}
    col=min(max(round((lon-lo1)/dx),0),nx-1); rowi=min(max(round((la1-lat)/dy),0),ny-1)
    f=data.get('fields') or {}
    def cell(key):
        v=f.get(key)
        try:return v[0][rowi][col] if v is not None else None
        except Exception:return None
    u_lo,v_lo,u_hi,v_hi=cell(f'ugrd{low_m}'),cell(f'vgrd{low_m}'),cell(f'ugrd{high_m}'),cell(f'vgrd{high_m}')
    if None in (u_lo,v_lo,u_hi,v_hi):return {'status':'missing','reason':f'wind components unavailable at {low_m}m/{high_m}m for this grid cell','valid_time':row['valid_time']}
    dir_lo=(degrees(atan2(u_lo,v_lo))+180)%360; dir_hi=(degrees(atan2(u_hi,v_hi))+180)%360
    diff=abs(dir_hi-dir_lo); diff=min(diff,360-diff)
    return {'status':'ok','valid_time':row['valid_time'],'forecast_hour':row.get('forecast_hour'),'low_level_m':low_m,'high_level_m':high_m,
            'surface_wind_dir_deg':round(dir_lo,1),'surface_wind_speed_kmh':round(hypot(u_lo,v_lo)*3.6,1),
            'upper_wind_dir_deg':round(dir_hi,1),'upper_wind_speed_kmh':round(hypot(u_hi,v_hi)*3.6,1),
            'direction_diff_deg':round(diff,1)}
