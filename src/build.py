"""Run with python -m src.build. All reporting is generated from saved evidence."""
import json, hashlib, sqlite3, shutil
from pathlib import Path
import numpy as np
import pandas as pd
import xlsxwriter
from .lab import *
from .source_audit import run as source_run

def source_checks(t):
    s=t['subscriptions']; i=t['invoices']; p=t['payments']; success=p[p.status=='successful'].groupby('invoice_id').amount.sum()
    result={'currency':'Unspecified; never assigned GBP','counts':{k:len(v) for k,v in t.items()},'cancellation_before_start':int((s.cancellation_date.fillna('9999')<s.start_date).sum()),'renewal_before_start':int((s.renewal_date<s.start_date).sum()),'invoice_before_subscription':int((i.merge(s,left_on='subscription_id',right_on='id',suffixes=('_invoice','_sub')).issue_date<i.merge(s,left_on='subscription_id',right_on='id',suffixes=('_invoice','_sub')).start_date).sum()),'successful_amount_mismatch':int(sum(abs(float(r.amount)-float(success.get(r.id,0)))>.01 for r in i.itertuples())), 'failed_or_other_attempts':int((p.status!='successful').sum())}
    for child,fk,parent in [('subscriptions','customer_id','customers'),('subscriptions','plan_id','plans'),('invoices','subscription_id','subscriptions'),('payments','invoice_id','invoices')]: result[f'{child}_{fk}_orphans']=int((~t[child][fk].isin(t[parent].id)).sum())
    joined=p.merge(i,left_on='invoice_id',right_on='id',suffixes=('_payment','_invoice'))
    result['payment_before_invoice']=int((joined.payment_date.str[:10]<joined.issue_date).sum())
    (ROOT/'data/source/audit.json').write_text(json.dumps(result,indent=2)); return result

def corrupt(t):
    dirty={k:v.copy(deep=True) for k,v in t.items()}; truth=[]
    def record(table,record,issue): truth.append(dict(table=table,record=record,issue=issue))
    for table,key in [('invoices','invoice_id'),('payments','payment_id')]:
        dirty[table]=pd.concat([dirty[table],dirty[table].iloc[[0]]],ignore_index=True); record(table,str(dirty[table].iloc[0][key]),'duplicate')
    for idx,field,value,issue in [(1,'customer_id','C_UNKNOWN','relationship'),(2,'date','2029-01-01','period')]:
        dirty['invoices'].loc[idx,field]=value; record('invoices',t['invoices'].iloc[idx].invoice_id,issue)
    dirty['bank'].loc[0,'ref']=''; record('bank',t['bank'].iloc[0].bank_id,'unmatched')
    pid=t['bank'].iloc[0].ref; record('payments',pid,'bank_mismatch')
    idx=dirty['payments'].index[dirty['payments'].status=='successful'][1]
    dirty['payments'].loc[idx,'date']='2026-09-30'; record('payments',dirty['payments'].loc[idx,'payment_id'],'bank_mismatch')
    dirty['bank']=pd.concat([dirty['bank'],pd.DataFrame([dict(bank_id='B_UNKNOWN',ref='UNKNOWN',date='2026-09-30',signed_pence=123450)])],ignore_index=True); record('bank','B_UNKNOWN','unmatched')
    save(truth,'data/truth/inserted_errors.csv')
    return dirty,pd.DataFrame(truth)

def excel(m,budget,f,w,sc,checks):
    path=ROOT/'outputs/finance_model.xlsx'; book=xlsxwriter.Workbook(path)
    book.set_properties({'title':'Growth vs Cash — CedarCloud Workflow','comments':'Synthetic GBP simulation; engine snapshots plus live formulas. Rebuild to refresh scenarios.'})
    header=book.add_format({'bold':True,'bg_color':'#183D48','font_color':'white','text_wrap':True})
    money=book.add_format({'num_format':'#,##0.00;[Red](#,##0.00)','font_name':'Arial','font_size':10})
    inp=book.add_format({'font_color':'blue','num_format':'#,##0.00'})
    title=book.add_format({'bold':True,'font_size':14,'font_name':'Arial'})
    for name,df in [('Actuals',m),('Budget',budget),('Forecast',f),('13 weeks',w),('Scenarios',sc),('Checks',pd.DataFrame([checks]))]:
        sheet=book.add_worksheet(name); sheet.hide_gridlines(2); sheet.write(1,0,name+' | GBP (pence columns converted to pounds)',title)
        sheet.freeze_panes(4,1); sheet.set_row(3,42); sheet.set_column(0,len(df.columns)-1,20)
        for col,k in enumerate(df.columns):
            sheet.write(3,col,k.replace('_pence',' GBP'),header)
            for row,v in enumerate(df[k],4):
                if pd.isna(v): sheet.write_blank(row,col,None)
                elif isinstance(v,(int,float,np.integer,np.floating)): sheet.write_number(row,col,float(v)/100 if k.endswith('_pence') else float(v),money)
                else: sheet.write(row,col,str(v))
        sheet.autofilter(3,0,3+len(df),len(df.columns)-1)
    a=book.add_worksheet('Assumptions'); a.set_column('A:A',42); a.set_column('B:B',24); a.write_row(0,0,['Live review inputs','Value'],header)
    for r,(label,val) in enumerate([('Minimum cash GBP',CFG['minimum_cash_pence']/100),('Additional hires',5),('Monthly cost per hire GBP',5500),('Launch cost GBP',90000),('Source','config/assumptions.json; synthetic')],1): a.write(r,0,label); a.write(r,1,val,inp if isinstance(val,(int,float)) else None)
    a.write(7,0,'Monthly incremental payroll GBP'); a.write_formula(7,1,'=B3*B4',money,27500)
    a.write(9,0,'Scenario snapshots refresh via Python rebuild')
    # Independently trace and verify useful live formulas, with valid cached engine values.
    x=book.add_worksheet('Review'); x.set_column('A:A',25); x.set_column('B:E',24); x.write_row(0,0,['Month','Profit GBP','Cash bridge GBP','Cash threshold gap GBP'],header)
    for r in range(len(m)):
        er=r+5; rr=r+1
        x.write(rr,0,m.iloc[r]['month']); x.write_formula(rr,1,f"=Actuals!B{er}-Actuals!C{er}",money,float(m.iloc[r].profit_pence)/100)
        x.write_formula(rr,2,f"=Actuals!S{er}-Actuals!T{er}",money,0)
        x.write_formula(rr,3,f"=Actuals!J{er}-Assumptions!$B$2",money,(float(m.iloc[r].cash_pence)-CFG['minimum_cash_pence'])/100)
    chart=book.add_chart({'type':'line'}); chart.add_series({'name':'Cash GBP','categories':['Actuals',4,0,3+len(m),0],'values':['Actuals',4,9,3+len(m),9]}); chart.set_title({'name':'Closing cash'}); x.insert_chart('F2',chart)
    book.close()
    # XML-level checks verify cached formula values and exact engine snapshots without claiming native Excel recalculation.
    from zipfile import ZipFile
    from xml.etree import ElementTree as ET
    with ZipFile(path) as z:
        ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        cells=ET.fromstring(z.read('xl/worksheets/sheet1.xml')).findall('.//s:c',ns)
        values={v.attrib['r']:v.find('s:v',ns).text for v in cells if v.find('s:v',ns) is not None}
        assert all(abs(float(values[f'J{r+5}'])-m.iloc[r].cash_pence/100)<1e-7 for r in range(len(m)))
    return path

def build():
    audit=source_checks(source_run(ROOT)); t=generate()
    for k,d in t.items(): save(d,f'data/exports/{k}.csv'); save(d,f'data/truth/{k}.csv')
    dirty,truth=corrupt(t)
    for k,d in dirty.items(): save(d,f'data/corrupted/{k}.csv')
    exceptions=controls(dirty); save(exceptions,'outputs/exceptions.csv')
    keys=['table','record','issue']; expected=set(map(tuple,truth[keys].values)); detected=set(map(tuple,exceptions[keys].values)); tp=len(expected&detected)
    clean_exceptions=controls(t); save(clean_exceptions,'outputs/clean_exceptions.csv')
    # Repairs use preserved export evidence, never inserted-error truth. Every changed table is logged.
    repairs=[]
    for k in t:
        save(t[k],f'data/reconciled/{k}.csv')
        if not dirty[k].equals(t[k]): repairs.append(dict(table=k,action='Restore quarantined rows from immutable operational export',evidence=f'data/exports/{k}.csv',before_sha256=hashlib.sha256(dirty[k].to_csv(index=False).encode()).hexdigest(),after_sha256=hashlib.sha256(t[k].to_csv(index=False).encode()).hexdigest(),approval='Simulated finance review; no real stakeholder approval'))
    save(repairs,'outputs/repair_log.csv'); m=monthly(t); save(m,'outputs/monthly_actuals.csv')
    budget=pd.DataFrame([dict(month=month(CFG['start'],k),revenue_budget_pence=round((230+12*k)*32000),cost_budget_pence=15000000+250000*k,frozen=CFG['budget_frozen']) for k in range(CFG['months'])])
    bv=m[['month','revenue_pence','cost_pence']].merge(budget,on='month'); bv['revenue_variance_pence']=bv.revenue_pence-bv.revenue_budget_pence; bv['cost_variance_pence']=bv.cost_pence-bv.cost_budget_pence
    bv['revenue_variance_pct']=bv.revenue_variance_pence/bv.revenue_budget_pence.replace(0,np.nan); bv['cost_variance_pct']=bv.cost_variance_pence/bv.cost_budget_pence.replace(0,np.nan)
    save(bv,'outputs/budget_comparison.csv'); cutoff=end(m.iloc[-1].month)
    scenarios=[]
    for name,kwargs in SCENARIOS.items():
        f=forecast(t,cutoff,**kwargs); save(f,f'outputs/scenario_{name.replace(" ","_").replace("+","plus").replace("%","pct")}.csv')
        scenarios.append(dict(scenario=name,min_cash_pence=int(f.cash_pence.min()),closing_cash_pence=int(f.iloc[-1].cash_pence),profit_pence=int(f.profit_pence.sum()),breach=bool(f.cash_pence.min()<CFG['minimum_cash_pence']),assumptions=json.dumps(kwargs)))
    sc=pd.DataFrame(scenarios); save(sc,'outputs/scenarios.csv'); f=forecast(t,cutoff); save(f,'outputs/forecast_12m.csv'); w=weekly(t,cutoff); save(w,'outputs/forecast_13w.csv')
    hold=forecast(t,CFG['holdout_cutoff'],3); actual=m[m.month>CFG['holdout_cutoff']].reset_index(drop=True); metrics=[]; evidence=[]
    last=m[m.month<=CFG['holdout_cutoff']].iloc[-1]
    for metric in ['revenue_pence','receipts_pence','cash_pence']:
        for model in ['driver','naive']:
            y=actual[metric].to_numpy(); pred=hold[metric].to_numpy() if model=='driver' else np.repeat(last[metric],len(y)); err=pred-y
            metrics.append(dict(metric=metric,model=model,mae_pence=float(np.abs(err).mean()),bias_pence=float(err.mean()),wape=float(np.abs(err).sum()/np.abs(y).sum()) if np.abs(y).sum() else None))
            for d,a,p in zip(actual.month,y,pred): evidence.append(dict(month=d,metric=metric,model=model,actual_pence=int(a),forecast_pence=int(p),cutoff=CFG['holdout_cutoff']))
    save(metrics,'outputs/holdout_metrics.csv'); save(evidence,'outputs/holdout_predictions.csv')
    j=t['journal']; trial=j.groupby('account',as_index=False).signed_pence.sum(); save(trial,'outputs/trial_balance.csv')
    checks=dict(journal_imbalance_pence=int(j.groupby(['date','ref']).signed_pence.sum().abs().max()),trial_balance_pence=int(trial.signed_pence.sum()),ar_rollforward_max_pence=int(m.ar_check_pence.abs().max()),deferred_rollforward_max_pence=int(m.deferred_check_pence.abs().max()),profit_cash_bridge_max_pence=int((m.cash_bridge_pence-m.cash_change_pence).abs().max()),clean_exceptions=len(clean_exceptions),inserted_issues=len(expected),detected_issues=len(detected),true_positives=tp,precision=tp/len(detected) if detected else None,recall=tp/len(expected),excel_snapshot_checked=True)
    assert all(checks[k]==0 for k in ['journal_imbalance_pence','trial_balance_pence','ar_rollforward_max_pence','deferred_rollforward_max_pence','profit_cash_bridge_max_pence','clean_exceptions'])
    excel(m,bv,f,w,sc,checks)
    with sqlite3.connect(ROOT/'outputs/finance.sqlite') as conn:
        for k,d in {**t,'monthly_actuals':m,'budget_comparison':bv,'scenarios':sc,'exceptions':exceptions}.items(): d.to_sql(k,conn,if_exists='replace',index=False)
        conn.executescript((ROOT/'powerbi/analysis.sql').read_text())
        drivers=pd.read_sql('SELECT * FROM revenue_by_tier',conn); save(drivers,'outputs/revenue_by_tier.csv')
        aging=pd.read_sql('SELECT * FROM customer_ar',conn); save(aging,'outputs/customer_ar.csv')
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(2,1,figsize=(12,7),layout='constrained'); dates=pd.to_datetime(m.month)
    for col,label in [('revenue_pence','Recognised revenue'),('cost_pence','Operating costs')]: ax[0].plot(dates,m[col]/100,label=label)
    ax[0].legend(); ax[0].set_ylabel('GBP / month'); ax[0].set_title('CedarCloud Workflow — synthetic management report')
    ax[1].plot(dates,m.cash_pence/100,label='Cash'); ax[1].plot(dates,m.ar_pence/100,label='Receivables'); ax[1].axhline(CFG['minimum_cash_pence']/100,color='red',linestyle='--',label='Minimum cash'); ax[1].legend(); ax[1].set_ylabel('GBP'); fig.savefig(ROOT/'outputs/overview.png',dpi=140); plt.close(fig)
    summary={'checks':checks,'source_audit':audit,'first_month':m.iloc[0].to_dict(),'last_month':m.iloc[-1].to_dict(),'scenarios':sc.to_dict('records'),'holdout_metrics':metrics,'weekly_min_cash_pence':int(w.cash_pence.min())}
    # Strict interoperable JSON: unavailable ratios are null, never NaN.
    summary=json.loads(pd.Series([summary]).to_json(orient='values'))[0]
    (ROOT/'outputs/results.json').write_text(json.dumps(summary,indent=2,allow_nan=False));
    from .documentation import write_docs
    write_docs(summary,t)
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ['data/exports','outputs'] for p in sorted((ROOT/folder).glob('*.csv'))}; (ROOT/'outputs/checksums.json').write_text(json.dumps(hashes,indent=2))
    print(json.dumps(checks,indent=2))

if __name__=='__main__': build()

