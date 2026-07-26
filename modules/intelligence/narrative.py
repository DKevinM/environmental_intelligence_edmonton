from core.geometry import compass
from core.timefmt import format_short
from core.aqhi import cap_str as faqhi, eccc_messages
from modules.wind_trajectory.service import nearest_fire_on_path
def f(v,d=0):return 'unavailable' if v is None else f'{v:.{d}f}'
def sensor_label(source):
    fam=(source or '').split('_')[0]
    return {'VIIRS':'NASA FIRMS – VIIRS','MODIS':'NASA FIRMS – MODIS','LANDSAT':'NASA FIRMS – Landsat'}.get(fam,'NASA FIRMS' if not fam else f'NASA FIRMS – {fam}')
def build(cfg,w,aq,fx,a,fire=None,trajectory=None,wx_alerts=None):
 c=w['current']; m=a['weather_metrics']; h=a['hazards']; parts=[f"At {cfg['event']['name']}, temperature is {f(c.get('temperature_c'),1)}°C and feels near {f(c.get('apparent_temperature_c'),1)}°C. Winds are {f(c.get('wind_speed_kmh'))} km/h from {compass(c.get('wind_direction_deg'))}, gusting near {f(c.get('wind_gust_kmh'))} km/h."]
 wx=(wx_alerts or {}).get('alerts') or []
 if wx:parts.append(f"Environment Canada has {len(wx)} active alert(s) in effect for the venue: {', '.join(sorted(set(x['name'] for x in wx)))}.")
 tz=cfg['project'].get('timezone','America/Edmonton')
 parts.append(f"The nearest current AQHI is {faqhi(aq.get('aqhi'))} at {aq.get('station_name','the nearest point')}, {f(aq.get('distance_km'),1)} km from the venue." if aq.get('aqhi') is not None else 'A valid current AQHI was not available.')
 blend=aq.get('blend') or {}
 if blend.get('status')=='ok' and blend.get('value') is not None:parts.append(f"A gridded AQHI estimate blending official and community sensors (confidence: {blend.get('confidence','unknown')}) puts the area near {faqhi(blend.get('value'))}.")
 pollutant=aq.get('pollutant') or {}
 if pollutant.get('status')=='ok':parts.append(f"The nearest air monitoring station ({pollutant.get('station_name')}, {f(pollutant.get('distance_km'),1)} km) reports fine particulate matter (PM2.5) at {f(pollutant.get('value'),1)} µg/m³.")
 pa=aq.get('purpleair') or {}
 if pa.get('status')=='ok':
  loc='an on-site' if (pa.get('distance_km') or 99)<1 else 'a nearby'
  parts.append(f"{loc.capitalize()} community sensor ('{pa.get('name')}', {f(pa.get('distance_km'),1)} km) reads {f(pa.get('pm25'),1)} µg/m³ PM2.5.")
 wd=c.get('wind_direction_deg')
 traj_ok=(trajectory or {}).get('status')=='ok'; origin=(trajectory or {}).get('origin') if traj_ok else None
 if origin:
  parts.append(f"Back-trajectory modeling (HRDPS wind fields, {f(trajectory.get('hours'),0)} h lookback) indicates the air currently at the venue traveled from the vicinity of a point {origin['distance_km']} km to the {origin['direction']}, i.e. arriving from the {origin['direction']}.")
 elif wd is not None:
  parts.append(f"Surface winds are moving from the {compass(wd)} toward the {compass((wd+180)%360)}, the direction smoke and particulate matter are likely being carried across the area.")
 nearest_fire=(fire or {}).get('nearest')
 if nearest_fire:
  align=''
  path_check=nearest_fire_on_path(trajectory.get('centerlines'),[nearest_fire]) if traj_ok else None
  threshold=float(cfg.get('wind_trajectory',{}).get('fire_path_threshold_km',20))
  if path_check:
   dist=path_check['min_distance_to_path_km']
   if dist<=threshold:align=f' The modeled back-trajectory passes within {f(dist,1)} km of this fire, making smoke transport to the venue plausible based on wind-field modeling.'
   else:align=f' The modeled back-trajectory does not pass near this fire (nearest approach {f(dist,1)} km), so this specific fire is unlikely to be the source of any smoke reaching the venue right now.'
  elif wd is not None:
   diff=abs(nearest_fire['bearing_deg']-wd); upwind=min(diff,360-diff)<=45
   align=' This fire is roughly upwind of the venue, so smoke transport toward the site is plausible.' if upwind else ''
  parts.append(f"The nearest active fire detection ({sensor_label(cfg.get('firms',{}).get('source'))}, last {nearest_fire.get('acq_date','—')}) is {nearest_fire['distance_km']} km {nearest_fire['direction']} of the venue.{align}")
 if fx.get('plus_3h') is not None:
  when=format_short(fx.get('valid_at'),tz)
  parts.append(f"The AQHI forecast for {when or 'the next few hours'} is {faqhi(fx.get('plus_3h'))}.")
 if m.get('thunderstorm_possible'):parts.append(f"Thunderstorm conditions appear in the hourly forecast beginning around {format_short(m.get('first_thunderstorm_hour'),cfg['project'].get('timezone','America/Edmonton'))}.")
 elif (m.get('max_precipitation_probability_pct') or 0)>=40:parts.append(f"Precipitation probability reaches approximately {f(m.get('max_precipitation_probability_pct'))}%.")
 key=[k.replace('_',' ') for k,v in h.items() if v['risk'] in ('HIGH','EXTREME')]; headline=f"Overall operational environmental risk is {a['overall_risk']}."+(f" Primary concerns are {', '.join(key)}." if key else '')
 parts.append(headline); rec=[]
 if h['thunderstorm']['risk'] in ('HIGH','EXTREME'):rec.append('Confirm lightning monitoring, shelter, pause and evacuation procedures.')
 if h['heat']['risk'] in ('HIGH','EXTREME'):rec.append('Increase hydration, shade, cooling and heat-illness messaging.')
 if h['wind']['risk'] in ('HIGH','EXTREME'):rec.append('Review temporary structures, signage and stage wind limits.')
 if h['precipitation']['risk'] in ('HIGH','EXTREME'):rec.append('Prepare drainage, electrical protection and wet-weather controls.')
 if wx:rec.append(f"Active Environment Canada alert(s) for the venue — review details: {', '.join(sorted(set(x['name'] for x in wx)))}.")
 aqmsg=eccc_messages(h['air_quality']['risk'])
 if aqmsg:
  rec.append(f"Environment Canada AQHI guidance — general population: {aqmsg['general']}")
  rec.append(f"Environment Canada AQHI guidance — at-risk populations: {aqmsg['at_risk']}")
 if not rec:rec=['Continue routine monitoring and rerun as new observations arrive.']
 return {'headline':headline,'summary':' '.join(parts),'recommendations':rec}
