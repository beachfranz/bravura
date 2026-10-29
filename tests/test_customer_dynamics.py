import copy
import json
import unittest
from pathlib import Path
from bravura.generator import simulate,SCENARIOS,customer_available
from bravura.release import validate,validate_config
from bravura.customer_audit import audit

class CustomerDynamics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=json.loads(Path('examples/apple/generation-config-v3.json').read_text())
        cls.t,_=simulate(cls.cfg,SCENARIOS)

    def test_combined_stories_and_bridges(self):
        self.assertTrue(all(audit(self.t)['checks'].values()),audit(self.t)['checks'])
        self.assertEqual(validate(self.t,self.cfg)['status'],'pass')

    def test_lifecycle_dates(self):
        from datetime import date
        for line in self.t['order_lines']:
            self.assertTrue(customer_available(self.cfg,int(line['customer_id'][1:]),date.fromisoformat(line['order_date']).replace(day=1)))
        cs={c['customer_id']:c for c in self.t['customers']}
        for row in self.t['account_activity']:
            self.assertGreaterEqual(row['activity_date'],cs[row['customer_id']]['acquisition_date'])

    def test_reject_invalid_terms(self):
        cfg=copy.deepcopy(self.cfg);cfg['customer_dynamics']['new_account_discount_bp']=9999
        with self.assertRaises(ValueError):validate_config(cfg)

    def test_reject_missing_story(self):
        t=copy.deepcopy(self.t)
        for r in t['order_lines']:
            if r['order_date']>='2026-01-01':r['contribution_cents']=r['net_sales_cents']
        self.assertFalse(audit(t)['checks']['growth_with_profit_decline'])
