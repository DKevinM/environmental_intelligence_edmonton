from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parents[1]
def load_config(path='config/config.yaml'):
    p=Path(path); p=p if p.is_absolute() else ROOT/p
    cfg=yaml.safe_load(p.read_text()) or {}; cfg['_root']=str(ROOT); return cfg
def resolve_path(cfg,value):
    p=Path(value); return p if p.is_absolute() else Path(cfg['_root'])/p
