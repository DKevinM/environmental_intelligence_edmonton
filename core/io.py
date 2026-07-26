from pathlib import Path
import csv,io,json,requests
def read_structured_source(source,timeout=20):
    if source.startswith(('http://','https://')):
        r=requests.get(source,timeout=timeout,headers={'User-Agent':'EventEnvironmentalIntelligence/1.0'}); r.raise_for_status(); text=r.text
    else:text=Path(source).read_text(encoding='utf-8')
    return list(csv.DictReader(io.StringIO(text))) if source.lower().split('?')[0].endswith('.csv') else json.loads(text)
def write_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(data,indent=2,default=str),encoding='utf-8')
