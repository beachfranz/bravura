"""Release gates and allowlisted packaging. No blind-isolation claim is made."""
import csv
import hashlib
import html
import json
import platform
import time
import zipfile
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from . import contracts as c
from .generator import (VERSION, SCENARIOS, simulate, line_metrics, totals, METRICS,
                        allocate, rounded, write_tables, file_hashes)
from .packet import verify_approval

KEYS = dict(product_categories='category_id',product_families='family_id',product_versions='version_id',regions='region_id',territories='territory_id',channels='channel_id',
    sales_organization='sales_rep_id',fulfillment_locations='location_id',suppliers='supplier_id',
    customer_parents='parent_id',customers='customer_id',purchasers='purchaser_id',
    customer_locations='customer_location_id',products='product_id',calendar='date_id',
    cost_history='cost_version_id',promotions='promotion_id',orders='order_id',order_lines='order_line_id',
    shipments='shipment_id',returns='return_id',account_activity='activity_id',account_plans='plan_id')
ALLOWLIST = {name+'.csv' for name in [*KEYS,'shipment_allocations']} | {'data_dictionary.json','README.txt'}


def validate_config(cfg):
    c.require(cfg.get('schema_version')==1,'unsupported generation schema')
    c.require(cfg.get('start_date')=='2024-01-01' and cfg.get('end_date')=='2026-06-30',
              'v0.2 Apple generator supports January 2024–June 2026 only')
    c.require(cfg.get('cutoff')=='2026-10-28','v0.2 cutoff must be October 28, 2026')
    c.integer(cfg.get('seed'),'seed',0,2**32-1)
    c.integer(cfg.get('order_lines'),'order_lines',10000,1000000)
    c.require(cfg['order_lines']%2==0,'two-line orders require an even line count')
    c.require(cfg.get('accounts')==300,'v0.2 requires 300 accounts')
    c.require(len(cfg['seasonality'])==12 and all(type(x) is int and x>0 for x in cfg['seasonality']), 'invalid seasonality')
    c.require(set(cfg['accounts_scenario']['accounts'])=={'C0003','C0007'} and cfg['accounts_scenario']['service_account']=='C0003', 'unsupported account cohort')
    if cfg.get('customer_dynamics'):
        d=cfg['customer_dynamics']
        for key in ('large_account_scale_bp','anchor_growth_bp','new_account_discount_bp'):
            c.integer(d.get(key),key,0,1000000)
        c.require(d['large_account_scale_bp']>=10000 and d['new_account_discount_bp']<=5000,'invalid customer economics')
    from .recipes import validate_quality
    validate_quality(cfg.get('quality'))
    for p in cfg['catalog']:
        c.require(p['family'] in ('iPhone','MacBook Air','iPad Air'),'unsupported family')
        c.day(p['available_from'],'availability')
        c.integer(p['price_cents'],'price',100,10000000)
        c.text(p['source_url'],'catalog source')
    if cfg.get('quality'):
        from .generator import dimensions
        products={p['product_id']:p for p in dimensions(cfg)['products']}
        q=cfg['quality']
        c.require(all(k in products and products[k]['available_from']<=q['start_date'] for k in q['product_ids']), 'quality product unavailable')
        c.require(cfg['start_date']<=q['start_date']<=q['end_date']<=cfg['end_date'], 'quality outside transaction history')
        c.require(q['lag_days']>=32, 'monthly adapter requires at least 32-day feedback lag')
    for family in ('iPhone','MacBook Air','iPad Air'):
        c.require(any(p['family']==family and p['available_from']<=cfg['start_date'] for p in cfg['catalog']), 'family unavailable at start')
    for x in (cfg['margin']['cost_uplift_bp'],cfg['margin']['premium_mix_bp'],cfg['accounts_scenario']['retention_bp'],cfg['promotion']['unit_uplift_bp']):
        c.integer(x,'scenario basis points',0,10000)
    for channel in ('direct','reseller'):
        for x in cfg['promotion'][channel].values(): c.integer(x,'promotion basis points',0,10000)
    for bounds in cfg['bounds'].values():
        c.require(isinstance(bounds,list) and len(bounds)==2 and all(type(x) in (int,float) for x in bounds) and bounds[0]<=bounds[1], 'invalid bounds')


def validate(t, cfg):
    """Fail closed on inconsistent operational data; returns explicit checks."""
    checks=[]
    def ok(condition, label):
        if not condition: raise ValueError('Validation failed: '+label)
        checks.append(label)
    ix={}
    for name,key in KEYS.items():
        rows=t[name];ix[name]={r[key]:r for r in rows}
        ok(len(rows)==len(ix[name]), name+': unique keys')
        ok(all(all(v is not None for v in r.values()) for r in rows),name+': no unknown required values')
    ok(len(t['order_lines'])==cfg['order_lines'],'requested line count')
    counts=Counter(p['customer_id'] for p in t['purchasers'])
    ok(all(2<=counts[k]<=5 for k in ix['customers']),'multiple purchasers per customer')
    for table,field,target in [
        ('product_families','category_id','product_categories'),('product_versions','family_id','product_families'),
        ('products','category_id','product_categories'),('products','family_id','product_families'),('products','version_id','product_versions'),
        ('territories','region_id','regions'),('customers','parent_id','customer_parents'),
        ('customers','territory_id','territories'),('customers','sales_rep_id','sales_organization'),
        ('customers','channel_id','channels'),('purchasers','customer_id','customers'),
        ('customer_locations','customer_id','customers'),('products','supplier_id','suppliers'),
        ('cost_history','product_id','products'),('cost_history','supplier_id','suppliers'),
        ('orders','customer_id','customers'),('orders','purchaser_id','purchasers'),
        ('orders','bill_to_location_id','customer_locations'),('orders','ship_to_location_id','customer_locations'),
        ('orders','sales_rep_id','sales_organization'),('order_lines','order_id','orders'),
        ('order_lines','product_id','products'),('order_lines','customer_id','customers'),
        ('order_lines','purchaser_id','purchasers'),('order_lines','territory_id','territories'),
        ('order_lines','channel_id','channels'),('order_lines','promotion_id','promotions'),
        ('order_lines','cost_version_id','cost_history'),('shipments','order_id','orders'),
        ('shipments','location_id','fulfillment_locations'),('returns','order_line_id','order_lines'),
        ('account_activity','customer_id','customers'),('account_activity','purchaser_id','purchasers'),
        ('account_plans','customer_id','customers')]:
        ok(all(r[field] in ix[target] for r in t[table]),f'{table}.{field}: valid references')
    for p in t['products']:
        v=ix['product_versions'][p['version_id']];f=ix['product_families'][p['family_id']]
        ok(v['family_id']==p['family_id'] and f['category_id']==p['category_id'],'product hierarchy consistency')
    for customer in t['customers']:
        ok(ix['territories'][customer['territory_id']]['country_code']==customer['country_code'],'customer territory consistency')
    for order in t['orders']:
        ok(all(ix['customer_locations'][order[k]]['customer_id']==order['customer_id'] for k in ('bill_to_location_id','ship_to_location_id')),'bill-to and ship-to ownership')
    group=defaultdict(list)
    for cost in t['cost_history']:
        ok(type(cost['unit_cost_cents']) is int and cost['unit_cost_cents']>0,'positive known cost '+cost['cost_version_id'])
        group[(cost['product_id'],cost['country_code'])].append(cost)
    for pair,rows in group.items():
        rows.sort(key=lambda x:x['effective_start'])
        ok(all(a['effective_end']<b['effective_start'] for a,b in zip(rows,rows[1:])),f'nonoverlapping costs {pair}')
    allocations=defaultdict(int);line_allocations=defaultdict(int);seen=set()
    for a in t['shipment_allocations']:
        key=(a['shipment_id'],a['order_line_id'])
        ok(key not in seen and a['shipment_id'] in ix['shipments'] and a['order_line_id'] in ix['order_lines'],'allocation unique valid pair')
        seen.add(key)
        ok(ix['shipments'][a['shipment_id']]['order_id']==ix['order_lines'][a['order_line_id']]['order_id'],'allocation same order')
        allocations[a['shipment_id']]+=a['allocated_cost_cents'];line_allocations[a['order_line_id']]+=a['allocated_cost_cents']
    ship_by_order={s['order_id']:s for s in t['shipments']}
    ok(len(ship_by_order)==len(t['orders']),'one shipment per order')
    for s in t['shipments']:
        ok(s['total_fulfillment_cents']==s['freight_cents']+s['expedite_cents']+s['handling_cents']==allocations[s['shipment_id']],'shipment conservation')
        ok(ix['orders'][s['order_id']]['order_date']<=s['ship_date']<=s['actual_delivery_date']<=cfg['cutoff'],'shipment dates')
        ok(s['ship_date']<=s['promised_date']<=cfg['cutoff'],'promise dates')
    monthly=Counter();order_counts=Counter()
    for l in t['order_lines']:
        prod=ix['products'][l['product_id']];customer=ix['customers'][l['customer_id']];buyer=ix['purchasers'][l['purchaser_id']]
        cost=ix['cost_history'][l['cost_version_id']];order=ix['orders'][l['order_id']]
        ok(all(type(v) is int for k,v in l.items() if k.endswith('_cents') or k in ('quantity','discount_bp')),'integer economics')
        ok(l['quantity']>0 and 0<=l['discount_bp']<=10000,'quantity and discount bounds')
        ok(customer['acquisition_date']<=l['order_date'] and buyer['customer_id']==l['customer_id'] and buyer['valid_from']<=l['order_date']<=buyer['valid_to'],'purchaser ownership and time')
        ok(l['order_date']==order['order_date'] and l['customer_id']==order['customer_id'] and l['purchaser_id']==order['purchaser_id'],'header line coherence')
        ok(l['territory_id']==customer['territory_id'] and l['channel_id']==customer['channel_id'],'commercial dimension coherence')
        ok(cfg['start_date']<=l['order_date']<=cfg['end_date'] and l['order_date'] in ix['calendar'],'order coverage')
        ok(prod['available_from']<=l['order_date']<=prod['available_to'],'product availability')
        ok(cost['product_id']==l['product_id'] and cost['country_code']==customer['country_code'] and cost['effective_start']<=l['order_date']<=cost['effective_end'],'effective cost resolution')
        ok(l['net_unit_price_cents']==rounded(l['list_unit_price_cents']*(10000-l['discount_bp'])),'price identity')
        ok(l['net_sales_cents']==l['quantity']*l['net_unit_price_cents'],'sales identity')
        ok(l['product_cost_cents']==l['quantity']*cost['unit_cost_cents'],'cost identity')
        ok(l['gross_profit_cents']==l['net_sales_cents']-l['product_cost_cents'],'gross identity')
        ok(l['allocated_fulfillment_cents']==line_allocations[l['order_line_id']],'line allocation identity')
        ok(l['contribution_cents']==l['gross_profit_cents']-l['program_cost_cents']-l['allocated_fulfillment_cents'],'contribution identity')
        if l['promotion_id']!='NONE':
            p=ix['promotions'][l['promotion_id']]
            ok(p['start_date']<=l['order_date']<=p['end_date'] and prod['family']==p['eligible_family'] and customer['country_code'] in p['eligible_markets'].split('|') and customer['account_tier']==p['eligible_account_tier'] and l['channel_id']==p['eligible_channel'],'promotion eligibility')
            ok(l['discount_bp']==p['discount_bp'] and l['program_cost_cents']==rounded(l['net_sales_cents']*p['program_cost_bp']),'promotion economics')
        else: ok(l['program_cost_cents']==0,'no unlinked program cost')
        monthly[l['order_date'][:7]]+=1;order_counts[l['order_id']]+=1
    ok(len(monthly)==30 and min(monthly.values())>0,'30 populated months')
    ok(set(order_counts.values())=={2},'declared two-line order grain')
    returned=Counter()
    for r in t['returns']:
        l=ix['order_lines'][r['order_line_id']];cost=ix['cost_history'][l['cost_version_id']]
        returned[l['order_line_id']]+=r['returned_quantity']
        ok(0<returned[l['order_line_id']]<=l['quantity'],'cumulative return quantity')
        ok(ship_by_order[l['order_id']]['actual_delivery_date']<=r['return_date']<=cfg['cutoff'],'return knowledge cutoff')
        ok(r['refund_cents']==r['returned_quantity']*l['net_unit_price_cents'],'refund identity')
        ok(r['recoverable_value_cents']==rounded(r['returned_quantity']*cost['unit_cost_cents']*8000),'recovery policy')
        ok(r['net_return_cost_cents']==r['refund_cents']+r['restocking_cents']-r['recoverable_value_cents'],'return cost identity')
    for a in t['account_activity']:
        ok(ix['purchasers'][a['purchaser_id']]['customer_id']==a['customer_id'] and a['activity_date']<=a['known_date']<=cfg['cutoff'],'activity ownership and cutoff')
    for p in t['account_plans']: ok(p['approved_date']<p['month_start']<=cfg['cutoff'],'plan known in advance')
    # Counts, not repeated labels, keep the report compact.
    return {'status':'pass','assertions':len(checks),'gate_counts':dict(Counter(checks)),
            'rows':{k:len(v) for k,v in t.items()},'calendar_months':dict(sorted(monthly.items()))}


def scenario_checks(cfg, states, affected):
    combined=states['combined']; baseline=states['baseline']; report={}; checks={}
    def compare(label,old,new,metric,bounds):
        a=totals(old)[metric];b=totals(new)[metric]
        if not a: raise ValueError('zero comparison denominator: '+label)
        change=b/a-1
        report[label]={'before':a,'after':b,'metric':metric,'change':change,'bounds':bounds}
        checks[label]=bounds[0]<=change<=bounds[1]
    scopes=lambda rows,year:[r for r in rows if r['country'] in ('US','UK') and f'{year}-01-01'<=r['date']<=f'{year}-06-30']
    compare('US_UK_H1_sales_YoY',scopes(combined,2025),scopes(combined,2026),'revenue_after_returns',cfg['bounds']['margin_sales_yoy'])
    compare('US_UK_H1_contribution_YoY',scopes(combined,2025),scopes(combined,2026),'contribution_after_returns',cfg['bounds']['margin_contribution_yoy'])
    for cid in cfg['accounts_scenario']['accounts']:
        select=lambda year:[r for r in combined if r['customer_id']==cid and f'{year}-03-03'<=r['date']<=f'{year}-12-31']
        compare(cid+'_sales_YoY',select(2024),select(2025),'revenue',cfg['bounds']['account_sales_yoy'])
    select=lambda year:[r for r in combined if r['country']=='CN' and r['customer_id'] not in cfg['accounts_scenario']['accounts'] and f'{year}-03-03'<=r['date']<=f'{year}-12-31']
    compare('CN_unaffected_sales_YoY',select(2024),select(2025),'revenue',cfg['bounds']['unaffected_account_sales_yoy'])
    promo_ids=set(affected['promotion']);promoted=[r for r in combined if r['order_line_id'] in promo_ids]
    compare('promotion_units_vs_private_baseline',[r for r in baseline if r['order_line_id'] in promo_ids],promoted,'units',cfg['bounds']['promotion_units_lift'])
    for channel in ('direct','reseller'):
        total=totals([r for r in promoted if r['channel']==channel]);report['promotion_'+channel]=total
        checks['promotion_'+channel]=(total['contribution_after_returns']>0 if channel=='direct' else total['contribution_after_returns']<0)
    overall={name:totals(rows) for name,rows in states.items()}
    interactions={k:overall['combined'][k]-overall['baseline'][k]-sum(overall[s][k]-overall['baseline'][k] for s in SCENARIOS) for k in METRICS}
    overlap=set(affected['margin'])&set(affected['promotion'])
    checks['nonempty_cost_promotion_overlap']=len(overlap)>0
    checks['nonzero_interaction']=interactions['contribution_after_returns']!=0
    report.update(checks=checks,totals=overall,interaction_residual=interactions,overlap_lines=len(overlap),
        basis='Monetary totals in USD cents; YoY observations and private intervention contrasts are separate.')
    return report


def zip_directory(source, destination, names=None):
    source=Path(source)
    files=sorted(names if names is not None else [str(p.relative_to(source)) for p in source.rglob('*') if p.is_file()])
    with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name in files:
            info=zipfile.ZipInfo(name,date_time=(2024,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o644<<16;z.writestr(info,(source/name).read_bytes())


def overview(scenarios, counts):
    esc=html.escape
    rows=''
    for label in ('US_UK_H1_sales_YoY','US_UK_H1_contribution_YoY','C0003_sales_YoY','C0007_sales_YoY','CN_unaffected_sales_YoY'):
        r=scenarios[label]
        rows+=f"<tr><td>{esc(label)}</td><td>${r['before']/100:,.2f}</td><td>${r['after']/100:,.2f}</td><td>{r['change']:+.1%}</td></tr>"
    promo=''.join(f"<li>{channel.title()} promotion cohort contribution after returns: ${scenarios['promotion_'+channel]['contribution_after_returns']/100:,.2f}</li>" for channel in ('direct','reseller'))
    inventory=''.join(f'<tr><td>{esc(k)}</td><td>{v:,}</td></tr>' for k,v in counts.items())
    return f"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Bravura Apple demo release</title>
<style>body{{font:16px/1.6 system-ui;background:#f3f6f3;color:#163c33;margin:0}}main{{max-width:1050px;margin:32px auto;padding:32px;background:white}}h1{{font-size:36px}}table{{border-collapse:collapse;width:100%;font-size:14px}}td,th{{padding:10px;text-align:left;border-bottom:1px solid #ddd}}.note{{padding:16px;background:#fff1d5}}.scroll{{overflow:auto}}</style><main>
<p>BRAVURA / APPLE-INSPIRED DEMO / AUTHORING RESULTS</p><h1>{counts['order_lines']:,} lines. 30 months. Interacting business stories.</h1>
<p>January 2024–June 2026 · {counts['customers']:,} fictional accounts · {counts['purchasers']:,} purchasers · USD synthetic economics</p>
<p class="note">This report contains the answer key. Do not give it to a blind analyst. Apple product names and regional definitions provide context; customers, prices, costs and events are simulated.</p>
<h2>Observed comparisons in the combined dataset</h2><div class="scroll"><table><tr><th>Population and metric</th><th>Prior period</th><th>Current period</th><th>YoY</th></tr>{rows}</table></div>
<p>US/UK compares H1 2025 with H1 2026 after returns. Account and unaffected-China comparisons use March 3–December 31, 2024 versus the same dates in 2025, before returns. These are observed comparisons, not isolated causal effects.</p>
<h2>Promotion tradeoff</h2><ul>{promo}</ul><p>Both annual synthetic refresh offers, April–June 2025 and 2026. The source news does not establish these outcomes at Apple.</p>
<h2>Overlap and evidence strength</h2><p>{scenarios['overlap_lines']:,} lines participate in both margin pressure and promotion. The private interaction residual for contribution after returns is ${scenarios['interaction_residual']['contribution_after_returns']/100:,.2f}. It is reported separately, not silently counted as an isolated effect.</p>
<p>Account C0003 has preceding delivery and unresolved service evidence. C0007 declines without a supported operational cause. The evaluator knows the purchasing mechanism; the analyst should preserve uncertainty.</p>
<h2>Validation</h2><p>All configured scenario/plausibility gates passed. Keys, grains, purchaser ownership, product availability, effective costs, cents-level financial identities, shipment allocations, returns and cutoff checks passed for baseline, isolated and combined states. Combined regeneration matched exactly.</p>
<p>Operational ZIP allowlist and missing-private-path checks passed. Full environment isolation and fresh-context blind analyst evaluation were NOT RUN. Export separation alone is not an isolation guarantee.</p>
<h2>Package contents</h2><ul><li>operational.zip: business CSVs and neutral dictionary; the only candidate analyst input.</li><li>answer_key.zip: parameters, approved design, affected records, baseline/isolated economics, evaluation and provenance.</li></ul>
<h2>Operational table inventory</h2><table><tr><th>Table</th><th>Rows</th></tr>{inventory}</table>
<p>Selected legacy generations and synthetic configuration bands are intentional; this is not a complete current Apple catalog. Money columns ending in _cents must be divided by 100 for dollars. No inventory or realized-benefit claims.</p></main></html>"""


def generate(cfg, approval, out):
    validate_config(cfg)
    verify_approval(approval,approval['bundle'])
    c.require(approval['bundle'].get('generation_config_sha256')==c.digest(cfg),'generation parameters differ from approved snapshot')
    spec=approval['bundle']['brief']
    c.require(cfg['order_lines']==spec['order_lines'] and cfg['start_date']==spec['start_date'] and cfg['end_date']==spec['end_date'] and cfg['cutoff']==spec['reporting_cutoff'],'configuration differs from approved scope')
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    answer=out/'answer_key';answer.mkdir()
    dump=lambda path,data: Path(path).write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    dump(answer/'configuration.json',cfg);dump(answer/'design_approval.json',approval)
    state_metrics={};validations={};baseline_rates={}
    started=time.monotonic()
    for name,active in [('baseline',()),*[(s,(s,)) for s in SCENARIOS],('combined',SCENARIOS)]:
        t,affected=simulate(cfg,active)
        validations[name]=validate(t,cfg)
        state_metrics[name]=line_metrics(t)
        write_tables({'line_economics':state_metrics[name]},answer/name)
        if name=='baseline':
            baseline_rates={'return_line_rate':len(t['returns'])/len(t['order_lines']),
                'late_shipment_rate':sum(s['actual_delivery_date']>s['promised_date'] for s in t['shipments'])/len(t['shipments'])}
        if name=='combined':
            combined=t;combined_affected=affected
    scenarios=scenario_checks(cfg,state_metrics,combined_affected)
    scenarios['checks']['baseline_return_rate']=.02<=baseline_rates['return_line_rate']<=.04
    scenarios['checks']['baseline_late_rate']=.05<=baseline_rates['late_shipment_rate']<=.09
    if cfg.get('customer_dynamics'):
        from .customer_audit import audit
        customer_report = audit(combined)
        dump(answer/'customer_story_audit.json',customer_report)
        scenarios['checks'].update(customer_report['checks'])
    from .recipes import quality_audit, recipe_catalog
    dump(answer/'recipe_catalog.json', recipe_catalog())
    if cfg.get('quality'):
        quality_report = quality_audit(combined, cfg['quality'])
        dump(answer/'quality_story_audit.json',quality_report)
        scenarios['checks'].update(quality_report['checks'])
    dump(answer/'scenario_evaluation.json',scenarios)
    dump(answer/'affected_records.json',combined_affected)
    dump(answer/'validation.json',{'states':validations,'baseline_rates':baseline_rates,
          'scenario_checks':scenarios['checks'],'blind_evaluation':'not_run','access_isolation':'not_run'})
    if not all(scenarios['checks'].values()):
        raise ValueError('Scenario release gates failed: '+str([k for k,v in scenarios['checks'].items() if not v]))
    # Repeat the combined state from scratch; check every serialized table.
    repeat,_=simulate(cfg,SCENARIOS)
    c.require(c.digest(repeat)==c.digest(combined),'combined regeneration mismatch')
    operational=out/'operational';write_tables(combined,operational)
    dictionary={'status':'Synthetic Apple-inspired commercial slice; no actual customer records or private Apple economics.',
        'start_date':cfg['start_date'],'end_date':cfg['end_date'],'reporting_cutoff':cfg['cutoff'],
        'currency':'USD','money_unit':'integer cents; divide by 100 for dollars',
        'calendar':'Gregorian month/quarter/year; not Apple fiscal periods',
        'product_policy':'Selected legacy generations; synthetic configuration bands and commercial prices. Not a complete current catalog.',
        'relationships':{'orders':'one order -> two order_lines; one shipment per order',
            'purchasers':'many purchasers -> one customer; order purchaser must belong to order customer',
            'shipments':'allocated through shipment_allocations; never sum full shipment cost once per line',
            'returns':'at most one event per sold line; quantity <= sold quantity',
            'cost_history':'unique product, market and effective interval',
            'territories':'territory -> country -> Apple reporting region; India belongs to Europe'},
        'metrics':{'net_sales':'quantity * rounded net_unit_price','gross_profit':'net_sales - product_cost',
            'contribution':'gross_profit - allocated_fulfillment - program_cost',
            'net_revenue_after_returns':'net_sales - refund',
            'contribution_after_returns':'contribution - (refund + restocking - recoverable_value)'},
        'rounding':'Half-up at net unit price/program/recovery; integer arithmetic thereafter; largest-remainder allocation.',
        'missing_cost':'unknown, never zero','NONE_promotion':'Explicit not-applicable member',
        'tables':{k:{'primary_key':KEYS.get(k,['shipment_id','order_line_id']),
                       'columns':list(v[0]) if v else []} for k,v in combined.items()}}
    dump(operational/'data_dictionary.json',dictionary)
    (operational/'README.txt').write_text('SYNTHETIC DEMO DATA — not Apple operational records.\nRead data_dictionary.json for units, joins and definitions.\nTransaction history: January 2024–June 2026. All accounts, purchasers, prices, costs and operational events are simulated.\n')
    actual={p.name for p in operational.iterdir()}
    c.require(actual==ALLOWLIST,'operational export differs from allowlist')
    for p in operational.glob('*.csv'):
        header=p.read_text().splitlines()[0].lower()
        c.require(not any(x in header for x in ('scenario','counterfactual','ground_truth','expected_effect','injected')),'answer-bearing header')
    zip_directory(operational,out/'operational.zip',ALLOWLIST)
    with zipfile.ZipFile(out/'operational.zip') as z:
        c.require(set(z.namelist())==ALLOWLIST,'ZIP allowlist mismatch')
        for forbidden in ('../answer_key/configuration.json','answer_key/affected_records.json','generator.py'):
            try: z.read(forbidden)
            except KeyError: pass
            else: raise ValueError('private file included in operational ZIP')
    dump(answer/'manifest.json',{'generator_version':VERSION,'python_version':platform.python_version(),
        'config_sha256':c.digest(cfg),'approval_sha256':c.digest(approval),'operational_checksums':file_hashes(operational),
        'code_checksums':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(__file__).parent.glob('*.py'))},
        'reproducibility':'combined state regenerated and matched exactly; all exported files checksummed',
        'export_allowlist':'pass','zip_negative_path_checks':'pass','full_environment_isolation':'not_run',
        'fresh_context_analyst':'not_run'})
    dump(answer/'runtime.json',{'elapsed_seconds':round(time.monotonic()-started,3)})
    summary=overview(scenarios,{k:len(v) for k,v in combined.items()})
    (answer/'overview.html').write_text(summary)
    (out/'OVERVIEW.html').write_text(summary)
    zip_directory(answer,out/'answer_key.zip')
    (out/'README.txt').write_text(f'Bravura Apple demo {VERSION}\n\noperational.zip: synthetic business records and neutral dictionary.\nanswer_key.zip: authoring/evaluator-only configuration, approved design, baseline and isolated states, effects and validation.\nNever give answer_key.zip, this repository, or the authoring blueprint to a blind analyst.\nNo fresh-context analyst test or full filesystem access-isolation test was run. ZIP allowlist tests are not that isolation proof.\nSee answer_key/scenario_evaluation.json for observed YoY versus private intervention effects. Money is integer USD cents.\n')
    zip_directory(out,out/'Bravura_Apple_Demo.zip',['README.txt','OVERVIEW.html','operational.zip','answer_key.zip'])
    return {'rows':len(combined['order_lines']),'purchasers':len(combined['purchasers']),
            'scenario_checks':scenarios['checks'],'totals':scenarios['totals']['combined'],
            'seconds':round(time.monotonic()-started,3)}
