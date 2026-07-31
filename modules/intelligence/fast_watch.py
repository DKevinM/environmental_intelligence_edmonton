"""Fast, cheap severe-weather checks meant to run every minute — separate
from the full run_demo.py pipeline (which is too slow for that cadence).
Pulls from Environment Canada's public GeoMet WMS: the same Canadian
Lightning Detection Network and radar composite data a meteorologist
would actually watch, not something inferred from hourly forecast codes.
"""
import io
import math

import requests
from PIL import Image

GEOMET_URL = 'https://geo.weather.gc.ca/geomet/?lang=en&SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap'


def _nearest_echo_km(lat, lon, layer, radius_km, px=64, timeout=15):
    """Distance in km from (lat,lon) to the nearest non-transparent pixel in
    a WMS raster layer, or None if nothing is present within radius_km."""
    d = radius_km / 111.0
    url = f'{GEOMET_URL}&LAYERS={layer}&FORMAT=image/png&TRANSPARENT=true&CRS=EPSG:4326&BBOX={lat-d},{lon-d},{lat+d},{lon+d}&WIDTH={px}&HEIGHT={px}'
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    im = Image.open(io.BytesIO(r.content)).convert('RGBA')
    pixels = im.load()
    cx = cy = px / 2
    km_per_px = (2 * radius_km) / px
    best = None
    for y in range(px):
        for x in range(px):
            if pixels[x, y][3] > 0:
                dist_km = math.hypot(x - cx, y - cy) * km_per_px
                if best is None or dist_km < best:
                    best = dist_km
    return best


def check_lightning(cfg, radius_km=40):
    e = cfg['event']
    try:
        km = _nearest_echo_km(float(e['latitude']), float(e['longitude']), 'Lightning_2.5km_Density', radius_km)
        return {'status': 'ok', 'nearest_km': round(km, 1) if km is not None else None, 'source': 'Environment Canada CLDN (10 min density grid)'}
    except Exception as ex:
        return {'status': 'error', 'error': f'{type(ex).__name__}: {ex}'}


def check_radar_echo(cfg, radius_km=40):
    e = cfg['event']
    try:
        km = _nearest_echo_km(float(e['latitude']), float(e['longitude']), 'RADAR_1KM_RRAI', radius_km)
        return {'status': 'ok', 'nearest_km': round(km, 1) if km is not None else None, 'source': 'Environment Canada composite radar'}
    except Exception as ex:
        return {'status': 'error', 'error': f'{type(ex).__name__}: {ex}'}
