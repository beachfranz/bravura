import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

from bravura import contracts as c
from bravura import packet, workflow

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    return json.loads((ROOT / "examples/fictional-bundle.json").read_text())


def sourced():
    data = fixture()
    # Deliberately invented source, used only to exercise evidence validation.
    data['research']['sources'] = [{'id': 'financial_source', 'title': 'Invented test source',
        'url': 'https://example.invalid/fixture', 'published_date': '2025-12-01',
        'accessed_date': '2026-01-01', 'snapshot_text': 'Fictional sales were 100 USD.'}]
    data['research']['claims'].append({'id': 'financial_sales', 'statement': 'Fictional sales were 100 USD.',
        'scope': 'Fictional test', 'status': 'reported', 'period_start': '2025-01-01',
        'period_end': '2025-11-30', 'value': '100', 'unit': 'money', 'currency': 'USD',
        'evidence': [{'source_id': 'financial_source', 'excerpt': 'sales were 100 USD', 'location': 'paragraph 1'}]})
    data['review']['claim_reviews'].append({'claim_id': 'financial_sales', 'disposition': 'accepted',
                                           'reason': 'Test source only.'})
    return data


class Contracts(unittest.TestCase):
    def test_valid_fixture_and_sourced_contract(self):
        c.bundle(fixture())
        c.bundle(sourced())

    def test_missing_audience_and_invalid_period(self):
        for field, value in [('audience', ''), ('start_date', '2027-01-01'), ('order_lines', True)]:
            data = fixture()
            data['brief'][field] = value
            with self.subTest(field=field), self.assertRaises(c.Invalid):
                c.bundle(data)

    def test_reported_claim_requires_evidence(self):
        data = sourced()
        data['research']['claims'][1]['evidence'] = []
        with self.assertRaisesRegex(c.Invalid, 'needs source'):
            c.bundle(data)

    def test_excerpt_must_exist(self):
        data = sourced()
        data['research']['claims'][1]['evidence'][0]['excerpt'] = 'Fabricated quotation'
        with self.assertRaisesRegex(c.Invalid, 'excerpt not in'):
            c.bundle(data)

    def test_post_cutoff_source(self):
        data = sourced()
        data['research']['sources'][0]['published_date'] = '2026-01-01'
        with self.assertRaisesRegex(c.Invalid, 'after cutoff'):
            c.bundle(data)

    def test_money_requires_currency(self):
        data = sourced()
        del data['research']['claims'][1]['currency']
        with self.assertRaisesRegex(c.Invalid, 'currency'):
            c.bundle(data)

    def test_inference_cycle(self):
        data = sourced()
        for key, parent in [('infer_a', 'infer_b'), ('infer_b', 'infer_a')]:
            item = copy.deepcopy(data['research']['claims'][1])
            item.update(id=key, status='inferred', input_claim_ids=[parent], method='Test inference')
            data['research']['claims'].append(item)
        with self.assertRaisesRegex(c.Invalid, 'circular'):
            c.bundle(data)

    def test_malformed_claim_status(self):
        data = sourced()
        data['research']['claims'][1]['status'] = {}
        with self.assertRaises(c.Invalid):
            c.bundle(data)

    def test_ancestor_missing_parent(self):
        data = fixture()
        levels = data['blueprint']['dimensions'][0]['hierarchy']
        levels[0]['parent'] = 'family'
        levels[1]['parent'] = 'missing'
        with self.assertRaises(c.Invalid):
            c.bundle(data)

    def test_duplicate_dimension(self):
        data = fixture()
        data['blueprint']['dimensions'].append(data['blueprint']['dimensions'][0])
        with self.assertRaisesRegex(c.Invalid, 'duplicate'):
            c.bundle(data)

    def test_hierarchy_cycle_and_missing_parent(self):
        for parent in ['sku', 'missing']:
            data = fixture()
            data['blueprint']['dimensions'][0]['hierarchy'][0]['parent'] = parent
            with self.subTest(parent=parent), self.assertRaises(c.Invalid):
                c.bundle(data)

    def test_multiple_purchasers_required(self):
        data = fixture()
        data['blueprint']['relationships'][0]['cardinality'] = 'one_to_one'
        with self.assertRaisesRegex(c.Invalid, 'many-to-one'):
            c.bundle(data)

    def test_many_to_many_requires_bridge(self):
        data = fixture()
        rel = copy.deepcopy(data['blueprint']['relationships'][0])
        rel.update(id='extra', cardinality='many_to_many')
        data['blueprint']['relationships'].append(rel)
        with self.assertRaisesRegex(c.Invalid, 'bridge'):
            c.bundle(data)

    def test_order_lines_require_account_and_purchaser(self):
        data = fixture()
        del data['blueprint']['facts'][0]['dimension_keys']['purchaser']
        with self.assertRaisesRegex(c.Invalid, 'core dimension'):
            c.bundle(data)

    def test_synthetic_story_label(self):
        data = fixture()
        data['blueprint']['stories'][0]['status'] = 'reported'
        with self.assertRaisesRegex(c.Invalid, 'simulated'):
            c.bundle(data)

    def test_unknown_cannot_be_accepted(self):
        data = fixture()
        data['review']['claim_reviews'][0]['disposition'] = 'accepted'
        with self.assertRaisesRegex(c.Invalid, 'unknown or conflicting'):
            c.bundle(data)

    def test_unreviewed_claim(self):
        data = fixture()
        data['review']['claim_reviews'] = []
        with self.assertRaisesRegex(c.Invalid, 'every claim'):
            c.bundle(data)

    def test_blueprint_cannot_use_rejected_evidence(self):
        data = sourced()
        data['review']['claim_reviews'][1]['disposition'] = 'revise'
        data['blueprint']['stories'][0]['claim_ids'] = ['financial_sales']
        with self.assertRaisesRegex(c.Invalid, 'unaccepted'):
            c.bundle(data)


class Execution(unittest.TestCase):
    def test_replay_repeatable_and_not_approved(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp)/'a', Path(tmp)/'b'
            for dest in [a, b]:
                result = workflow.run(fixture()['brief'], workflow.Replay(ROOT/'examples/replay'), dest)
                self.assertEqual(result, fixture())
                self.assertEqual(json.loads((dest/'manifest.json').read_text())['status'], 'awaiting_user_review')
                trace = json.loads((dest/'run.json').read_text())
                self.assertEqual(len(trace['calls']), 5)
                self.assertEqual(trace['mode'], 'replay')
            for name in ['bundle.json', 'review.html', 'manifest.json', 'run.json']:
                self.assertEqual((a/name).read_bytes(), (b/name).read_bytes())

    def test_failed_run_not_published(self):
        class Bad:
            mode = 'test'
            def run(self, task):
                return {'sources': [], 'claims': [{'id': 'wrong_prefix'}]}
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)/'run'
            with self.assertRaises(c.Invalid):
                workflow.run(fixture()['brief'], Bad(), dest)
            self.assertFalse((dest/'bundle.json').exists())
            self.assertEqual(json.loads((dest/'run.json').read_text())['status'], 'failed')

    def test_command_adapter_json_round_trip(self):
        backend = workflow.Command([sys.executable, '-c', 'import json,sys; x=json.load(sys.stdin); print(json.dumps({"role":x["role"]}))'])
        self.assertEqual(backend.run(workflow.request('structure', fixture()['brief'], {})), {'role': 'structure'})

    def test_command_failure_hides_stderr(self):
        backend = workflow.Command([sys.executable, '-c', 'import sys; print("secret",file=sys.stderr); sys.exit(1)'])
        with self.assertRaises(c.Invalid) as caught:
            backend.run(workflow.request('structure', fixture()['brief'], {}))
        self.assertNotIn('secret', str(caught.exception))

    def test_timeout(self):
        backend = workflow.Command([sys.executable, '-c', 'import time; time.sleep(3)'])
        task = workflow.request('structure', fixture()['brief'], {})
        task['budget']['timeout_seconds'] = 1
        with self.assertRaisesRegex(c.Invalid, 'timed out'):
            backend.run(task)

    def test_packet_escapes_untrusted_text(self):
        data = fixture()
        data['brief']['target'] = '<script>alert(1)</script>'
        rendered = packet.render(data)
        self.assertNotIn('<script>', rendered)
        self.assertIn('&lt;script&gt;', rendered)

    def test_approval_invalidated_by_edit_and_no_overwrite(self):
        data = fixture()
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)/'approval.json'
            record = packet.approve(data, 'Test Reviewer', 'Fixture-only approval for a unit test.', dest)
            packet.verify_approval(record, data)
            with self.assertRaises(FileExistsError):
                packet.approve(data, 'Test Reviewer', 'Repeated approval', dest)
            data['brief']['order_lines'] += 1
            with self.assertRaisesRegex(c.Invalid, 'does not match'):
                packet.verify_approval(record, data)

    def test_blockers_prevent_approval(self):
        data = fixture()
        data['review']['blockers'] = ['Missing source verification']
        with tempfile.TemporaryDirectory() as tmp, self.assertRaisesRegex(c.Invalid, 'blockers'):
            packet.approve(data, 'Test Reviewer', 'Test', Path(tmp)/'approval.json')


if __name__ == '__main__':
    unittest.main()
