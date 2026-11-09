"""Download immutable source snapshots; do not mix source money with GBP simulation."""
import hashlib, json, urllib.request
from pathlib import Path
import pandas as pd

BASE = 'https://database-sample-website.s3.eu-north-1.amazonaws.com/datasets/subscription-billing/v3/csv/'
PUBLISHED_HASHES = dict(zip(['customers','plans','subscriptions','invoices','payments'],[
    'cf4f65611763fee7ed70b64f5be0d65744789ccdf335959d2ae9319d5dfb839f',
    'a66e5e2dd78553b612b4158c54b3ee1b09f1f2a46b62842ab81258e068ec4e15',
    'f59217be33ad55bf163c7c08fe2562c7cc275078e9625c9c7dc2a9ba95a7c936',
    '9e8acd48c3f187d66c3af14533d8b5a1a6f06a010daf0a6f4152a57b117a31dc',
    '8cfb127ae808bd798e0b917c3b985c0eed6374f072ec327de4ba8e281de1af0a']))
def run(root):
    tables, manifest = {}, []
    for name in ['customers','plans','subscriptions','invoices','payments']:
        path = root/'data/source'/f'{name}.csv'
        url = BASE+path.name
        if not path.exists():
            with urllib.request.urlopen(url, timeout=40) as r: path.write_bytes(r.read())
        d = pd.read_csv(path); tables[name] = d
        assert hashlib.sha256(path.read_bytes()).hexdigest()==PUBLISHED_HASHES[name], f'Source checksum changed: {name}; review before use'
        dates = {c: {'min':str(d[c].dropna().min()),'max':str(d[c].dropna().max())} for c in d if 'date' in c or c.endswith('_at')}
        manifest.append(dict(table=name,url=url,access_date='2026-11-08',sha256=hashlib.sha256(path.read_bytes()).hexdigest(),rows=len(d),schema={c:str(t) for c,t in d.dtypes.items()},dates=dates,sample=d.head(3).fillna('').to_dict('records')))
    (root/'data/source/manifest.json').write_text(json.dumps(manifest,indent=2))
    return tables

