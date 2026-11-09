"""CedarCloud finance engine. Money is signed integer GBP pence throughout."""
from pathlib import Path
import json, random, sqlite3, hashlib
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT/'config/assumptions.json').read_text())
def month(d, n=0): return (pd.Timestamp(d).to_period('M')+n).start_time.strftime('%Y-%m-%d')
def end(d): return pd.Timestamp(d).to_period('M').end_time.strftime('%Y-%m-%d')
def save(d, path):
    pd.DataFrame(d).to_csv(ROOT/path,index=False)
def generate(c=CFG):
    rng=random.Random(c['seed']); cutoff=end(month(c['start'],c['months']-1))
    customers=[]; subs=[]; inv=[]; pay=[]; rev=[]; expenses=[]; bank=[]; journals=[]
    def journal(date,ref,dr,cr,amount):
        journals.extend([dict(date=date,ref=ref,account=dr,signed_pence=int(amount)),dict(date=date,ref=ref,account=cr,signed_pence=-int(amount))])
    journal(c['start'],'OPEN','Cash','Equity',c['opening_cash_pence'])
    for i in range(c['customers']):
        start=month(c['start'],0 if i<230 else 1+(i-230)//14)
        tier=rng.choices([0,1,2],[.5,.35,.15])[0]; annual=rng.random()<c['annual_share']
        duration=12 if annual else 1; price=c['monthly_prices_pence'][tier]
        fee=price*duration if not annual else price*108//10
        cancel=None
        for k in range(1,36):
            if rng.random()<c['monthly_churn'] and (not annual or k%12==0): cancel=month(start,k); break
        cid=f'C{i:04}'; sid=f'S{i:04}'
        customers.append(dict(customer_id=cid,name=f'Customer {i:04}',acquired=start,segment='Enterprise' if tier==2 else 'SMB'))
        subs.append(dict(subscription_id=sid,customer_id=cid,tier=['Starter','Team','Scale'][tier],start=start,cancel=cancel or '',term_months=duration,fee_pence=fee,mrr_pence=fee//duration))
        for k in range(0,c['months']+12,duration):
            date=month(start,k)
            if date>cutoff or (cancel and date>=cancel): break
            iid=f'I{len(inv):06}'; due=(pd.Timestamp(date)+pd.Timedelta(days=30)).strftime('%Y-%m-%d')
            inv.append(dict(invoice_id=iid,subscription_id=sid,customer_id=cid,date=date,due=due,service_end=month(date,duration),amount_pence=fee))
            journal(date,iid,'AR','Deferred',fee)
            for j in range(duration):
                rd=month(date,j)
                if rd<=cutoff:
                    amount=fee//duration + (fee%duration if j==duration-1 else 0)
                    rev.append(dict(invoice_id=iid,subscription_id=sid,customer_id=cid,tier=subs[-1]['tier'],date=rd,amount_pence=amount))
                    journal(rd,iid,'Deferred','Revenue',amount)
            slow=40 if date>='2026-04-01' else 8
            delay=rng.choice([slow,slow+15,slow+40,120])
            if rng.random()<.18:
                pay.append(dict(payment_id=f'P{len(pay):06}',invoice_id=iid,date=(pd.Timestamp(date)+pd.Timedelta(days=3)).strftime('%Y-%m-%d'),status='failed',amount_pence=fee))
            pdte=(pd.Timestamp(date)+pd.Timedelta(days=delay)).strftime('%Y-%m-%d')
            if pdte<=cutoff and rng.random()>.035:
                pid=f'P{len(pay):06}'
                pay.append(dict(payment_id=pid,invoice_id=iid,date=pdte,status='successful',amount_pence=fee))
                bank.append(dict(bank_id=f'B{len(bank):06}',ref=pid,date=pdte,signed_pence=fee))
                journal(pdte,pid,'Cash','AR',fee)
                # Service credit after delivery: contra revenue and cash, no AR reopening.
                if rng.random()<.008:
                    rid=f'P{len(pay):06}'; amount=fee//20
                    pay.append(dict(payment_id=rid,invoice_id=iid,date=pdte,status='refund',amount_pence=amount))
                    bank.append(dict(bank_id=f'B{len(bank):06}',ref=rid,date=pdte,signed_pence=-amount))
                    journal(pdte,rid,'Revenue','Cash',amount)
    for k in range(c['months']):
        date=month(c['start'],k)
        active=sum(s['start']<=date and (not s['cancel'] or date<s['cancel']) for s in subs)
        costs={'Payroll':8000000+min(k,15)*250000,'Cloud':active*6500,'Marketing':2200000+k*60000,'Rent':900000,'Supplier':600000}
        for cat,amount in costs.items():
            eid=f'E{len(expenses):04}'; payment=(pd.Timestamp(date)+pd.Timedelta(days=24 if cat!='Supplier' else 40)).strftime('%Y-%m-%d')
            expenses.append(dict(expense_id=eid,category=cat,date=date,payment_date=payment,amount_pence=amount))
            journal(date,eid,cat,'AP',amount)
            if payment<=cutoff:
                bank.append(dict(bank_id=f'B{len(bank):06}',ref=eid,date=payment,signed_pence=-amount)); journal(payment,eid,'AP','Cash',amount)
    return {k:pd.DataFrame(v) for k,v in dict(customers=customers,subscriptions=subs,invoices=inv,payments=pay,revenue=rev,expenses=expenses,bank=bank,journal=journals).items()}

def controls(t):
    """Only operational exports and bank evidence enter detection; no inserted truth."""
    issues=[]
    def add(table,key,issue,amount,status='Investigate'):
        issues.append(dict(table=table,record=str(key),issue=issue,exposure_pence=abs(int(amount)),action='Quarantine duplicate; otherwise verify against signed invoice or bank evidence',resolution=status))
    for table,key in [('invoices','invoice_id'),('payments','payment_id')]:
        for _,r in t[table][t[table].duplicated(key)].iterrows(): add(table,r[key],'duplicate',r.amount_pence,'Confirmed duplicate')
    inv=t['invoices'].drop_duplicates('invoice_id'); payments=t['payments'].drop_duplicates('payment_id')
    for _,r in inv.iterrows():
        sub=t['subscriptions'][t['subscriptions'].subscription_id==r.subscription_id]
        if sub.empty or r.customer_id not in set(t['customers'].customer_id) or (not sub.empty and sub.iloc[0].customer_id!=r.customer_id): add('invoices',r.invoice_id,'relationship',r.amount_pence)
        if r.date>=r.service_end: add('invoices',r.invoice_id,'period',r.amount_pence)
    refs=set(payments.loc[payments.status.isin(['successful','refund']),'payment_id'])|set(t['expenses'].expense_id)
    for _,r in t['bank'].iterrows():
        if r.ref not in refs: add('bank',r.bank_id,'unmatched',r.signed_pence)
    receipts=payments[payments.status=='successful']
    for _,r in receipts.iterrows():
        b=t['bank'][t['bank'].ref==r.payment_id]
        if len(b)!=1 or (not b.empty and (b.iloc[0].date!=r.date or b.iloc[0].signed_pence!=r.amount_pence)): add('payments',r.payment_id,'bank_mismatch',r.amount_pence)
        if r.invoice_id not in set(inv.invoice_id): add('payments',r.payment_id,'missing_invoice',r.amount_pence)
    return pd.DataFrame(issues,columns=['table','record','issue','exposure_pence','action','resolution'])

def monthly(t,c=CFG):
    rows=[]; prev={'Cash':c['opening_cash_pence'],'AR':0,'Deferred':0,'AP':0}
    for k in range(c['months']):
        d=month(c['start'],k); e=end(d); j=t['journal']; balances=j[j.date<=e].groupby('account').signed_pence.sum()
        jm=j[(j.date>=d)&(j.date<=e)].groupby('account').signed_pence.sum()
        cash=int(balances.get('Cash',0)); ar=int(balances.get('AR',0)); deferred=-int(balances.get('Deferred',0)); ap=-int(balances.get('AP',0))
        revenue=-int(jm.get('Revenue',0)); cost=int(sum(jm.get(a,0) for a in ['Payroll','Cloud','Marketing','Rent','Supplier']))
        b=t['bank']; bm=b[(b.date>=d)&(b.date<=e)]
        invoices=t['invoices']; payments=t['payments']; billed=invoices[(invoices.date>=d)&(invoices.date<=e)].amount_pence.sum()
        receipts=payments[(payments.date>=d)&(payments.date<=e)&(payments.status=='successful')].amount_pence.sum()
        refunds=payments[(payments.date>=d)&(payments.date<=e)&(payments.status=='refund')].amount_pence.sum()
        paid=payments[(payments.date<=e)&(payments.status=='successful')].groupby('invoice_id').amount_pence.sum()
        overdue=sum(max(0,int(r.amount_pence)-int(paid.get(r.invoice_id,0))) for r in invoices[invoices.due<e].itertuples())
        s=t['subscriptions']; active=s[(s.start<=d)&((s.cancel=='')|(s.cancel>d))]
        opening=s[(s.start<d)&((s.cancel=='')|(s.cancel>=d))]
        cancelled=len(s[(s.cancel>=d)&(s.cancel<=e)])
        profit=revenue-cost; bridge=profit-(ar-prev['AR'])+(deferred-prev['Deferred'])+(ap-prev['AP'])
        rows.append(dict(month=d,revenue_pence=revenue,cost_pence=cost,profit_pence=profit,margin=profit/revenue if revenue else None,invoiced_pence=int(billed),receipts_pence=int(receipts),refunds_pence=int(refunds),payments_pence=int(-bm[bm.signed_pence<0].signed_pence.sum()),cash_pence=cash,ar_pence=ar,overdue_pence=overdue,deferred_pence=deferred,ap_pence=ap,active_customers=len(active),mrr_pence=int(active.mrr_pence.sum()),churn=cancelled/len(opening) if len(opening) else None,collections_rate=int(receipts)/int(billed) if billed else None,cash_bridge_pence=int(bridge),cash_change_pence=cash-prev['Cash'],ar_check_pence=ar-prev['AR']-int(billed)+int(receipts),deferred_check_pence=deferred-prev['Deferred']-int(billed)+revenue+int(refunds)))
        prev={'Cash':cash,'AR':ar,'Deferred':deferred,'AP':ap}
    return pd.DataFrame(rows)

def forecast(t,cutoff,months=12,price=0,collection=.0,expense_cut=.0,hire_delay=99,launch=False,growth=None,c=CFG):
    """Snapshot filtering precedes calibration. No future status or receipt is consulted."""
    observed=t['invoices'][t['invoices'].date<=cutoff]
    known=t['payments'][(t['payments'].date<=cutoff)&(t['payments'].status=='successful')]
    s=t['subscriptions']; active=s[(s.start<=cutoff)&((s.cancel=='')|(s.cancel>cutoff))]
    # Future cancellation fields never influence projection; only already-cancelled rows excluded.
    past_cancel=s[(s.cancel!='')&(s.cancel<=cutoff)&(s.cancel>=month(cutoff,-5))]
    churn=len(past_cancel)/max(1,len(active)*6)
    adds=len(s[(s.start>=month(cutoff,-5))&(s.start<=cutoff)])/6 if growth is None else growth
    avg=active.mrr_pence.mean(); avg=0 if pd.isna(avg) else float(avg)
    paid=known.groupby('invoice_id').amount_pence.sum()
    ar=sum(max(0,int(r.amount_pence)-int(paid.get(r.invoice_id,0))) for r in observed.itertuples())
    j=t['journal'][t['journal'].date<=cutoff]; cash=int(j.loc[j.account=='Cash','signed_pence'].sum())
    recent=t['expenses'][(t['expenses'].date>=month(cutoff,-2))&(t['expenses'].date<=cutoff)]
    costs=recent.groupby('category').amount_pence.mean().to_dict(); count=float(len(active)); rows=[]
    # Steady billing proxy calibrated only from last three complete observed months.
    recent_inv=observed[observed.date>=month(cutoff,-2)].amount_pence.sum()/3
    recent_rec=known[known.date>=month(cutoff,-2)].amount_pence.sum()/3
    ratio=min(1.0,recent_rec/max(1,recent_inv)); ratio=min(1,ratio+collection)
    for k in range(1,months+1):
        d=month(cutoff,k); count=count*(1-churn)+adds
        revenue=round(count*avg*(1+price*min(1,k/12)))
        billed=round(recent_inv*count/max(1,len(active))*(1+price*min(1,k/12)))
        collected=round((ar+billed)*ratio); ar=ar+billed-collected
        cost=round(sum(costs.values())+max(0,count-len(active))*6500-costs.get('Marketing',0)*expense_cut)
        if k>hire_delay: cost+=c['proposed_hires']*c['hire_monthly_cost_pence']
        if launch and k==1: cost+=c['launch_cost_pence']
        cash+=collected-cost
        rows.append(dict(month=d,revenue_pence=revenue,cost_pence=cost,profit_pence=revenue-cost,receipts_pence=collected,payments_pence=cost,cash_pence=cash,ar_pence=ar,customers=count))
    return pd.DataFrame(rows)

SCENARIOS={'Base':{},'Upside':{'growth':18,'collection':.12},'Downside':{'growth':5,'collection':-.15},'Hire now + launch':{'hire_delay':0,'launch':True},'Delay hires 6 months':{'hire_delay':6,'launch':True},'Collections':{'collection':.15},'Price +5%':{'price':.05},'Marketing -20%':{'expense_cut':.2},'Combined staged':{'collection':.15,'price':.05,'expense_cut':.2,'hire_delay':6,'launch':True}}

def weekly(t,cutoff,c=CFG,collection_days=35):
    """Invoice maturity schedule plus recurring billing; 13 consecutive seven-day windows."""
    inv=t['invoices'][t['invoices'].date<=cutoff]; p=t['payments'][(t['payments'].date<=cutoff)&(t['payments'].status=='successful')].groupby('invoice_id').amount_pence.sum()
    events=[]
    for r in inv.itertuples():
        balance=int(r.amount_pence)-int(p.get(r.invoice_id,0))
        if balance>0: events.append((max(pd.Timestamp(cutoff)+pd.Timedelta(days=7),pd.Timestamp(r.due)+pd.Timedelta(days=collection_days)),round(balance*.95),'AR'))
    s=t['subscriptions']; active=s[(s.start<=cutoff)&((s.cancel=='')|(s.cancel>cutoff))]
    for k in range(1,5):
        d=month(cutoff,k)
        for r in active.itertuples():
            age=(pd.Timestamp(d).year-pd.Timestamp(r.start).year)*12+pd.Timestamp(d).month-pd.Timestamp(r.start).month
            if age%r.term_months==0: events.append((pd.Timestamp(d)+pd.Timedelta(days=collection_days),round(r.fee_pence*.95),'New billing'))
    exp=t['expenses']; recent=exp[(exp.date>=month(cutoff,-2))&(exp.date<=cutoff)].groupby('category').amount_pence.mean()
    for r in exp[(exp.date<=cutoff)&(exp.payment_date>cutoff)].itertuples(): events.append((pd.Timestamp(r.payment_date),-int(r.amount_pence),'AP'))
    for k in range(1,5):
        for cat,amt in recent.items(): events.append((pd.Timestamp(month(cutoff,k))+pd.Timedelta(days=40 if cat=='Supplier' else 24),-round(amt),cat))
    j=t['journal']; cash=int(j[(j.date<=cutoff)&(j.account=='Cash')].signed_pence.sum()); rows=[]
    for w in range(13):
        start=pd.Timestamp(cutoff)+pd.Timedelta(days=1+w*7); stop=start+pd.Timedelta(days=7)
        vals=[a for d,a,_ in events if start<=d<stop]; receipts=sum(a for a in vals if a>0); payments=-sum(a for a in vals if a<0); cash+=receipts-payments
        rows.append(dict(week_start=str(start.date()),receipts_pence=receipts,payments_pence=payments,cash_pence=cash,breach=cash<c['minimum_cash_pence']))
    return pd.DataFrame(rows)
