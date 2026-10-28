import copy
import json
import tempfile
import unittest
from pathlib import Path
from bravura import contracts as c
from bravura.generator import allocate,rounded,simulate,line_metrics,SCENARIOS
from bravura.release import validate,validate_config,scenario_checks,ALLOWLIST,zip_directory,generate
from bravura.packet import approve

ROOT=Path(__file__).resolve().parents[1]

class Generator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=json.loads((ROOT/'examples/apple/generation-config.json').read_text())
        cls.cfg['order_lines']=10000
        cls.tables,cls.affected=simulate(cls.cfg,SCENARIOS)

    def test_money_rounding_and_conservation(self):
        self.assertEqual(rounded(5,2),3)
        self.assertEqual(allocate(101,[1,1,1]),[34,34,33])
        with self.assertRaises(ValueError):allocate(10,[0,1])

    def test_generated_structure_financial_temporal_integrity(self):
        result=validate(self.tables,self.cfg)
        self.assertEqual(result['status'],'pass')
        self.assertEqual(len(result['calendar_months']),30)
        self.assertEqual(len(self.tables['order_lines']),10000)

    def test_replay_identical_and_seed_changes_data(self):
        repeat,_=simulate(self.cfg,SCENARIOS)
        self.assertEqual(c.digest(repeat),c.digest(self.tables))
        other=copy.deepcopy(self.cfg);other['seed']+=1
        changed,_=simulate(other,SCENARIOS)
        self.assertNotEqual(c.digest(changed),c.digest(repeat))

    def test_baseline_does_not_expose_authoring_cost(self):
        self.assertNotIn('baseline_cost_cents',self.tables['products'][0])
        self.assertFalse(any('answer_key' in x or 'scenario' in x for x in ALLOWLIST))

    def test_cost_and_promotion_act_on_shared_records(self):
        self.assertTrue(set(self.affected['margin']) & set(self.affected['promotion']))

    def corrupt(self, table, field, value):
        t=copy.deepcopy(self.tables);t[table][0][field]=value
        with self.assertRaises(ValueError):validate(t,self.cfg)

    def test_incorrect_purchaser_account_rejected(self):
        self.corrupt('order_lines','purchaser_id',self.tables['purchasers'][-1]['purchaser_id'])

    def test_missing_cost_not_zero(self):
        self.corrupt('cost_history','unit_cost_cents',None)

    def test_double_charged_fulfillment_rejected(self):
        row=self.tables['order_lines'][0]
        self.corrupt('order_lines','allocated_fulfillment_cents',row['allocated_fulfillment_cents']*2)

    def test_excess_return_rejected(self):
        self.corrupt('returns','returned_quantity',100000)

    def test_post_cutoff_evidence_rejected(self):
        self.corrupt('account_activity','known_date','2027-01-01')

    def test_broken_hierarchy_rejected(self):
        self.corrupt('products','family_id','F3')

    def test_unknown_configuration_rejected(self):
        cfg=copy.deepcopy(self.cfg);cfg['start_date']='2025-01-01'
        with self.assertRaises(c.Invalid):validate_config(cfg)

    def test_changed_parameters_reject_approval(self):
        bundle=json.loads((ROOT/'examples/apple/generation-bundle.json').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            approval=approve(bundle,'Unit test','Test only',Path(tmp)/'approval.json')
            with self.assertRaisesRegex(c.Invalid,'parameters differ'):
                generate(self.cfg,approval,Path(tmp)/'release')

    def test_deterministic_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'data').mkdir();(root/'data'/'x.csv').write_text('x\n1\n')
            zip_directory(root/'data',root/'a.zip');zip_directory(root/'data',root/'b.zip')
            self.assertEqual((root/'a.zip').read_bytes(),(root/'b.zip').read_bytes())

if __name__=='__main__':unittest.main()
