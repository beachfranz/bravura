"""Exercise frozen scenario bounds on held-out seeds; outputs evaluator-only JSON."""
import argparse
import copy
import json
from pathlib import Path
from bravura.generator import SCENARIOS,simulate,line_metrics
from bravura.release import validate,scenario_checks

parser=argparse.ArgumentParser()
parser.add_argument('config')
parser.add_argument('--out',required=True)
args=parser.parse_args()
config=json.loads(Path(args.config).read_text())
results={}
for seed in (20261029,20261030):
    cfg=copy.deepcopy(config);cfg['seed']=seed
    states={}
    for name,active in [('baseline',()),*[(s,(s,)) for s in SCENARIOS],('combined',SCENARIOS)]:
        tables,affected=simulate(cfg,active)
        states[name]=line_metrics(tables)
        if name=='combined':
            report=validate(tables,cfg)
    checks=scenario_checks(cfg,states,affected)
    if cfg.get('customer_dynamics'):
        from bravura.customer_audit import audit
        checks['checks'].update(audit(tables)['checks'])
    results[str(seed)]={'checks':checks['checks'],'combined_assertions':report['assertions'],
                        'interaction_residual':checks['interaction_residual']}
Path(args.out).write_text(json.dumps(results,indent=2,sort_keys=True)+'\n')
if not all(all(r['checks'].values()) for r in results.values()):
    raise SystemExit('One or more held-out seeds failed the frozen bounds')
print('Both held-out seeds pass combined-state and scenario checks.')
