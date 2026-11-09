"""Local, credential-free finance exploration. Launch: python -m streamlit run app.py."""
import json
import pandas as pd
import streamlit as st
from src.lab import ROOT, CFG, forecast, end
st.set_page_config(page_title='Growth vs Cash',layout='wide')
st.title('Growth vs Cash — CedarCloud Workflow')
st.caption('Fictional company • synthetic GBP • September 2026 reporting cutoff')
@st.cache_data
def load(name): return pd.read_csv(ROOT/'outputs'/name)
try: m=load('monthly_actuals.csv')
except FileNotFoundError:
    st.error('Run python -m src.build first.'); st.stop()
page=st.sidebar.radio('Investigation',['Financial overview','Cash versus profit','Reconciliation exceptions','Budget and forecast','Scenario decisions'])
if page=='Financial overview':
    last=m.iloc[-1]; a,b,c=st.columns(3)
    a.metric('Monthly revenue GBP',f'{last.revenue_pence/100:,.0f}'); b.metric('Operating profit GBP',f'{last.profit_pence/100:,.0f}'); c.metric('Cash GBP',f'{last.cash_pence/100:,.0f}')
    st.line_chart(m.set_index('month')[['revenue_pence','cost_pence']]/100); st.dataframe(m)
elif page=='Cash versus profit':
    st.write('Profit − increase in AR + increase in deferred revenue + increase in AP = cash movement.')
    st.line_chart(m.set_index('month')[['cash_pence','ar_pence','deferred_pence']]/100)
    st.dataframe(m[['month','profit_pence','cash_bridge_pence','cash_change_pence','ar_check_pence','deferred_check_pence']])
    st.subheader('Customer collection priorities'); st.dataframe(load('customer_ar.csv').sort_values('overdue_pence',ascending=False).head(30))
    st.subheader('Gross service revenue by tier'); st.dataframe(load('revenue_by_tier.csv'))
elif page=='Reconciliation exceptions':
    st.write('Controlled test-copy exceptions. Exposure can overlap; overdue invoices are separate business risks.')
    st.dataframe(load('exceptions.csv')); st.subheader('Evidence restoration audit trail'); st.dataframe(load('repair_log.csv'))
elif page=='Budget and forecast':
    st.warning('The monthly driver model underperformed the naive baseline on the three-month holdout. Treat projections as sensitivity analysis; validate collections before committing cash.')
    st.subheader('Original fixed budget versus actual'); st.dataframe(load('budget_comparison.csv'))
    st.subheader('13-week cash schedule GBP'); st.line_chart(load('forecast_13w.csv').set_index('week_start')[['cash_pence']]/100)
    st.dataframe(load('forecast_13w.csv')); st.subheader('12-month forecast'); st.dataframe(load('forecast_12m.csv'))
    st.subheader('Three-month holdout, no claim beyond observed horizon'); st.dataframe(load('holdout_metrics.csv'))
else:
    st.warning('Forecast accuracy is weak on the observed holdout. These conditional projections do not establish affordability.')
    threshold=st.number_input('Minimum cash GBP',min_value=0,value=200000,step=10000)
    collection=st.slider('Collection fraction uplift (percentage points)',-20,30,15)/100
    price=st.slider('Renewal price uplift (%)',0,15,5)/100
    cut=st.slider('Marketing reduction (%)',0,40,20)/100
    delay=st.slider('Delay before five hires (months)',0,12,6)
    launch=st.checkbox('Launch in first month (GBP 90,000)',value=True)
    tables={name:pd.read_csv(ROOT/'data/reconciled'/f'{name}.csv',keep_default_na=False) for name in ['invoices','payments','subscriptions','expenses','journal']}
    f=forecast(tables,end(m.iloc[-1].month),collection=collection,price=price,expense_cut=cut,hire_delay=delay,launch=launch)
    st.metric('Projected minimum cash GBP',f'{f.cash_pence.min()/100:,.0f}')
    if f.cash_pence.min()<threshold*100: st.warning('Cash policy breached: revise commitments or secure funding before approval.')
    else: st.success('Cash stays above the selected threshold under these assumptions. Review commercial trade-offs before committing.')
    st.write('Collections change cash timing, not revenue. Price and marketing changes have no estimated demand response. Hiring productivity is unmodelled.')
    st.line_chart(f.set_index('month')[['cash_pence']]/100); st.dataframe(f)
    st.subheader('Fixed intervention comparison'); st.dataframe(load('scenarios.csv'))
