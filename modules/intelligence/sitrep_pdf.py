import base64
import io
from pathlib import Path

import qrcode
from weasyprint import HTML

from core.aqhi import cap as cap_aqhi
from core.aqhi import eccc_messages
from core.timefmt import format_long, format_short
from core.config import ROOT

ASSETS = ROOT / 'assets'
DASHBOARD_URL = 'https://dkevinm.github.io/environmental_intelligence_edmonton/'

RISK_LABEL = {'LOW': 'Low Risk', 'MODERATE': 'Moderate Risk', 'HIGH': 'High Risk', 'EXTREME': 'Very High Risk', 'UNKNOWN': 'Unavailable'}
RISK_COLOR = {'LOW': '#0f6cbd', 'MODERATE': '#e0a800', 'HIGH': '#e8590c', 'EXTREME': '#7d1935', 'UNKNOWN': '#6c757d'}


def _b64(path):
    return base64.b64encode(path.read_bytes()).decode('ascii')


def _qr_data_uri(url):
    img = qrcode.make(url, border=1)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode('ascii')


def _v(x, suffix=''):
    return '—' if x is None else f'{x}{suffix}'


def render_html(cfg, p, contact):
    tz = cfg['project'].get('timezone', 'America/Edmonton')
    e = cfg['event']
    w = p['weather']['current']
    aq = p['air_quality']['current']
    fx = p['air_quality']['forecast']
    a = p['assessment']
    n = p['narrative']
    air = a['hazards']['air_quality']
    risk = air['risk']
    msgs = eccc_messages(risk) or eccc_messages('LOW')

    logo_b64 = _b64(ASSETS / 'aca_logo.jpg')
    qr_b64 = _qr_data_uri(DASHBOARD_URL)

    hazard_rows = ''.join(
        f"<div class='hz' style='border-color:{RISK_COLOR.get(h['risk'], '#6c757d')}'>"
        f"<span class='hz-label'>{key.replace('_', ' ').title()}</span>"
        f"<span class='hz-risk' style='color:{RISK_COLOR.get(h['risk'], '#6c757d')}'>{RISK_LABEL.get(h['risk'], h['risk'])}</span>"
        f"<span class='hz-val'>{_v(cap_aqhi(h.get('indicator')) if key == 'air_quality' else h.get('indicator'))} {h.get('unit', '')}</span>"
        f"</div>"
        for key, h in a['hazards'].items()
    )

    summary_items = ''.join(f'<li>{pt}</li>' for pt in (n.get('summary_points') or [n['summary']]))
    rec_items = ''.join(f'<li>{r}</li>' for r in n.get('recommendations', []))

    blend = aq.get('blend') or {}
    pollutant = aq.get('pollutant') or {}
    pa = aq.get('purpleair') or {}
    local_cards = ''
    local_cards += f"<div class='lc'><small>Nearest station</small><b>{_v(cap_aqhi(aq.get('aqhi')))}</b><small>{aq.get('station_name', 'unavailable')} · {_v(aq.get('distance_km'), ' km')}</small></div>"
    if blend.get('status') == 'ok':
        local_cards += f"<div class='lc'><small>Blended estimate</small><b>{_v(cap_aqhi(blend.get('value')))}</b><small>confidence {blend.get('confidence', '—')}</small></div>"
    if pollutant.get('status') == 'ok':
        local_cards += f"<div class='lc'><small>PM2.5 (station)</small><b>{_v(pollutant.get('value'), ' µg/m³')}</b><small>{pollutant.get('station_name', '')} · {_v(pollutant.get('distance_km'), ' km')}</small></div>"
    if pa.get('status') == 'ok':
        local_cards += f"<div class='lc'><small>PM2.5 (community)</small><b>{_v(pa.get('pm25'), ' µg/m³')}</b><small>{pa.get('name', '')} · {_v(pa.get('distance_km'), ' km')}</small></div>"

    wx_alerts = (p.get('wx_alerts') or {}).get('alerts') or []
    if wx_alerts:
        wx_html = ''.join(f"<div class='alert'><b>{x.get('name', '').title()}</b> — {x.get('region', '')}</div>" for x in wx_alerts)
        wx_section = f"<section class='panel alertbox'><h2>Active Environment Canada Alerts</h2>{wx_html}</section>"
    else:
        wx_section = "<section class='panel okbox'><p>No active Environment Canada weather alerts for the venue.</p></section>"

    valid_label = format_short(fx.get('valid_at'), tz) or '+3h forecast'

    return f'''<!doctype html><html><head><meta charset="utf-8"><style>
@page {{ size: Letter; margin: 15mm 16mm; }}
body {{ font-family: Arial, Helvetica, sans-serif; color:#1a2733; font-size:11.5px; }}
h1 {{ font-size:20px; margin:0 0 2px; color:#0f6cbd; }}
h2 {{ font-size:13.5px; margin:0 0 8px; color:#0f6cbd; border-bottom:2px solid #0f6cbd; padding-bottom:3px; }}
header {{ display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px; }}
header .title {{ flex:1; margin-left:16px; }}
header img.logo {{ height:52px; }}
header .meta {{ text-align:right; font-size:11px; color:#4a5a68; }}
.contact {{ font-size:10px; color:#4a5a68; font-style:italic; margin-top:2px; }}
section.panel {{ margin-bottom:11px; }}
.current-aqhi {{ display:flex; align-items:center; gap:16px; background:#f2f6fa; border-radius:8px; padding:10px 14px; margin-bottom:8px; }}
.current-aqhi .big {{ font-size:34px; font-weight:bold; color:{RISK_COLOR.get(risk, '#0f6cbd')}; }}
.current-aqhi .lbl {{ font-size:11px; color:#4a5a68; }}
table.msg {{ width:100%; border-collapse:collapse; font-size:10.5px; margin-bottom:2px;}}
table.msg th, table.msg td {{ border:1px solid #c6d2dc; padding:6px 8px; text-align:left; vertical-align:top; }}
table.msg th {{ background:#eaf1f8; }}
table.msg tr.active td {{ background:#fff3cd; font-weight:bold; }}
.hazards {{ display:flex; gap:6px; flex-wrap:wrap; }}
.hz {{ flex:1; min-width:95px; border:1.5px solid; border-radius:6px; padding:6px 8px; text-align:center; }}
.hz-label {{ display:block; font-size:9px; color:#4a5a68; text-transform:uppercase; }}
.hz-risk {{ display:block; font-size:12.5px; font-weight:bold; margin:2px 0; }}
.hz-val {{ display:block; font-size:9.5px; color:#4a5a68; }}
ul {{ margin:4px 0 0; padding-left:16px; }}
li {{ margin-bottom:3px; }}
.lc-row {{ display:flex; gap:8px; }}
.lc {{ flex:1; background:#f2f6fa; border-radius:6px; padding:8px; text-align:center; }}
.lc small {{ display:block; color:#4a5a68; font-size:9px; }}
.lc b {{ display:block; font-size:17px; margin:2px 0; }}
.alertbox {{ border:1.5px solid #e8590c; border-radius:6px; padding:8px 10px; }}
.alertbox h2 {{ border-color:#e8590c; color:#e8590c; }}
.okbox {{ border:1.5px solid #2f9e44; border-radius:6px; padding:8px 10px; color:#2f9e44; }}
.alert {{ margin-bottom:4px; }}
footer {{ display:flex; justify-content:space-between; align-items:center; border-top:1px solid #c6d2dc; padding-top:8px; margin-top:8px; font-size:9.5px; color:#4a5a68; }}
footer img.qr {{ height:56px; width:56px; }}
footer .foot-text {{ max-width:75%; }}
</style></head>
<body>
<header>
  <img class="logo" src="data:image/jpeg;base64,{logo_b64}"/>
  <div class="title">
    <h1>Air Quality Situation Report</h1>
    <div>{e['name']} · {e.get('venue', '')}</div>
  </div>
  <div class="meta">
    <div><b>{format_long(p['generated_at'], tz)}</b></div>
    <div class="contact">For more information, contact {contact['name']} at {contact['phone']}</div>
  </div>
</header>

<section class="panel">
  <h2>Air Quality Health Index (AQHI) — Edmonton</h2>
  <div class="current-aqhi">
    <div class="big">{_v(cap_aqhi(aq.get('aqhi')))}</div>
    <div>
      <div class="lbl">Current AQHI at {aq.get('station_name', 'nearest station')} ({_v(aq.get('distance_km'), ' km from venue')})</div>
      <div class="lbl">Forecast {valid_label}: <b>{_v(cap_aqhi(fx.get('plus_3h')))}</b></div>
    </div>
  </div>
  <table class="msg">
    <tr><th>Health Risk</th><th>AQHI</th><th>At-Risk Population</th><th>General Population</th></tr>
    <tr class="active"><td>{RISK_LABEL.get(risk, risk)}</td><td>{_v(cap_aqhi(air.get('indicator')))}</td><td>{msgs['at_risk']}</td><td>{msgs['general']}</td></tr>
  </table>
</section>

{wx_section}

<section class="panel">
  <h2>Environmental Intelligence Summary</h2>
  <ul>{summary_items}</ul>
</section>

<section class="panel">
  <h2>Recommendations</h2>
  <ul>{rec_items}</ul>
</section>

<section class="panel">
  <h2>Hazard Snapshot — Overall Risk: {RISK_LABEL.get(a['overall_risk'], a['overall_risk'])}</h2>
  <div class="hazards">{hazard_rows}</div>
</section>

<section class="panel">
  <h2>Local Monitoring</h2>
  <div class="lc-row">{local_cards}</div>
</section>

<footer>
  <div class="foot-text">Prepared by Alberta Capital Airshed for the Edmonton Folk Music Festival. Beta decision-support product — for the interactive map, live cameras and hourly outlook, scan the QR code or visit {DASHBOARD_URL}</div>
  <img class="qr" src="{qr_b64}"/>
</footer>
</body></html>'''


def build_pdf(cfg, p, out_path, contact=None):
    contact = contact or (cfg.get('contact') or {'name': 'Gary Redmond, ACA Executive Director', 'phone': '780.935.4279'})
    html = render_html(cfg, p, contact)
    HTML(string=html, base_url=str(ROOT)).write_pdf(out_path)
    return out_path
