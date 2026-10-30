"""Versioned authoring recipes; operational data never contains recipe IDs.

QualityFeedback consumes canonical line/return fields and is independent of
organization names, customer identifiers, calendar years and product taxonomy.
Existing mechanisms remain in the Apple adapter; catalog entries do not imply
that arbitrary industry schemas are executable.
"""
from datetime import date, timedelta


def recipe_catalog():
    definitions = [
        ('margin', 'Growth with margin deterioration', ['cost_uplift_bp','premium_mix_bp'], ['cost_history','order_lines','shipments'], 'Comparable-period revenue and contribution', ['Product mix','Freight','Commercial terms']),
        ('accounts', 'Concentrated decline with partial explanation', ['accounts','service_account','retention_bp'], ['customers','account_activity','shipments','order_lines'], 'Same-account comparable periods and advance plans', ['Procurement timing','Competition','Unexplained decline']),
        ('promotion', 'Promotional growth with weak contribution', ['unit_uplift_bp','discount_bp','program_bp','return_rate_bp'], ['promotions','order_lines','returns','shipment_allocations'], 'Eligible cohorts; private intervention contrast kept separate', ['Selection','Seasonality','Purchase pull-forward']),
        ('customer_dynamics', 'Acquisition masking inactivity and concentration', ['large_account_scale_bp','anchor_growth_bp','new_account_discount_bp'], ['customers','customer_parents','order_lines'], 'Conserved new/retained/inactive revenue and contribution bridges', ['Temporary dormancy','Account migration','Normal replacement cycles']),
        ('quality', 'Returns followed by weaker purchasing', ['product_ids','start_date','end_date','return_rate_bp','response_share_bp','retention_bp','lag_days','followup_days'], ['products','returns','account_activity','order_lines'], 'Mature delivery cohorts and equal pre/post account windows', ['Promotion pull-forward','Seasonality','Other service failures','Unaffected decline'])]
    return {'version':1,'recipes':[dict(id=k,version=1,title=title,parameters=params,evidence_tables=tables,comparison=basis,alternatives=alts,
        implementation='portable canonical-field mechanism' if k=='quality' else 'existing Apple adapter; portable design recipe',
        decision_owner='CRO with account, product and finance owners',
        economics='Integer cents; revenue, gross profit, contribution and returns reconciled separately. No realized benefit modeled.',
        validation='Structural and financial integrity, recipe gates on final combined data, held-out seeds and exact regeneration',
        publication='Authoring only; operational evidence exported by allowlist',
        prohibited_claims=['YoY or peer differences prove causality','Inactivity proves churn','Historical decline equals recoverable benefit']) for k,title,params,tables,basis,alts in definitions]}


def validate_quality(q):
    if q is None: return
    required={'product_ids','start_date','end_date','return_rate_bp','response_share_bp','retention_bp','lag_days','followup_days','minimum_return_lines','minimum_responding_accounts'}
    if set(q)!=required: raise ValueError('quality recipe fields differ from supported v1 contract')
    if not q['product_ids'] or len(set(q['product_ids']))!=len(q['product_ids']): raise ValueError('quality requires distinct products')
    if date.fromisoformat(q['start_date'])>date.fromisoformat(q['end_date']): raise ValueError('quality date interval')
    for k in ('return_rate_bp','response_share_bp','retention_bp'):
        if type(q[k]) is not int or not 0<=q[k]<=10000: raise ValueError(k)
    for k in ('lag_days','followup_days','minimum_return_lines','minimum_responding_accounts'):
        if type(q[k]) is not int or q[k]<1: raise ValueError(k)


class QualityFeedback:
    def __init__(self, config, seed):
        validate_quality(config)
        self.config=config;self.seed=seed;self.events=[];self.first_return={}

    def applies(self,line):
        q=self.config
        return bool(q and line['product_id'] in q['product_ids'] and q['start_date']<=line['order_date']<=q['end_date'])

    def responds(self,customer):
        from .generator import rng
        return bool(self.config and rng(self.seed,'quality-response',customer).randrange(10000)<self.config['response_share_bp'])

    def record(self,line,returned):
        cid=line['customer_id'];dt=returned['return_date']
        self.first_return[cid]=min(self.first_return.get(cid,dt),dt)
        self.events.append(dict(customer_id=cid,purchaser_id=line['purchaser_id'],order_line_id=line['order_line_id'],return_date=dt))

    def quantity(self,customer,order_date,quantity):
        from .generator import rounded
        if customer not in self.first_return or not self.responds(customer): return quantity
        after=date.fromisoformat(self.first_return[customer])+timedelta(days=self.config['lag_days'])
        return max(1,rounded(quantity*self.config['retention_bp'])) if date.fromisoformat(order_date)>=after else quantity


def quality_audit(t,q):
    """Observed evidence with equal windows; private response membership separate."""
    lines={r['order_line_id']:r for r in t['order_lines']}
    targeted={k:v for k,v in lines.items() if v['product_id'] in q['product_ids'] and q['start_date']<=v['order_date']<=q['end_date']}
    events=[r for r in t['returns'] if r['order_line_id'] in targeted and r['return_reason']=='Intermittent failure']
    first={}
    for r in events:
        cid=lines[r['order_line_id']]['customer_id'];first[cid]=min(first.get(cid,r['return_date']),r['return_date'])
    last=max(r['order_date'] for r in lines.values());start=min(r['order_date'] for r in lines.values())
    from collections import defaultdict
    by_customer=defaultdict(list)
    for line in lines.values(): by_customer[line['customer_id']].append(line)
    observations=[]
    for cid,event in sorted(first.items()):
        anchor=date.fromisoformat(event)+timedelta(days=q['lag_days']);before=anchor-timedelta(days=q['followup_days']);end=anchor+timedelta(days=q['followup_days'])
        if before.isoformat()<start or end.isoformat()>last: continue
        pre=sum(l['net_sales_cents'] for l in by_customer[cid] if before.isoformat()<=l['order_date']<anchor.isoformat())
        post=sum(l['net_sales_cents'] for l in by_customer[cid] if anchor.isoformat()<=l['order_date']<end.isoformat())
        observations.append(dict(customer_id=cid,first_return=event,window_start=before.isoformat(),response_window_start=anchor.isoformat(),window_end_exclusive=end.isoformat(),before_revenue_cents=pre,after_revenue_cents=post))
    count=len(events);rate=count/len(targeted) if targeted else 0
    return {'basis':'Observed equal-window account revenue before returns, not causal effects. Return cost is separate and must not be added to account revenue decline.',
        'target_lines':len(targeted),'reliability_return_lines':count,'return_line_rate':rate,
        'refund_cents':sum(r['refund_cents'] for r in events),'net_return_cost_cents':sum(r['net_return_cost_cents'] for r in events),
        'observations':observations,'checks':{
            'quality_return_evidence':count>=q['minimum_return_lines'],
            'quality_rate_in_bounds':.25<=rate<=.65,
            'quality_followup_declines':sum(o['after_revenue_cents']<o['before_revenue_cents'] for o in observations)>=q['minimum_responding_accounts'],
            'quality_healthy_exposed_accounts':any(o['after_revenue_cents']>=o['before_revenue_cents'] for o in observations),
            'quality_support_evidence':sum(a['reason_code']=='Product reliability inquiry' for a in t['account_activity'])==count}}
