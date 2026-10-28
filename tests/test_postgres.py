import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from bravura.generator import simulate,write_tables,SCENARIOS
from bravura.postgres import prepare,sql_type,ident

ROOT=Path(__file__).resolve().parents[1]

class PostgresPreparation(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.source=self.root/'operational'
        cfg=json.loads((ROOT/'examples/apple/generation-config.json').read_text());cfg['order_lines']=10000
        data,_=simulate(cfg,SCENARIOS);write_tables(data,self.source)
        (self.source/'README.txt').write_text('Synthetic test')
        (self.source/'data_dictionary.json').write_text('{}')
        self.manifest=self.root/'manifest.json';self.sign()

    def sign(self):
        self.manifest.write_text(json.dumps({'operational_checksums':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in self.source.iterdir()}}))

    def test_prepares_typed_restricted_transactional_import(self):
        out=self.root/'import'
        r=prepare(self.source,out,self.manifest)
        self.assertEqual(r['row_counts']['order_lines'],10000)
        ddl=(out/'schema.sql').read_text();script=(out/'import.psql').read_text()
        self.assertIn('"net_sales_cents" bigint NOT NULL',ddl)
        self.assertIn('"order_date" date NOT NULL',ddl)
        self.assertEqual(ddl.count('ENABLE ROW LEVEL SECURITY'),24)
        self.assertIn('FOREIGN KEY (purchaser_id, customer_id)',ddl)
        self.assertNotIn('DROP ',ddl)
        self.assertNotIn('GRANT ',ddl)
        self.assertIn('BEGIN;',script);self.assertTrue(script.endswith('COMMIT;\n'))
        self.assertEqual(script.count('\\copy '),24)
        self.assertNotIn('answer_key',script)
        self.assertEqual(r['database_execution'],'not_run')

    def test_tampering_rejected_before_preparation(self):
        with (self.source/'order_lines.csv').open('a') as f:f.write('bad\n')
        with self.assertRaisesRegex(ValueError,'Checksum mismatch'):
            prepare(self.source,self.root/'import',self.manifest)
        self.assertFalse((self.root/'import').exists())

    def test_private_files_rejected(self):
        (self.source/'answer_key.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'exact operational'):
            prepare(self.source,self.root/'import',self.manifest)

    def test_no_overwrite(self):
        out=self.root/'import';out.mkdir();(out/'keep').write_text('existing')
        with self.assertRaises(FileExistsError):prepare(self.source,out,self.manifest)
        self.assertEqual((out/'keep').read_text(),'existing')

    def test_identifier_and_types(self):
        with self.assertRaises(ValueError):ident('x;drop table y')
        self.assertEqual(sql_type('resolved'),'boolean')
        self.assertEqual(sql_type('valid_from'),'date')
        self.assertEqual(sql_type('product_id'),'text')

if __name__=='__main__':unittest.main()
