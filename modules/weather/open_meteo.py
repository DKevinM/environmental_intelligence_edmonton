import requests
URL='https://api.open-meteo.com/v1/forecast'
CURRENT=['temperature_2m','relative_humidity_2m','apparent_temperature','precipitation','weather_code','cloud_cover','surface_pressure','wind_speed_10m','wind_direction_10m','wind_gusts_10m']
HOURLY=['temperature_2m','relative_humidity_2m','apparent_temperature','precipitation_probability','precipitation','weather_code','cloud_cover','wind_speed_10m','wind_direction_10m','wind_gusts_10m']
MAP={'temperature_2m':'temperature_c','relative_humidity_2m':'relative_humidity_pct','apparent_temperature':'apparent_temperature_c','precipitation_probability':'precipitation_probability_pct','precipitation':'precipitation_mm','weather_code':'weather_code','cloud_cover':'cloud_cover_pct','surface_pressure':'surface_pressure_hpa','wind_speed_10m':'wind_speed_kmh','wind_direction_10m':'wind_direction_deg','wind_gusts_10m':'wind_gust_kmh'}
def fetch(lat,lon,tz,hours=24,timeout=20):
    p={'latitude':lat,'longitude':lon,'timezone':tz,'forecast_days':2,'current':','.join(CURRENT),'hourly':','.join(HOURLY),'wind_speed_unit':'kmh','temperature_unit':'celsius','precipitation_unit':'mm'}
    r=requests.get(URL,params=p,timeout=timeout,headers={'User-Agent':'EventEnvironmentalIntelligence/1.0'}); r.raise_for_status(); raw=r.json(); c=raw['current']
    current={MAP[k]:c.get(k) for k in CURRENT}; rows=[]
    for i,t in enumerate(raw['hourly'].get('time',[])):
        if t < c['time'][:13]+':00':continue
        row={'time':t}
        for k in HOURLY:
            vals=raw['hourly'].get(k,[]); row[MAP[k]]=vals[i] if i<len(vals) else None
        rows.append(row)
        if len(rows)>=hours:break
    return {'source':'open_meteo','observed_at':c['time'],'current':current,'hourly':rows,'provider_metadata':{'latitude':raw.get('latitude'),'longitude':raw.get('longitude'),'elevation_m':raw.get('elevation'),'timezone':raw.get('timezone')}}
