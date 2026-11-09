import json
import pandas as pd
import pytest
from src.lab import *
@pytest.fixture(scope='module')
def t(): return generate()

def test_balanced_books_and_independent_bank(t):
    j=t['journal']; assert j.groupby(['date','ref']).signed_pence.sum().eq(0).all()
    assert j.loc[j.account=='Cash','signed_pence'].sum()==CFG['opening_cash_pence']+t['bank'].signed_pence.sum()
    m=monthly(t)
    assert (m.cash_change_pence==m.cash_bridge_pence).all()
    assert m.ar_check_pence.eq(0).all() and m.deferred_check_pence.eq(0).all()

def test_annual_recognition_and_failed_attempts(t):
    annual=t['subscriptions'].query('term_months==12').iloc[0]
    invoice=t['invoices'][t['invoices'].subscription_id==annual.subscription_id].iloc[0]
    r=t['revenue'][t['revenue'].invoice_id==invoice.invoice_id]
    assert len(r)==12 and r.amount_pence.sum()==invoice.amount_pence
    assert (r.date<invoice.service_end).all()
    failed=t['payments'].query("status=='failed'")
    assert len(failed)>0 and not set(failed.payment_id)&set(t['bank'].ref)

def test_controls_and_duplicate_quarantine(t):
    assert controls(t).empty
    dirty={k:v.copy() for k,v in t.items()}
    for name,key in [('invoices','invoice_id'),('payments','payment_id')]:
        dirty[name]=pd.concat([dirty[name],dirty[name].iloc[[0]]])
    assert len(controls(dirty))==2
    for name,key in [('invoices','invoice_id'),('payments','payment_id')]: dirty[name]=dirty[name].drop_duplicates(key)
    pd.testing.assert_frame_equal(monthly(dirty),monthly(t))

def test_forecast_no_future_leakage(t):
    cutoff=CFG['holdout_cutoff']; original=forecast(t,cutoff,3)
    changed={k:v.copy() for k,v in t.items()}
    changed['payments'].loc[changed['payments'].date>cutoff,'amount_pence']=999999999
    changed['invoices'].loc[changed['invoices'].date>cutoff,'amount_pence']=999999999
    changed['expenses'].loc[changed['expenses'].date>cutoff,'amount_pence']=999999999
    changed['subscriptions'].loc[(changed['subscriptions'].cancel!='')&(changed['subscriptions'].cancel>cutoff),'cancel']=''
    pd.testing.assert_frame_equal(original,forecast(changed,cutoff,3))

def test_collection_is_timing_not_revenue(t):
    base=forecast(t,'2026-09-30'); fast=forecast(t,'2026-09-30',collection=.15)
    assert base.revenue_pence.equals(fast.revenue_pence)
    assert fast.cash_pence.min()>=base.cash_pence.min()
    hired=forecast(t,'2026-09-30',hire_delay=0)
    assert (base.profit_pence-hired.profit_pence).eq(5*550000).all()
    assert (base.cash_pence-hired.cash_pence).iloc[-1]==12*5*550000

def test_week_boundaries_and_cash(t):
    w=weekly(t,'2026-09-30'); assert len(w)==13
    assert pd.to_datetime(w.week_start).diff().dropna().eq(pd.Timedelta(days=7)).all()
    opening=monthly(t).iloc[-1].cash_pence
    assert w.iloc[-1].cash_pence==opening+w.receipts_pence.sum()-w.payments_pence.sum()

def test_app_workflows():
    from streamlit.testing.v1 import AppTest
    at=AppTest.from_file(str(ROOT/'app.py')).run(timeout=30)
    assert not at.exception
    for page in ['Cash versus profit','Reconciliation exceptions','Budget and forecast','Scenario decisions']:
        at.sidebar.radio[0].set_value(page).run(timeout=30); assert not at.exception
    at.slider[0].set_value(0).run(timeout=30); assert not at.exception

def test_saved_control_evaluation():
    r=json.loads((ROOT/'outputs/results.json').read_text())
    assert r['checks']['precision']==1 and r['checks']['recall']==1

def test_no_active_customers_and_no_receipts(t):
    zero={k:v.copy() for k,v in t.items()}
    zero['subscriptions']['start']='2029-01-01'
    zero['payments']=zero['payments'].iloc[:0]
    f=forecast(zero,'2026-09-30',3)
    assert f.revenue_pence.eq(0).all()
    assert not f.isna().any().any()

def test_overdue_not_a_data_error(t):
    m=monthly(t); assert m.overdue_pence.iloc[-1]>0
    assert controls(t).empty

def test_missing_reference_and_period_fault(t):
    changed={k:v.copy() for k,v in t.items()}
    changed['invoices'].loc[0,'customer_id']='MISSING'
    changed['invoices'].loc[1,'date']='2030-01-01'
    detected=controls(changed)
    assert {'relationship','period'}<=set(detected.issue)
