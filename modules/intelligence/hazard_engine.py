from modules.weather.metrics import humidex,summarize
from core.timefmt import format_short
R={'UNKNOWN':-1,'LOW':0,'MODERATE':1,'HIGH':2,'EXTREME':3}
def level(v,m,h,e=None):
    if v is None:return 'UNKNOWN'
    if e is not None and v>=e:return 'EXTREME'
    if v>=h:return 'HIGH'
    if v>=m:return 'MODERATE'
    return 'LOW'
def top(*x):return max(x,key=lambda z:R[z])
def assess(cfg,w,aq,fx):
    t=cfg['thresholds']; c=w['current']; s=summarize(w.get('hourly',[])); hx=humidex(c.get('temperature_c'),c.get('relative_humidity_pct'))
    heatv=max([v for v in (c.get('apparent_temperature_c'),hx,s.get('max_apparent_temperature_c')) if v is not None],default=None); gust=max([v for v in (c.get('wind_gust_kmh'),s.get('max_wind_gust_kmh')) if v is not None],default=None)
    heat=level(heatv,**{'m':t['heat']['moderate_c'],'h':t['heat']['high_c'],'e':t['heat']['extreme_c']}); wind=level(gust,t['wind_gust_kmh']['moderate'],t['wind_gust_kmh']['high'],t['wind_gust_kmh']['extreme'])
    rain=top(level(s.get('max_precipitation_probability_pct'),t['precipitation_probability']['moderate'],t['precipitation_probability']['high']),level(s.get('max_hourly_precipitation_mm'),t['precipitation_mm_hour']['moderate'],t['precipitation_mm_hour']['high']))
    av=max([v for v in (aq.get('aqhi'),fx.get('plus_3h')) if v is not None],default=None); air=level(av,t['aqhi']['moderate'],t['aqhi']['high'],t['aqhi']['extreme']); thunder='HIGH' if s['thunderstorm_possible'] else ('MODERATE' if (s.get('max_precipitation_probability_pct') or 0)>=60 and (gust or 0)>=45 else 'LOW')
    hazards={'heat':{'risk':heat,'indicator':heatv,'unit':'°C apparent/humidex'},'wind':{'risk':wind,'indicator':gust,'unit':'km/h peak gust'},'precipitation':{'risk':rain,'indicator':s.get('max_hourly_precipitation_mm'),'unit':'mm/h maximum'},'air_quality':{'risk':air,'indicator':av,'unit':'AQHI'},'thunderstorm':{'risk':thunder,'indicator':format_short(s.get('first_thunderstorm_hour'),cfg['project'].get('timezone','America/Edmonton')),'unit':'first forecast signal'}}
    return {'overall_risk':top(*[x['risk'] for x in hazards.values()]),'hazards':hazards,'weather_metrics':{'humidex':hx,**s}}
