"""Offline preparation; no network calls or database writes."""
import argparse
import json
from bravura.postgres import prepare
p=argparse.ArgumentParser()
p.add_argument('operational')
p.add_argument('--manifest',required=True)
p.add_argument('--out',required=True)
a=p.parse_args()
print(json.dumps(prepare(a.operational,a.out,a.manifest),indent=2))
