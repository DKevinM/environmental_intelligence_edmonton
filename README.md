# Edmonton Folk Music Festival Environmental Intelligence — Working Demo v1

Runnable first release with live site-specific weather, hourly forecast, AQHI adapters, hazard assessment, narrative and standalone HTML dashboard.

## Install and run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_demo.py
xdg-open output/dashboard.html
```

`data_mode: auto` attempts live Open-Meteo weather and falls back to bundled samples. Add your current and forecast AQHI URLs or local files under `air_quality` in `config/config.yaml`.

Supported AQHI formats: GeoJSON, JSON and CSV. Common fields are detected automatically: AQHI/aqhi/value, latitude/lat, longitude/lon/lng, aqhi_1h, aqhi_2h and aqhi_3h.

## Test

```bash
python -m unittest discover -s tests -v
```

## Outputs

- `output/dashboard.html`
- `output/dashboard_data.json`
- `output/intelligence_summary.json`
- `output/run.log`

This release uses forecast signals for thunderstorm potential. Direct lightning-strike and radar-cell tracking are the next integration chunk.
