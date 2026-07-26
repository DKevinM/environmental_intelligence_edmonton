from datetime import datetime
from zoneinfo import ZoneInfo
import logging,traceback
from core.config import load_config,ROOT
from core.io import write_json
from modules.weather.service import load_weather
from modules.air_quality.service import load_current_aqhi,load_forecast_aqhi,load_blend_estimate,load_nearest_pollutant,load_nearest_purpleair
from modules.intelligence.hazard_engine import assess
from modules.intelligence.narrative import build
from modules.intelligence.dashboard import build_html
from modules.intelligence import map_layers
from modules.fire.service import load_hotspots
from modules.cameras.service import load_nearby_cameras
from modules.wind_trajectory.service import load_trajectory
from modules.alerts.service import load_weather_alerts
def main():
 cfg=load_config();out=ROOT/'output';out.mkdir(exist_ok=True);logging.basicConfig(level=logging.INFO,format='%(asctime)s | %(levelname)s | %(message)s',handlers=[logging.FileHandler(out/'run.log'),logging.StreamHandler()]);log=logging.getLogger()
 try:
  w=load_weather(cfg); aq=load_current_aqhi(cfg); fx=load_forecast_aqhi(cfg); aq['blend']=load_blend_estimate(cfg); aq['pollutant']=load_nearest_pollutant(cfg); aq['purpleair']=load_nearest_purpleair(cfg); a=assess(cfg,w,aq,fx); fire=load_hotspots(cfg); cams=load_nearby_cameras(cfg); traj=load_trajectory(cfg); wx_alerts=load_weather_alerts(cfg); n=build(cfg,w,aq,fx,a,fire,traj,wx_alerts); mp=map_layers.build(cfg); mp['fire']=fire; mp['trajectory']=traj; now=datetime.now(ZoneInfo(cfg['project']['timezone'])).isoformat(timespec='seconds'); p={'generated_at':now,'event':cfg['event'],'weather':w,'air_quality':{'current':aq,'forecast':fx},'assessment':a,'narrative':n,'map':mp,'cameras':cams,'wx_alerts':wx_alerts};write_json(out/'dashboard_data.json',p);write_json(out/'intelligence_summary.json',{'generated_at':now,'assessment':a,'narrative':n});(out/'dashboard.html').write_text(build_html(cfg,p));print(f"Overall risk: {a['overall_risk']}\nDashboard: {out/'dashboard.html'}");return 0
 except Exception:log.error(traceback.format_exc());return 1
if __name__=='__main__':raise SystemExit(main())
