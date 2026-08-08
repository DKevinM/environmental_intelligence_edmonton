from modules.weather.metrics import humidex,summarize
from core.timefmt import format_short,localize
R={'UNKNOWN':-1,'LOW':0,'MODERATE':1,'HIGH':2,'EXTREME':3}
def level(v,m,h,e=None):
    if v is None:return 'UNKNOWN'
    if e is not None and v>=e:return 'EXTREME'
    if v>=h:return 'HIGH'
    if v>=m:return 'MODERATE'
    return 'LOW'
def top(*x):return max(x,key=lambda z:R[z])
def _hours_until(when,observed_at,tz):
    if not when or not observed_at:return None
    now_dt=localize(observed_at,tz); when_dt=localize(when,tz)
    if not now_dt or not when_dt:return None
    return max(0,round((when_dt-now_dt).total_seconds()/3600))
def assess(cfg,w,aq,fx,shear=None):
    t=cfg['thresholds']; c=w['current']; tz=cfg['project'].get('timezone','America/Edmonton')
    # Match the 12h window shown in the hourly outlook table below, so the
    # "peak" hazard callouts always point at an hour the visitor can see.
    s=summarize(w.get('hourly',[])[:12]); hx=humidex(c.get('temperature_c'),c.get('relative_humidity_pct'))
    heatv=max([v for v in (c.get('apparent_temperature_c'),hx,s.get('max_apparent_temperature_c')) if v is not None],default=None); gust=max([v for v in (c.get('wind_gust_kmh'),s.get('max_wind_gust_kmh')) if v is not None],default=None)
    heat=level(heatv,**{'m':t['heat']['moderate_c'],'h':t['heat']['high_c'],'e':t['heat']['extreme_c']}); wind=level(gust,t['wind_gust_kmh']['moderate'],t['wind_gust_kmh']['high'],t['wind_gust_kmh']['extreme'])
    rain=top(level(s.get('max_precipitation_probability_pct'),t['precipitation_probability']['moderate'],t['precipitation_probability']['high']),level(s.get('max_hourly_precipitation_mm'),t['precipitation_mm_hour']['moderate'],t['precipitation_mm_hour']['high']))
    av=max([v for v in (aq.get('aqhi'),fx.get('plus_3h')) if v is not None],default=None); air=level(av,t['aqhi']['moderate'],t['aqhi']['high'],t['aqhi']['extreme']); thunder='HIGH' if s['thunderstorm_possible'] else ('MODERATE' if (s.get('max_precipitation_probability_pct') or 0)>=60 and (gust or 0)>=45 else 'LOW')
    hazards={'air_quality':{'risk':air,'indicator':av,'unit':'AQHI'},'heat':{'risk':heat,'indicator':heatv,'unit':'°C apparent/humidex'},'wind':{'risk':wind,'indicator':gust,'unit':'km/h peak gust'},'precipitation':{'risk':rain,'indicator':s.get('max_hourly_precipitation_mm'),'unit':'mm/h maximum','probability_pct':s.get('max_precipitation_probability_pct'),'peak_in_hours':_hours_until(s.get('max_hourly_precipitation_time'),w.get('observed_at'),tz)},'thunderstorm':{'risk':thunder,'indicator':format_short(s.get('first_thunderstorm_hour'),tz),'unit':'first forecast signal'}}
    # AQHI rate-of-change: only a rising AQHI is a hazard signal, a falling/flat one is not
    tr=t.get('aqhi_rate',{'moderate':1.0,'high':2.0,'extreme':3.0}); rate1h=aq.get('aqhi_change_1h')
    rate_risk='UNKNOWN' if rate1h is None else ('LOW' if rate1h<=0 else level(rate1h,tr['moderate'],tr['high'],tr['extreme']))
    hazards['aqhi_rate_of_change']={'risk':rate_risk,'indicator':rate1h,'unit':'AQHI change/hour'}
    # Wind shear: surface vs upper-level HRDPS wind direction divergence (see modules/wind_shear)
    shear=shear or {}; ts=t.get('wind_shear',{'moderate':45,'high':90,'extreme':135})
    hazards['wind_shear']={'risk':level(shear.get('direction_diff_deg'),ts['moderate'],ts['high'],ts['extreme']),'indicator':shear.get('direction_diff_deg'),'unit':f"° direction diff ({shear.get('low_level_m',10)}m vs {shear.get('high_level_m',120)}m)"}
    return {'overall_risk':top(*[x['risk'] for x in hazards.values()]),'hazards':hazards,'weather_metrics':{'humidex':hx,**s}}
