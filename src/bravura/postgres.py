"""Prepare, but never execute, a transactional PostgreSQL import of operational CSVs."""
import csv
import hashlib
import json
import re
import shutil
from datetime import date
from pathlib import Path
from .release import ALLOWLIST, KEYS

SCHEMA='bravura_demo'
DATE_COLUMNS={'date_id','available_from','available_to','acquisition_date','valid_from','valid_to',
              'effective_start','effective_end','start_date','end_date','month_start'}
INTEGER_COLUMNS={'calendar_year','calendar_quarter','calendar_month','day_of_week','configuration_band',
                 'quantity','returned_quantity','discount_bp','program_cost_bp'}
FK={
 'product_families': [('category_id','product_categories')],
 'product_versions': [('family_id','product_families')],
 'territories': [('region_id','regions')],
 'customers': [('parent_id','customer_parents'),('territory_id','territories'),('sales_rep_id','sales_organization'),('channel_id','channels')],
 'purchasers': [('customer_id','customers')],
 'customer_locations': [('customer_id','customers')],
 'products': [('category_id','product_categories'),('family_id','product_families'),('version_id','product_versions'),('supplier_id','suppliers')],
 'cost_history': [('product_id','products'),('supplier_id','suppliers')],
 'orders': [('customer_id','customers'),('purchaser_id','purchasers'),('sales_rep_id','sales_organization'),
            ('bill_to_location_id','customer_locations'),('ship_to_location_id','customer_locations')],
 'order_lines': [('order_id','orders'),('customer_id','customers'),('purchaser_id','purchasers'),('product_id','products'),
                ('territory_id','territories'),('channel_id','channels'),('promotion_id','promotions'),('cost_version_id','cost_history')],
 'shipments': [('order_id','orders'),('location_id','fulfillment_locations')],
 'shipment_allocations': [('shipment_id','shipments'),('order_line_id','order_lines')],
 'returns': [('order_line_id','order_lines')],
 'account_activity': [('customer_id','customers'),('purchaser_id','purchasers')],
 'account_plans': [('customer_id','customers')],
}


def ident(name):
    if not re.fullmatch('[a-z][a-z0-9_]*',name):raise ValueError('Unsafe SQL identifier')
    return '"'+name+'"'


def sql_type(column):
    if column in DATE_COLUMNS or column.endswith('_date'):return 'date'
    if column.endswith('_cents') or column in INTEGER_COLUMNS:return 'bigint'
    if column=='resolved':return 'boolean'
    return 'text'


def prepare(operational, destination, checksum_manifest):
    """Require exact release checksums; accept no private files in the source directory."""
    source=Path(operational);out=Path(destination)
    actual={p.name for p in source.iterdir()}
    if actual!=ALLOWLIST:raise ValueError('Source is not an exact operational export')
    hashes=json.loads(Path(checksum_manifest).read_text())['operational_checksums']
    if set(hashes)!=actual:raise ValueError('Manifest does not match operational allowlist')
    for name in actual:
        if hashlib.sha256((source/name).read_bytes()).hexdigest()!=hashes[name]:raise ValueError('Checksum mismatch: '+name)
    fields={};counts={}
    for name in sorted(actual):
        if not name.endswith('.csv'):continue
        table=name[:-4];ident(table)
        with (source/name).open(newline='') as f:
            reader=csv.DictReader(f);columns=reader.fieldnames
            if not columns or len(columns)!=len(set(columns)):raise ValueError('Invalid header')
            for column in columns:ident(column)
            fields[table]=columns;counts[table]=0
            for row in reader:
                if None in row or any(v is None or v=='' for v in row.values()):raise ValueError('Malformed or empty required CSV field')
                for column,value in row.items():
                    kind=sql_type(column)
                    if kind=='bigint':
                        n=int(value)
                        if not -(2**63)<=n<2**63:raise ValueError('Integer outside bigint range')
                    elif kind=='date':date.fromisoformat(value)
                    elif kind=='boolean' and value not in ('true','false'):raise ValueError('Invalid boolean')
                counts[table]+=1
    out.mkdir(parents=True,exist_ok=False)
    ddl=['-- Prepared only; inspect the destination project before applying.',
         '-- No existing objects are dropped. An existing schema causes a safe failure.',
         'CREATE SCHEMA '+SCHEMA+';', 'REVOKE ALL ON SCHEMA '+SCHEMA+' FROM PUBLIC;',
         'REVOKE ALL ON SCHEMA '+SCHEMA+' FROM anon, authenticated;']
    for table,columns in fields.items():
        pk=KEYS.get(table)
        primary=[pk] if pk else ['shipment_id','order_line_id']
        definitions=[f'  {ident(column)} {sql_type(column)} NOT NULL' for column in columns]
        definitions.append('  PRIMARY KEY ('+', '.join(map(ident,primary))+')')
        if table=='purchasers':definitions.append('  UNIQUE (purchaser_id, customer_id)')
        if table=='orders':definitions.append('  UNIQUE (order_id, customer_id, purchaser_id, order_date)')
        if table=='returns':definitions.append('  UNIQUE (order_line_id)')
        if table=='shipments':definitions.append('  UNIQUE (order_id)')
        if table=='order_lines':
            definitions+=['  CHECK (quantity > 0)','  CHECK (discount_bp BETWEEN 0 AND 10000)',
                '  CHECK (net_sales_cents = quantity * net_unit_price_cents)',
                '  CHECK (gross_profit_cents = net_sales_cents - product_cost_cents)',
                '  CHECK (contribution_cents = gross_profit_cents - program_cost_cents - allocated_fulfillment_cents)']
        if table=='cost_history':definitions+=['  CHECK (unit_cost_cents > 0)','  CHECK (effective_start <= effective_end)']
        if table=='returns':definitions+=['  CHECK (returned_quantity > 0)',
            '  CHECK (net_return_cost_cents = refund_cents + restocking_cents - recoverable_value_cents)']
        if table=='shipments':definitions.append('  CHECK (total_fulfillment_cents = freight_cents + expedite_cents + handling_cents)')
        ddl+=[f'CREATE TABLE {SCHEMA}.{ident(table)} (\n'+',\n'.join(definitions)+'\n);',
              f'ALTER TABLE {SCHEMA}.{ident(table)} ENABLE ROW LEVEL SECURITY;',
              f'REVOKE ALL ON {SCHEMA}.{ident(table)} FROM PUBLIC, anon, authenticated;']
    for table,links in FK.items():
        for column,parent in links:
            ddl.append(f'ALTER TABLE {SCHEMA}.{ident(table)} ADD FOREIGN KEY ({ident(column)}) REFERENCES {SCHEMA}.{ident(parent)} ({ident(KEYS[parent])}) DEFERRABLE INITIALLY DEFERRED;')
    for table in ('orders','order_lines','account_activity'):
        ddl.append(f'ALTER TABLE {SCHEMA}.{ident(table)} ADD FOREIGN KEY (purchaser_id, customer_id) REFERENCES {SCHEMA}.purchasers (purchaser_id, customer_id) DEFERRABLE INITIALLY DEFERRED;')
    ddl.append(f'ALTER TABLE {SCHEMA}.order_lines ADD FOREIGN KEY (order_id, customer_id, purchaser_id, order_date) REFERENCES {SCHEMA}.orders (order_id, customer_id, purchaser_id, order_date) DEFERRABLE INITIALLY DEFERRED;')
    for table,column in [('order_lines','order_date'),('order_lines','customer_id'),('order_lines','product_id'),('order_lines','territory_id'),('orders','customer_id'),('returns','order_line_id'),('cost_history','product_id')]:
        ddl.append(f'CREATE INDEX ON {SCHEMA}.{ident(table)} ({ident(column)});')
    (out/'schema.sql').write_text('\n'.join(ddl)+'\n')
    commands=['\\set ON_ERROR_STOP on','BEGIN;','\\ir schema.sql']
    for table,columns in fields.items():
        shutil.copyfile(source/(table+'.csv'),out/(table+'.csv'))
        commands.append(f"\\copy {SCHEMA}.{ident(table)} ({', '.join(map(ident,columns))}) FROM '{table}.csv' WITH (FORMAT csv, HEADER true)")
    commands+=['SET CONSTRAINTS ALL IMMEDIATE;']
    for table,count in counts.items():
        commands.append(f"DO $check$ BEGIN IF (SELECT count(*) FROM {SCHEMA}.{ident(table)}) <> {count} THEN RAISE EXCEPTION 'Row count mismatch: {table}'; END IF; END $check$;")
    commands+=['COMMIT;']
    (out/'import.psql').write_text('\n'.join(commands)+'\n')
    report={'status':'prepared_not_applied','schema':SCHEMA,'row_counts':counts,
            'project_url':'https://udczuujwgyqgibfkuszg.supabase.co',
            'source_checksums_verified':True,'database_execution':'not_run',
            'access':'No grants/policies for anon or authenticated; owner/service roles can bypass RLS.',
            'answer_key_included':False}
    (out/'import_manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    return report
