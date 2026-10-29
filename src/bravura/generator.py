"""Deterministic business-slice simulator. All economics and accounts are synthetic.

Money uses integer cents with explicit half-up rational rounding. Scenario states
share keyed random draws; no model is involved in arithmetic or row generation.
"""
import calendar
import csv
import hashlib
import json
import random
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

VERSION = '0.3.0'
SCENARIOS = ('margin', 'accounts', 'promotion')
COUNTRIES = [('US','United States','Americas'), ('UK','United Kingdom','Europe'),
             ('IN','India','Europe'), ('CN','Mainland China','Greater China')]


def rounded(n, d=10000):
    if d <= 0 or n < 0:
        raise ValueError('rounding requires nonnegative numerator and positive denominator')
    return (2*n+d)//(2*d)


def money(cents):
    return f'{cents/100:.2f}' if abs(cents) < 10**12 else f'{cents//100}.{cents%100:02}'


def rng(seed, *keys):
    return random.Random(int.from_bytes(hashlib.sha256(json.dumps([seed,*keys]).encode()).digest()[:16], 'big'))


def allocate(total, weights):
    """Largest remainder, stable tie-break by input position; exact conservation."""
    if total < 0 or not weights or min(weights) <= 0:
        raise ValueError('positive allocation weights required')
    denom = sum(weights)
    result = [total*w//denom for w in weights]
    ranked = sorted(range(len(weights)), key=lambda i: (-(total*weights[i]%denom), i))
    for i in ranked[:total-sum(result)]:
        result[i] += 1
    return result


def months(start, end):
    current = date.fromisoformat(start).replace(day=1)
    last = date.fromisoformat(end)
    while current <= last:
        yield current
        current = date(current.year+int(current.month==12), current.month%12+1, 1)


def acquisition(cfg, i):
    if not cfg.get('customer_dynamics') or i < 260:
        return '2023-01-01'
    return f"{2025 if i < 280 else 2026}-{1+(i%20)//4:02}-01"


def customer_available(cfg, i, month):
    if month.isoformat() < acquisition(cfg, i):
        return False
    if not cfg.get('customer_dynamics'):
        return True
    # Private purchase cessation is not an operational assertion of churn.
    if 220 <= i < 240 and month >= date(2025, 7+(i%6), 1):
        return False
    if 240 <= i < 250 and date(2025, 4, 1) <= month < date(2025, 10, 1):
        return False
    return True


def account_scale(cfg, i, month):
    if not cfg.get('customer_dynamics'):
        return 10000
    d = cfg['customer_dynamics']
    scale = d['large_account_scale_bp'] if i < 10 else 10000
    if i < 3:
        scale = rounded(scale * (10000 + d['anchor_growth_bp'] * (month.year-2024)))
    if i >= 260:
        acquired = date.fromisoformat(acquisition(cfg, i))
        age = (month.year-acquired.year)*12+month.month-acquired.month
        scale = rounded(scale * min(10000, 4000+age*2000))
    return scale


def dimensions(cfg):
    seed = cfg['seed']
    tables = {}
    tables['regions'] = [dict(region_id=f'R{i+1}', region_name=name) for i,name in enumerate(
        ['Americas','Europe','Greater China','Japan','Rest of Asia Pacific'])]
    rid = {r['region_name']:r['region_id'] for r in tables['regions']}
    tables['territories'] = [dict(territory_id=f'{code}-{j}',country_code=code,country_name=name,
        region_id=rid[region],territory_name=f'{name} Business {j}') for code,name,region in COUNTRIES for j in (1,2,3)]
    tables['channels'] = [dict(channel_id='direct',channel_name='Direct business'),dict(channel_id='reseller',channel_name='Reseller')]
    tables['sales_organization'] = [dict(sales_rep_id=f'SR{i:02}',team_id=f'T{i//5:02}',rep_name=f'Account manager {i:02}') for i in range(20)]
    tables['fulfillment_locations'] = [dict(location_id=f'W{code}',country_code=code,location_name=f'{name} distribution hub') for code,name,_ in COUNTRIES]
    tables['suppliers'] = [dict(supplier_id=f'S{i}',supplier_name=f'Component Partner {i}') for i in range(3)]
    tables['customer_parents'] = [dict(parent_id=f'G{i:03}',parent_name=f'Business Group {i:03}') for i in range(100)]
    customers, purchasers, locations = [], [], []
    for i in range(cfg['accounts']):
        code = COUNTRIES[i%4][0]
        cid = f'C{i:04}'
        customers.append(dict(customer_id=cid,customer_name=f'{["Cedar","Harbor","Summit","Orchard"][i%4]} {i:03} Systems',
            parent_id=f'G{i//3:03}',territory_id=f'{code}-{i%3+1}',country_code=code,
            sales_rep_id=f'SR{i%20:02}',channel_id='reseller' if i%3==0 else 'direct',
            industry=['Professional services','Education','Manufacturing','Healthcare','Technology'][i%5],
            account_tier='Growth' if i%5==0 else 'Core',acquisition_date=acquisition(cfg, i)))
        locations.append(dict(customer_location_id=f'CL{i:04}',customer_id=cid,location_name='Primary office',country_code=code))
        for j in range(2+rng(seed,'buyers',i).randrange(4)):
            purchasers.append(dict(purchaser_id=f'P{i:04}-{j}',customer_id=cid,purchaser_name=f'Buyer {i:03}-{j}',
                buyer_role=['Procurement','IT operations','Finance','Department lead','Administration'][j],
                valid_from=acquisition(cfg, i),valid_to=cfg['cutoff']))
    tables.update(customers=customers,purchasers=purchasers,customer_locations=locations)
    tables['product_categories'] = [dict(category_id=k,category_name=v) for k,v in [('CAT1','iPhone'),('CAT2','Mac'),('CAT3','iPad')]]
    cat_ids={r['category_name']:r['category_id'] for r in tables['product_categories']}
    tables['product_families'] = [dict(family_id=k,family_name=v,category_id=cat_ids[c]) for k,v,c in [('F1','iPhone','iPhone'),('F2','MacBook Air','Mac'),('F3','iPad Air','iPad')]]
    fam_ids={r['family_name']:r['family_id'] for r in tables['product_families']}
    tables['product_versions'] = [dict(version_id=f'V{i:02}',family_id=fam_ids[v['family']],version_name=v['version'],available_from=v['available_from']) for i,v in enumerate(cfg['catalog'])]
    products = []
    for vi,v in enumerate(cfg['catalog']):
        for tier in range(3):
            # Configuration bands are synthetic commercial variants, not Apple SKU identifiers.
            products.append(dict(product_id=f'PR{vi:02}-{tier}',category_id=cat_ids[v['category']],family_id=fam_ids[v['family']],version_id=f'V{vi:02}',category=v['category'],family=v['family'],
                version=v['version'],product_name=f'{v["family"]} {v["version"]} / Configuration {tier+1}',
                configuration_band=tier,available_from=v['available_from'],available_to=cfg['end_date'],
                supplier_id=f'S{vi%3}',list_price_cents=v['price_cents']+tier*20000,
                baseline_cost_cents=rounded((v['price_cents']+tier*20000)*(6800+tier*400))))
    tables['products'] = products
    days=[]
    current=date.fromisoformat(cfg['start_date'])
    while current<=date.fromisoformat(cfg['cutoff']):
        days.append(dict(date_id=current.isoformat(),calendar_year=current.year,calendar_quarter=(current.month-1)//3+1,
                         calendar_month=current.month,month_id=current.strftime('%Y-%m'),day_of_week=current.isoweekday()))
        current+=timedelta(days=1)
    tables['calendar']=days
    return tables


def simulate(cfg, active=()):
    active=set(active)
    if not active<=set(SCENARIOS):
        raise ValueError('unknown scenario')
    tables=dimensions(cfg)
    products=tables['products']; seed=cfg['seed']
    buyers=defaultdict(list)
    for p in tables['purchasers']: buyers[p['customer_id']].append(p['purchaser_id'])
    ms=list(months(cfg['start_date'],cfg['end_date']))
    # Exactly two lines per order. Matching month volumes have the same seasonal basis.
    counts=allocate(cfg['order_lines']//2,[cfg['seasonality'][m.month-1] for m in ms])
    tables['cost_history']=[]
    for p in products:
        for year in range(2024,2027):
            a=max(p['available_from'],f'{year}-01-01'); b=min(cfg['end_date'],f'{year}-12-31')
            if a>b: continue
            for market in ['US','UK','IN','CN']:
                cost=p['baseline_cost_cents']
                if 'margin' in active and year==2026 and market in ('US','UK'):
                    cost=rounded(cost*(10000+cfg['margin']['cost_uplift_bp']))
                tables['cost_history'].append(dict(cost_version_id=f'CV-{p["product_id"]}-{market}-{year}',
                    product_id=p['product_id'],country_code=market,supplier_id=p['supplier_id'],
                    effective_start=a,effective_end=b,unit_cost_cents=cost,change_reason='Annual supply schedule'))
    costs={x['cost_version_id']:x for x in tables['cost_history']}
    promos=[dict(promotion_id='NONE',promotion_name='No promotion',start_date=cfg['start_date'],end_date=cfg['end_date'],eligible_family='All',eligible_markets='US|UK|IN|CN',eligible_account_tier='All',eligible_channel='All',discount_bp=0,program_cost_bp=0)]
    if 'promotion' in active:
        for year in (2025,2026):
            for channel in ('direct','reseller'):
                promos.append(dict(promotion_id=f'CP{year}-{channel}',promotion_name=f'Business Refresh {year}',
                    start_date=f'{year}-04-01',end_date=f'{year}-06-30',eligible_family='MacBook Air',
                    eligible_markets='US|UK|IN',eligible_account_tier='Growth',eligible_channel=channel,
                    discount_bp=cfg['promotion'][channel]['discount_bp'],program_cost_bp=cfg['promotion'][channel]['program_bp']))
    tables['promotions']=promos
    orders=[]; lines=[]; shipments=[]; allocations=[]; returns=[]; affected={s:[] for s in SCENARIOS}
    order_idx=0
    for m,count in zip(ms,counts):
        eligible = [i for i in range(cfg['accounts']) if customer_available(cfg, i, m)]
        for k in range(count):
            # Customer/product preferences repeat seasonally; dates and return decisions vary by year.
            r=rng(seed,'demand',m.month,k)
            ci=k%cfg['accounts'] if k<cfg['accounts'] else r.randrange(cfg['accounts'])
            if cfg.get('customer_dynamics'):
                if ci not in eligible:
                    ci = rng(seed, 'replacement', m.isoformat(), k).choice(eligible)
                elif ci >= 10 and rng(seed, 'cadence', m.month, ci).random() < .18:
                    ci = rng(seed, 'cadence-replacement', m.month, k).choice(eligible[:10])
            customer=tables['customers'][ci]; cid=customer['customer_id']; country=customer['country_code']
            day=min(1+r.randrange(calendar.monthrange(m.year,m.month)[1]),calendar.monthrange(m.year,m.month)[1])
            dt=date(m.year,m.month,day); ds=dt.isoformat()
            order_idx+=1; oid=f'O{order_idx:06}'
            pid=buyers[cid][r.randrange(len(buyers[cid]))]
            service='accounts' in active and cid==cfg['accounts_scenario']['service_account'] and ds>='2025-02-01'
            declined='accounts' in active and cid in cfg['accounts_scenario']['accounts'] and ds>='2025-03-03'
            margin='margin' in active and m.year==2026 and country in ('US','UK')
            order_lines=[]
            for slot in range(2):
                lid=f'L{(order_idx-1)*2+slot+1:06}'
                family=r.choices(['iPhone','MacBook Air','iPad Air'],[45,35,20])[0]
                available=[p for p in products if p['family']==family and p['available_from']<=ds]
                latest=max(p['available_from'] for p in available)
                # Most demand follows available generations; a long tail retains older models.
                group=[p for p in available if p['available_from']==latest] if r.random()<.8 else available
                tier_roll=r.random(); tier=0 if tier_roll<.55 else 1 if tier_roll<.85 else 2
                if margin and tier_roll<cfg['margin']['premium_mix_bp']/10000: tier=2
                candidates=[p for p in group if p['configuration_band']==tier]
                p=r.choice(candidates)
                quantity=rounded(r.randint(8,24)*(10000+500*(m.year-2024)))
                quantity = max(1, rounded(quantity * account_scale(cfg, ci, m)))
                if declined: quantity=max(1,rounded(quantity*cfg['accounts_scenario']['retention_bp']))
                promo=('promotion' in active and m.year in (2025,2026) and 4<=m.month<=6 and
                       family=='MacBook Air' and country!='CN' and customer['account_tier']=='Growth')
                discount=200+(ci%4)*100; program=0; promo_id='NONE'
                if cfg.get('customer_dynamics') and ci >= 260:
                    discount += cfg['customer_dynamics']['new_account_discount_bp']
                if promo:
                    terms=cfg['promotion'][customer['channel_id']]
                    discount=terms['discount_bp']; program=terms['program_bp']; promo_id=f'CP{m.year}-{customer["channel_id"]}'
                    quantity=rounded(quantity*(10000+cfg['promotion']['unit_uplift_bp']))
                cv=f'CV-{p["product_id"]}-{country}-{m.year}'
                unit_price=rounded(p['list_price_cents']*(10000-discount))
                revenue=quantity*unit_price; cost=quantity*costs[cv]['unit_cost_cents']
                line=dict(order_line_id=lid,order_id=oid,order_date=ds,customer_id=cid,purchaser_id=pid,
                    product_id=p['product_id'],territory_id=customer['territory_id'],channel_id=customer['channel_id'],
                    promotion_id=promo_id,cost_version_id=cv,quantity=quantity,list_unit_price_cents=p['list_price_cents'],
                    discount_bp=discount,net_unit_price_cents=unit_price,net_sales_cents=revenue,product_cost_cents=cost,
                    gross_profit_cents=revenue-cost,program_cost_cents=rounded(revenue*program))
                order_lines.append(line)
                for s,flag in [('margin',margin),('accounts',declined or service),('promotion',promo)]:
                    if flag: affected[s].append(lid)
            rr=rng(seed,'fulfillment',oid)
            expedite=rr.random()<(.35 if margin else .08) or any(x['promotion_id']!='NONE' for x in order_lines)
            ship=dt+timedelta(days=1); promised=ship+timedelta(days=2 if expedite else 4)
            late=rr.random()<(.75 if service else .07)
            delivery=promised+timedelta(days=rr.randint(2,6) if late else -1)
            units=sum(x['quantity'] for x in order_lines)
            freight=1000+units*125; surcharge=units*175 if expedite else 0; handling=units*50
            total=freight+surcharge+handling
            shipments.append(dict(shipment_id=f'SH{order_idx:06}',order_id=oid,location_id=f'W{country}',ship_date=ship.isoformat(),
                promised_date=promised.isoformat(),actual_delivery_date=delivery.isoformat(),ship_mode='Express' if expedite else 'Standard',
                freight_cents=freight,expedite_cents=surcharge,handling_cents=handling,total_fulfillment_cents=total))
            shares=allocate(total,[x['quantity'] for x in order_lines])
            for line,share in zip(order_lines,shares):
                line['allocated_fulfillment_cents']=share
                line['contribution_cents']=line['gross_profit_cents']-share-line['program_cost_cents']
                allocations.append(dict(shipment_id=f'SH{order_idx:06}',order_line_id=line['order_line_id'],allocated_cost_cents=share))
                ret_rng=rng(seed,'return',line['order_line_id'])
                rate=.03
                if line['promotion_id']!='NONE': rate=cfg['promotion'][customer['channel_id']]['return_rate_bp']/10000
                if ret_rng.random()<rate:
                    qty=max(1,rounded(line['quantity']*ret_rng.randint(2000,6000)))
                    refund=qty*line['net_unit_price_cents']; restock=qty*1000
                    recovery=rounded(qty*costs[line['cost_version_id']]['unit_cost_cents']*8000)
                    returns.append(dict(return_id=f'RT{len(returns)+1:06}',order_line_id=line['order_line_id'],
                        return_date=(delivery+timedelta(days=ret_rng.randint(7,35))).isoformat(),returned_quantity=qty,
                        return_reason=ret_rng.choice(['Compatibility','Order adjustment','Transit damage']),refund_cents=refund,
                        restocking_cents=restock,recoverable_value_cents=recovery,net_return_cost_cents=refund+restock-recovery))
                lines.append(line)
            orders.append(dict(order_id=oid,order_date=ds,customer_id=cid,purchaser_id=pid,
                bill_to_location_id=f'CL{ci:04}',ship_to_location_id=f'CL{ci:04}',sales_rep_id=customer['sales_rep_id'],currency='USD'))
    tables.update(orders=orders,order_lines=lines,shipments=shipments,shipment_allocations=allocations,returns=returns)
    activity=[]; plans=[]
    for m in ms:
        for ci,c in enumerate(tables['customers']):
            if m.isoformat() < c['acquisition_date']:
                continue
            cid=c['customer_id']; service='accounts' in active and cid==cfg['accounts_scenario']['service_account'] and m>=date(2025,2,1)
            ar=rng(seed,'activity',m.isoformat(),cid)
            reason='Delivery inquiry' if service or ar.random()<.06 else ar.choice(['Account review','Purchase planning','Product inquiry'])
            activity.append(dict(activity_id=f'AC{len(activity)+1:06}',customer_id=cid,purchaser_id=buyers[cid][0],
                activity_date=m.isoformat(),known_date=m.isoformat(),reason_code=reason,resolved='false' if service else 'true'))
            plans.append(dict(plan_id=f'PL{len(plans)+1:06}',customer_id=cid,month_start=m.isoformat(),
                approved_date=(m-timedelta(days=15)).isoformat(),planned_sales_cents=rounded((5000000+(ci%7)*500000)*account_scale(cfg,ci,m))))
    tables.update(account_activity=activity,account_plans=plans)
    for product in tables['products']:
        del product['baseline_cost_cents']  # Authoring baseline must not leak in the product dimension.
    return tables,affected


def line_metrics(tables):
    ret={r['order_line_id']:r for r in tables['returns']}
    rows=[]
    products={p['product_id']:p for p in tables['products']}; customers={c['customer_id']:c for c in tables['customers']}
    for line in tables['order_lines']:
        r=ret.get(line['order_line_id'],{})
        rows.append(dict(order_line_id=line['order_line_id'],date=line['order_date'],customer_id=line['customer_id'],
            country=customers[line['customer_id']]['country_code'],family=products[line['product_id']]['family'],
            channel=line['channel_id'],promotion=line['promotion_id'],units=line['quantity'],
            revenue=line['net_sales_cents'],gross_profit=line['gross_profit_cents'],contribution=line['contribution_cents'],
            revenue_after_returns=line['net_sales_cents']-r.get('refund_cents',0),
            contribution_after_returns=line['contribution_cents']-r.get('net_return_cost_cents',0)))
    return rows


METRICS=('units','revenue','gross_profit','contribution','revenue_after_returns','contribution_after_returns')

def totals(rows):
    return {k:sum(x[k] for x in rows) for k in METRICS}


def write_tables(tables, out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    for name,rows in tables.items():
        if not rows: continue
        with (out/(name+'.csv')).open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def file_hashes(path):
    return {str(p.relative_to(path)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(path).rglob('*')) if p.is_file()}
