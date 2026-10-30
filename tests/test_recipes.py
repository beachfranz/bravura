import copy
import json
import unittest
from pathlib import Path
from bravura.recipes import QualityFeedback, quality_audit, recipe_catalog
from bravura.generator import simulate, SCENARIOS
from bravura.release import validate, validate_config

class Recipes(unittest.TestCase):
    def setUp(self):
        self.cfg=json.loads(Path('examples/apple/generation-config-v4.json').read_text())

    def test_portable_feedback_and_lag(self):
        q=copy.deepcopy(self.cfg['quality']);q.update(product_ids=['WIDGET-X'],start_date='2030-01-01',end_date='2030-03-01',response_share_bp=10000)
        f=QualityFeedback(q,42)
        line=dict(product_id='WIDGET-X',customer_id='hospital-alpha',purchaser_id='buyer-z',order_date='2030-01-01',order_line_id='sale-1')
        self.assertTrue(f.applies(line));f.record(line,dict(return_date='2030-01-10'))
        self.assertEqual(f.quantity('hospital-alpha','2030-02-23',100),100)
        self.assertEqual(f.quantity('hospital-alpha','2030-02-24',100),85)
        self.assertEqual(f.quantity('unexposed','2030-05-01',100),100)
        q['response_share_bp']=0
        self.assertEqual(f.quantity('hospital-alpha','2030-05-01',100),100)

    def test_combined_quality(self):
        t,_=simulate(self.cfg,SCENARIOS)
        self.assertEqual(validate(t,self.cfg)['status'],'pass')
        self.assertTrue(all(quality_audit(t,self.cfg['quality'])['checks'].values()))
        t['returns']=[]
        self.assertFalse(quality_audit(t,self.cfg['quality'])['checks']['quality_return_evidence'])

    def test_invalid_recipe(self):
        self.cfg['quality']['lag_days']=-1
        with self.assertRaises(ValueError):validate_config(self.cfg)

    def test_catalog(self):
        self.assertEqual(len(recipe_catalog()['recipes']),5)
