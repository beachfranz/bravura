"""Authoring-only, observed cohort bridges; no causal or confirmed churn claims."""
from collections import defaultdict


def audit(tables):
    customers = {r['customer_id']: r for r in tables['customers']}
    periods = {'CY2024': ('2024-01-01','2024-12-31'), 'CY2025': ('2025-01-01','2025-12-31'),
               'H12025': ('2025-01-01','2025-06-30'), 'H12026': ('2026-01-01','2026-06-30')}
    amounts = {}
    for label,(start,end) in periods.items():
        a = defaultdict(lambda: [0,0])
        for r in tables['order_lines']:
            if start <= r['order_date'] <= end:
                a[r['customer_id']][0] += r['net_sales_cents']
                a[r['customer_id']][1] += r['contribution_cents']
        amounts[label] = dict(a)
    report = {'basis': 'Observed comparable calendar periods; USD cents before returns; inactive is not confirmed churn.', 'periods': {}, 'bridges': {}}
    for label,a in amounts.items():
        sales = sum(v[0] for v in a.values()); contribution = sum(v[1] for v in a.values())
        top = sorted(a, key=lambda k: (-a[k][0], k))[:10]
        parents = defaultdict(int)
        for cid,v in a.items(): parents[customers[cid]['parent_id']] += v[0]
        report['periods'][label] = dict(accounts=len(a),revenue=sales,contribution=contribution,
            contribution_margin=contribution/sales,top10_share=sum(a[k][0] for k in top)/sales,
            top10_accounts=top,parent_top10_share=sum(sorted(parents.values(),reverse=True)[:10])/sales)
    for old,new in [('CY2024','CY2025'),('H12025','H12026')]:
        a,b=amounts[old],amounts[new]; cohorts=defaultdict(lambda:dict(accounts=0,revenue_delta=0,contribution_delta=0,current_revenue=0,current_contribution=0))
        for cid in set(a)|set(b):
            av,bv=a.get(cid,[0,0]),b.get(cid,[0,0])
            cohort = ('newly_acquired' if customers[cid]['acquisition_date'] >= periods[new][0] else 'returning_or_outside_prior_window') if cid not in a else ('inactive' if cid not in b else ('retained_declining' if bv[0]<av[0] else 'retained_growing'))
            c=cohorts[cohort]; c['accounts']+=1
            c['revenue_delta']+=bv[0]-av[0];c['contribution_delta']+=bv[1]-av[1]
            c['current_revenue']+=bv[0];c['current_contribution']+=bv[1]
        for metric,index in [('revenue',0),('contribution',1)]:
            assert sum(c[metric+'_delta'] for c in cohorts.values()) == sum(v[index] for v in b.values())-sum(v[index] for v in a.values())
        report['bridges'][old+'_'+new]=dict(cohorts)
    h=report['periods']; bridge=report['bridges']['H12025_H12026']
    checks = {
        'growth_with_profit_decline': h['H12026']['revenue']>h['H12025']['revenue'] and h['H12026']['contribution']<h['H12025']['contribution'],
        'material_concentration': .25 <= h['H12026']['top10_share'] <= .65,
        'rising_concentration': h['H12026']['top10_share']>h['H12025']['top10_share'],
        'new_customers': bridge.get('newly_acquired',{}).get('accounts',0)>=10,
        'inactive_customers': bridge.get('inactive',{}).get('accounts',0)>=10,
        'large_account_deterioration': bool(set(h['CY2024']['top10_accounts']) & {cid for cid in amounts['CY2024'] if amounts['CY2025'].get(cid,[0])[0]<amounts['CY2024'][cid][0]}),
        'new_cohort_weaker_margin': (bridge.get('newly_acquired',{}).get('current_contribution',0)/max(1,bridge.get('newly_acquired',{}).get('current_revenue',0))) < h['H12026']['contribution_margin'],
    }
    report['checks']=checks
    return report
