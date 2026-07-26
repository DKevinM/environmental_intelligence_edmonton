from math import exp,log
THUNDER={95,96,99}
def humidex(t,rh):
    if t is None or rh is None:return None
    a,b=17.625,243.04; g=a*t/(b+t)+log(max(rh,1)/100); d=b*g/(a-g); e=6.11*exp(5417.753*(1/273.16-1/(273.15+d))); return round(t+.5555*(e-10),1)
def summarize(rows):
    def vs(k):return [r[k] for r in rows if r.get(k) is not None]
    def mx(k):
        x=vs(k); return max(x) if x else None
    ts=[r['time'] for r in rows if r.get('weather_code') in THUNDER]
    rain=vs('precipitation_mm')
    return {'max_temperature_c':mx('temperature_c'),'max_apparent_temperature_c':mx('apparent_temperature_c'),'max_precipitation_probability_pct':mx('precipitation_probability_pct'),'max_hourly_precipitation_mm':mx('precipitation_mm'),'total_precipitation_mm':round(sum(rain),1) if rain else None,'max_wind_gust_kmh':mx('wind_gust_kmh'),'thunderstorm_possible':bool(ts),'first_thunderstorm_hour':ts[0] if ts else None}
