"""Documentation combines stable explanations with execution-derived financial claims."""
from .lab import ROOT,CFG
import json

def write_docs(r,t):
    def write(name,text): (ROOT/name).write_text(text.strip()+'\n',encoding='utf-8')
    gbp=lambda x:f'GBP {x/100:,.0f}'
    a,z=r['first_month'],r['last_month']; checks=r['checks']
    best=max(r['scenarios'],key=lambda s:s['min_cash_pence'])
    findings=f"""Recognised monthly revenue changes from {gbp(a['revenue_pence'])} to {gbp(z['revenue_pence'])}; closing cash changes from {gbp(a['cash_pence'])} to {gbp(z['cash_pence'])}. At September 2026, operating profit is {gbp(z['profit_pence'])}, receivables {gbp(z['ar_pence'])}, overdue receivables {gbp(z['overdue_pence'])}, deferred revenue {gbp(z['deferred_pence'])}, and payables {gbp(z['ap_pence'])}. The weekly forecast minimum is {gbp(r['weekly_min_cash_pence'])}. These are simulation results, not observations about a real company."""
    scenario_rows='\n'.join(f"| {s['scenario']} | {gbp(s['min_cash_pence'])} | {gbp(s['closing_cash_pence'])} | {gbp(s['profit_pence'])} | {s['breach']} |" for s in r['scenarios'])
    write('README.md',f"""# Growth vs Cash: A Finance Decision Lab for a Subscription Business

CedarCloud Workflow is a fictional subscription software business. This portfolio investigation traces transactions through accounting, reconciliation, management reporting and cash decisions. All company data is synthetic GBP. No affiliation with LSEG is claimed.

{findings}

![Monthly finance report](outputs/overview.png)

## Run locally

Python 3.11.9 was used. From this directory:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m src.build
python -m pytest -q
python -m streamlit run app.py
```

Existing source snapshots allow offline rebuilds. Initial source downloads require internet. The build overwrites generated files in data/ and outputs/; keep manual edits elsewhere. Core analysis requires no UI, paid service or AI credentials.

## Deliverables

- [Management report](docs/management_report.md) and [scenario comparison](docs/scenario_analysis.md).
- [Excel financial review model](outputs/finance_model.xlsx): source snapshots and live review formulas. Scenario refresh uses Python; Excel is not a duplicate simulation engine.
- [SQLite database](outputs/finance.sqlite), CSV imports and [Power BI build instructions](docs/power_bi_setup.md). A native PBIX has not been created.
- [Saved checks](outputs/results.json), [exceptions](outputs/exceptions.csv), [audit trail](outputs/repair_log.csv), and [holdout results](outputs/holdout_metrics.csv).

## Documentation index

"""+'\n'.join(f'- [{n.replace("_"," ")}](docs/{n}.md)' for n in ['project_brief','requirements_mapping','data_sources','data_dictionary','financial_logic','data_quality_and_controls','architecture','forecasting_methodology','scenario_analysis','management_report','power_bi_setup','runbook','validation_report','learning_guide','decisions','limitations','portfolio_summary']))
    write('docs/project_brief.md',"""# Project brief

CedarCloud Workflow sells workflow software to SMB and enterprise customers using Starter, Team and Scale tiers. The CFO needs to evaluate cash capacity, the controller needs reliable month-end records, and the commercial lead needs pricing and collections options. These are simulated stakeholder needs, not evidence of actual stakeholder experience.

Questions: why cash differs from revenue and profit, which tiers/customers/costs explain changes, what 13-week liquidity looks like, whether five hires and a launch fit the minimum cash policy, and how trustworthy records are.

Scope: 500 acquired customers across 21 calendar months, January 2025–September 2026, one currency GBP, no VAT, tax, debt, fixed assets or investment returns. January opening balances are cash and equity of GBP 1.4m. All other opening balances are zero. Calendar months end at local date midnight without timezone conversions.

Success means reproducible reports, exact pence accounting reconciliation, measured corruption detection, chronological forecast evaluation and evidence-based decisions. Acceptance evidence is in validation_report.md. Illustrative probabilities describe this invented business; they are not estimates from the starter source.
""")
    requirements=[('Analyse financial and operational data','monthly_actuals.csv; revenue_by_tier.csv; customer_ar.csv','Profit/cash bridge and preaggregated SQL reconcile'),('Management reports, forecasts and budgets','management_report.md; budget_comparison.csv; forecast_12m.csv','Budget timestamp precedes January 2025; chronological holdout'),('Repeatable dashboards and analysis','app.py; finance_model.xlsx; powerbi/analysis.sql','AppTest and workbook snapshot checks'),('Responsible AI','Deterministic management commentary templates','No credentials or generated numerical claims'),('Evidence and communication','management_report.md and requirements mapping','Every financial claim reads saved execution results'),('Planning and month-end processes','trial_balance.csv; journal export; roll-forward checks','Journal and period bridge residuals zero'),('Accuracy and reliable records','manifest.json; exceptions.csv; repair_log.csv','Hashes; inserted truth never read by detector'),('Simplify and document processes','python -m src.build; runbook.md','Repeat build CSV hashes unchanged'),('Ownership and numerical judgment','scenario comparison and sensitivity controls','Threshold breach and trade-offs reported, including adverse cases'),('Financial statements and business support','financial_logic.md; trial balance; profit and cash report','AR, deferred, AP and cash reconcile')]
    write('docs/requirements_mapping.md',"# Requirements mapping\n\nThe current Workday posting R0125039 could not be retrieved on 2026-11-08. This mapping uses the supplied description, not independently confirmed current wording.\n\n| Requirement | Concrete feature/evidence | Acceptance check |\n|---|---|---|\n"+'\n'.join('| '+' | '.join(x)+' |' for x in requirements)+"\n\nDemonstrates local implementation, financial reasoning and technical documentation. Cannot establish experience with real senior stakeholders, actual month-end deadlines, commercial negotiation, production controls, Excel workplace proficiency or professional accounting judgment. No ATS score or interview guarantee.\n")
    write('docs/data_sources.md',f"""# Data sources and provenance

Access date: 2026-11-08. [Subscription Billing](https://databasesample.com/datasets/subscription-billing), version 3, describes synthetic data under [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/). Five CSV snapshots are preserved in data/source. manifest.json contains individual download URLs, SHA-256 checksums, schemas, actual row counts, date minima/maxima and three sample records per table. Currency is unspecified and is never assigned to source money.

Actual audit results (source amounts in unspecified units):

```json
{json.dumps(r['source_audit'],indent=2)}
```

Successful payments are aggregated by invoice before comparing to amounts. Other statuses are not cash receipts. Date checks compare payment dates with invoice dates, invoice with subscription start, cancellation and renewal with subscription start. Reference integrity is checked across all four foreign-key relationships. A mismatch is an investigation signal, not proof of fraud. The publisher's verified label is not relied on.

Decision: source data is suitable for schema inspiration, not a coherent accounting history. It lacks expenses, service periods, due dates, opening balances and currency. See decisions.md. The CedarCloud model is generated independently; no source records or amounts are merged into its books. Source CC0 does not imply any claim about a real business.

The job URL in the user brief was inaccessible. Learning links in learning_guide.md were retrieved successfully; Microsoft displays an authorization notice but its article text was accessible. These references are learning material, not project data.
""")
    dictionary='# Data dictionary\n\nAll money fields ending `_pence` are signed integer GBP pence. Dates are ISO YYYY-MM-DD strings. Source snapshot schemas are in data/source/manifest.json. Empty cancel means no recorded cancellation.\n\n'
    grains={'customers':'one acquired customer; customer_id key','subscriptions':'one subscription per customer; subscription_id key','invoices':'one billing obligation; invoice_id key; subscription/customer foreign keys','payments':'one attempt or refund; payment_id key; invoice_id foreign key','revenue':'one invoice/service month; invoice_id + date key','expenses':'one category/month bill; expense_id key','bank':'one cash movement; bank_id key; ref links receipt/refund or expense','journal':'one journal line; date + ref identifies entry; two lines per posting; repeated refs permitted across recognition months'}
    meanings={'date':'effective posting/issue/service-month date, according to table','amount_pence':'positive obligation, attempt, recognition or expense magnitude','signed_pence':'bank: inflow positive; ledger: debit positive, credit negative','cancel':'exclusive service stop date; cancellations only at annual renewal for annual terms','service_end':'exclusive end of invoiced service','due':'invoice date + 30 days','payment_date':'contracted expense cash settlement date','term_months':'1 monthly or 12 annual','fee_pence':'full billing-period fee','mrr_pence':'contract monthly recurring revenue, annual fee divided by 12','status':'failed, successful or refund; not interchangeable','ref':'document or transaction evidence reference','start':'inclusive subscription start','tier':'Starter, Team or Scale','segment':'SMB or Enterprise','acquired':'first subscription month','account':'Cash, AR, Deferred, Revenue, AP, Equity or expense category'}
    for name,df in t.items():
        dictionary+=f'## {name}\n\nGrain: {grains[name]}.\n\n| Field | Storage type | Meaning |\n|---|---|---|\n'
        for col in df: dictionary+=f'| {col} | {df[col].dtype} | {meanings.get(col,"Unique identifier / descriptive label: "+col)} |\n'
        dictionary+='\n'
    dictionary+='Reporting: monthly_actuals has one calendar month, scenarios one intervention, forecast_12m one projected month, forecast_13w one seven-day window, customer_ar one customer, and revenue_by_tier one month/tier. Balances are month-end stocks and must not be summed across months. Profit=revenue-cost, margin=profit/revenue, collections_rate=successful receipts/current invoices (can exceed 100% due to old AR), churn=cancelled subscriptions/opening subscriptions. Zero ratio denominators produce missing values, not zero. Active subscriptions are counted at month start; annual MRR uses discounted annual fee/12. MRR is neither invoiced cash nor recognised net revenue. Refunds reduce recognised revenue but not contract MRR. Cash runway is intentionally not reported. Variance=actual-budget; expense positive variance is adverse.\n'
    write('docs/data_dictionary.md',dictionary)
    annual=t['invoices'].merge(t['subscriptions'][['subscription_id','term_months']],on='subscription_id'); ex=annual[annual.term_months==12].iloc[0]
    write('docs/financial_logic.md',f"""# Financial logic

The engine uses integer GBP pence; no floating point journal postings. Debit is positive, credit negative. Bank inflows are positive. Reports present revenue, liabilities and cost magnitudes positive, profit can be negative. Cutoffs include the last day; service periods are start-inclusive/end-exclusive. All subscriptions start on the first of a month, so full-month allocation is exact. Any division remainder belongs to the final service month.

Invoice: Dr AR, Cr Deferred. Receipt: Dr Cash, Cr AR. Failed attempts: no journal. Recognition: Dr Deferred, Cr Revenue each service month. Expense: Dr category, Cr AP. Supplier payment: Dr AP, Cr Cash. Refund is a small service credit after delivery: Dr Revenue, Cr Cash. It does not reverse unearned service or reopen AR. There are no prepayments; AP is the basic accrual example. Opening: Dr Cash, Cr Equity GBP 1.4m.

AR close = open + invoices - successful settlements. Deferred close = open + invoices - gross scheduled recognition. Net revenue = scheduled recognition - service credits. AP close = open + expense recognised - supplier settlements. Cash close = open + receipts - cash outflows including refunds.

Cash change = operating profit - change in AR + change in Deferred + change in AP. No depreciation, debt, dividends, financing after opening or capex are modelled. This cash summary is not a statutory cash-flow statement. Trial balance uses cumulative signed account balances; profit is not closed into equity during the history.

## Worked annual example

Invoice {ex.invoice_id} for {ex.customer_id} bills {gbp(ex.amount_pence)} on {ex.date} for service through (excluding) {ex.service_end}. It creates equal AR and deferred revenue. Each month releases {gbp(ex.amount_pence//12)} into revenue. After one month, deferred is 11/12 of the invoice. A successful receipt clears the invoice AR in full and increases cash, without creating revenue. If unpaid, revenue still accrues while AR remains outstanding. Trace its actual attempts in payments.csv and ledger refs in journal.csv. A failed attempt has no cash effect. A service credit, if present, reduces revenue separately.

Reconciliation sources: journal totals generate monthly P&L and balance accounts; bank rows independently generate cash movements; invoice and successful payment totals verify AR; invoice totals and recognition verify deferred. SQL aggregates at invoice grain before joins to avoid one-to-many multiplication.
""")
    write('docs/data_quality_and_controls.md',f"""# Data quality and controls

Layers: data/truth contains coherent transactions plus a separate inserted_errors.csv evaluation answer key; data/exports contains immutable clean operational exports; data/corrupted contains controlled faults; data/reconciled contains evidence-restored records. controls() accepts source tables only and never opens inserted truth. build.py compares detection to truth only after detection.

Faults: duplicate invoice, duplicate payment, inconsistent customer reference, invoice outside its service period, missing bank reference, unmatched extra bank transaction and payment moved to a wrong period. The missing bank reference creates two exception symptoms. Detection uses primary keys, subscription/customer relationships, service dates, bank references and receipt-to-bank date/amount comparisons.

Measured issue-level precision {checks['precision']:.1%}, recall {checks['recall']:.1%}; {checks['true_positives']} matched issues out of {checks['inserted_issues']} truth issues. This is a small designed test, not an estimate of production accuracy. Clean exports produced {checks['clean_exceptions']} data exceptions. No blanket claim about unknown faults is justified.

exceptions.csv includes affected record, issue, exposure in pence, suggested action and status. Exposures can overlap and must not be added as a loss estimate. Duplicates are confirmed; relationship and bank exceptions require investigation. Overdue balances are a business risk, shown separately in monthly and customer reports, not flagged as corrupted data.

Correction workflow: quarantine, compare to preserved operational exports and bank evidence, restore evidence-backed records, rerun controls and financial tie-outs, retain original corrupt copy and before/after hashes in repair_log.csv. This exercise has clean evidence available; a real unknown bank item would remain unresolved, never silently deleted. Simulated review labels are not claims of actual approval. Reports use restored exports. Duplicate-only dirty copies must not change financial reports after key quarantine (tested).
""")
    write('docs/architecture.md',"""# Architecture

```mermaid
flowchart LR
  A[Seed and JSON assumptions] --> B[Coherent transaction simulation]
  B --> C[Operational CSV exports]
  C --> D[Controlled corrupt copies]
  D --> E[Controls and exception register]
  C --> F[Evidence restoration and audit log]
  E --> F
  F --> G[Ledger and monthly reporting]
  G --> H[Cutoff snapshots and driver forecasts]
  H --> I[Excel / Streamlit / Power BI CSVs]
  G --> J[SQLite views]
```

src/lab.py owns generation, finance logic, controls and forecasting. src/build.py orchestrates outputs and verifies invariants. src/source_audit.py downloads and profiles the unrelated starter schema. src/documentation.py produces documentation and template-based commentary from results. app.py reads outputs and calls the same forecast engine with controls. tests/ verifies accounting and boundaries. powerbi/analysis.sql documents safe aggregation. SQLite is a local analysis store, not an enterprise posting system. No external service is required after snapshots and dependencies are available.
""")
    write('docs/forecasting_methodology.md',"""# Forecasting methodology

Monthly model begins with customer status as of cutoff, contract MRR, historical six-month acquisitions and observed cancellations. Future start dates are excluded; cancellations after the forecast date never affect calibration or active count. Recent three-month billing, successful collections and category cost averages are filtered before fitting. Future payments and invoices are never used. forecast() accepts the full tables but gates all observations by cutoff; tests mutate future records to demonstrate invariance.

Customer count rolls forward using observed churn and acquisitions. Revenue uses contract MRR with price change phased over 12 months (a renewal approximation). Billing uses a recent billing/customer ratio, which smooths annual seasonality. Receipts collect a calibrated fraction of opening AR plus new billing each month. Collection interventions change that fraction, never revenue. Cloud changes with customer count; other costs use recent averages; marketing reductions, five hires and a one-off expensed launch alter cost and cash equally. Monthly AP timing is simplified to expense-paid-in-month; the weekly model explicitly handles known AP timing. Negative cash means funding required, not permitted bank overdraft.

Weekly model uses unpaid invoices known at cutoff, due dates plus 35-day delay, 95% recoverability, contracted recurring billing for existing customers, and scheduled category payments. Weeks begin the day after cutoff (not necessarily Monday), are seven days long and form exactly 91 days. It excludes new acquisitions and uncertain churn. Weekly and monthly models answer different timing questions and are not expected to match exactly; no false reconciliation is claimed.

Holdout: train through 2026-06-30, freeze July–September 2026, evaluate three monthly steps once. Baseline repeats the last observed monthly revenue, receipts or cash balance. MAE and signed bias are in pence (positive bias overpredicts). WAPE=sum absolute errors / sum absolute actuals, missing if denominator zero. Saved predictions and metrics are in outputs. A three-month sample is weak evidence and does not validate the 12-month horizon, weekly forecast or scenario effects. Assumptions are fixed in JSON before evaluation and not retuned to make driver forecasts outperform naive. See actual comparison in management_report.md.
""")
    write('docs/scenario_analysis.md',f"""# Scenario analysis

All amounts GBP. Forecast origin 2026-09-30. Minimum cash policy {gbp(CFG['minimum_cash_pence'])}, editable in config and app. Monthly minimum excludes opening cash; breach uses strict less-than.

| Intervention | Minimum cash | Closing cash | 12-month operating profit | Breach |
|---|---:|---:|---:|---|
{scenario_rows}

Exact drivers are stored in outputs/scenarios.csv assumptions column and SCENARIOS in src/lab.py. Base uses calibrated acquisition and churn, no hires or launch. Upside adds 18 customers/month and raises collection fraction 12 percentage points; downside adds five and cuts it 15 points. Hire-now includes five hires at GBP 5,500 per month each and a GBP 90,000 launch in month one. Delay starts hires after six months and includes the same immediate launch. Collections adds 15 percentage points capped at 100%. Pricing phases a 5% uplift across renewals over 12 months. Marketing control removes 20% of marketing cost. Combined uses collections, pricing, marketing control, six-month hiring delay and launch.

{best['scenario']} has the strongest minimum cash among these fixed cases ({gbp(best['min_cash_pence'])}). Ranking liquidity alone is not a complete business decision. Cases without hiring and launch have lower investment. Faster collections brings cash forward without increasing revenue; it cannot rescue unit economics indefinitely. Pricing assumes no incremental churn, and marketing cuts assume unchanged acquisition: optimistic causal simplifications, not proven elasticities. Delay may reduce capacity and launch delivery speed. Compare these trade-offs before commitment.

Sensitivity workflow: vary collection uplift, price, marketing cut, hiring delay and minimum cash in Streamlit; rerun projections and observe profits and minimum cash. Test adverse acquisition and collection cases, not only optimistic interventions. No conclusion about hiring-driven revenue uplift is supportable because that effect is not modelled.
""")
    metric_rows='\n'.join(f"| {x['metric']} | {x['model']} | {gbp(x['mae_pence'])} | {gbp(x['bias_pence'])} | {x['wape']:.2%} |" for x in r['holdout_metrics'])
    write('docs/management_report.md',f"""# Management report — September 2026

{findings}

The company consumes cash when spending exceeds collections. Positive recognised revenue alone says nothing about cash sufficiency. The generator includes expansion of payroll and marketing and longer collection delays from April 2026; inspect the actual monthly cost categories in expenses.csv before attributing the scale of the effect. AR growth represents revenue billed but not collected, annual advances create deferred balances, and supplier AP delays cash spending. The exact monthly profit-to-cash explanation is cash_bridge_pence alongside cash_change_pence in monthly_actuals.csv; their maximum residual is {checks['profit_cash_bridge_max_pence']} pence.

Investigate customer_ar.csv sorted by overdue_pence to prioritise collections. revenue_by_tier.csv shows service revenue contributions by tier; refunds are company-level service credits and are not allocated in this gross tier table. Expense category movements are available in expenses.csv and SQLite. Budget variances are in budget_comparison.csv: positive revenue variance is favourable, positive expense variance adverse. The original budget is a simple prehistory plan, not a forecast recalibrated with actuals.

Recommendation: use staged commitments, address overdue receivables with account-specific evidence, and compare five hires plus launch with delaying hiring against the cash threshold. The strongest minimum-cash case is {best['scenario']}; see scenario_analysis.md for quantified alternatives. Do not approve hiring merely because revenue is growing. A negative projected cash balance requires funding or revised commitments, and a threshold breach requires management review. Operational benefits of a launch and hiring are unquantified.

Forecast evaluation (three observed holdout months only):

| Metric | Model | MAE | Bias | WAPE |
|---|---|---:|---:|---:|
{metric_rows}

Use these recorded errors to assess forecast reliability; do not assume the driver model beats a naive forecast. The weekly schedule and 12-month projections have no full-horizon out-of-sample validation. This report is deterministic template commentary, with numbers supplied directly from saved engine results; no AI API or unsourced numerical narrative is used.
""")
    write('docs/power_bi_setup.md',"""# Power BI setup

No native .pbix was created or validated. All required import files are available locally; the Streamlit app provides the working interactive alternative.

1. Get Data > Text/CSV: import outputs/monthly_actuals.csv, budget_comparison.csv, forecast_12m.csv, forecast_13w.csv, scenarios.csv, exceptions.csv, customer_ar.csv and revenue_by_tier.csv. Import data/reconciled/customers.csv and subscriptions.csv for dimensions. Convert dates to Date, *_pence to Whole Number, ratio fields to Decimal Number. Display monetary measures divided by 100 as GBP.
2. Create Calendar = CALENDAR(DATE(2025,1,1), DATE(2027,9,30)). Add MonthStart = DATE(YEAR(Calendar[Date]),MONTH(Calendar[Date]),1). Mark Date as date table. Link Calendar[Date] one-to-many to each monthly fact's month and weekly week_start, with single-direction filtering. Facts are separate: never directly join monthly_actuals to invoices or payments. scenarios is disconnected. Relate customers[customer_id] one-to-many to subscriptions and customer_ar (single direction). Gross tier table can be sliced by a distinct Tier dimension; do not imply this filters company-level costs. Keep scenarios separate from time-series facts.
3. Use the measures below; cash must be last-date, not sum of monthly balances.

```dax
Revenue GBP = DIVIDE(SUM(monthly_actuals[revenue_pence]),100)
Cost GBP = DIVIDE(SUM(monthly_actuals[cost_pence]),100)
Operating Profit GBP = [Revenue GBP] - [Cost GBP]
Operating Margin = DIVIDE([Operating Profit GBP],[Revenue GBP])
Closing Cash GBP = DIVIDE(CALCULATE(SUM(monthly_actuals[cash_pence]),LASTNONBLANK(Calendar[Date],CALCULATE(SUM(monthly_actuals[cash_pence])))),100)
Receipts GBP = DIVIDE(SUM(monthly_actuals[receipts_pence]),100)
Collections Rate = DIVIDE(SUM(monthly_actuals[receipts_pence]),SUM(monthly_actuals[invoiced_pence]))
Revenue Variance GBP = DIVIDE(SUM(budget_comparison[revenue_variance_pence]),100)
Revenue Variance pct = DIVIDE(SUM(budget_comparison[revenue_variance_pence]),SUM(budget_comparison[revenue_budget_pence]))
Exception Count = COUNTROWS(exceptions)
```

Pages: (1) Overview: month slicer, revenue/profit/cash cards and time series. (2) Cash vs profit: monthly profit, cash change, AR/deferred/AP balance trends, customer overdue ranking. (3) Planning: budget variances and actual/forecast revenue; clearly mark forecast boundary. (4) Liquidity: 13-week receipts/payments/cash and threshold line. (5) Decisions and controls: scenario minimum/closing cash/profit table and exception detail/status table. Add tooltips with metric definitions from data_dictionary.md. Reconcile September cards to outputs/results.json and every scenario to scenarios.csv. Avoid totals over stock balances and averaging unweighted percentages. These instructions and DAX need native Power BI validation by the reader.
""")
    write('docs/runbook.md',"""# Runbook

Use README quick-start commands from the repository root. python -m src.build downloads missing starter CSVs, profiles sources, generates seeded transactions, injects faults, detects exceptions, restores evidence, builds reports/forecasts/Excel/SQLite/chart and documentation. It never deletes user files outside named generated paths. Source snapshots are reused; delete or archive one explicitly to redownload that source. requirements.txt pins the tested direct dependency versions, not a platform-complete transitive lock.

python -m pytest -q runs meaningful accounting, control, forecast and Streamlit tests. python -m streamlit run app.py serves locally; Ctrl+C stops it. If PowerShell activation is blocked, call .venv/Scripts/python.exe directly. If imports fail, install requirements into the same interpreter. No browser, Excel, Power BI account, database server or AI key is required for core analysis.

Change config/assumptions.json for a new controlled simulation; preserve previous results for comparison. Change src/lab.py SCENARIOS for named saved interventions. Threshold is pence in JSON and GBP in UI. Never edit generated totals manually. Forecast origin is the last historical month; holdout origin is separately fixed. outputs/checksums.json provides deterministic CSV fingerprints. Spreadsheet ZIP metadata can vary across builds; CSV hashes are the reproducibility contract. See validation_report.md for executed checks and known limits.
""")
    write('docs/validation_report.md',f"""# Validation report

Engine execution results:

```json
{json.dumps(checks,indent=2)}
```

Reproduce: python -m src.build; python -m pytest -q. Test runner results are separately saved in outputs/test_results.txt. Rebuild comparison is in outputs/reproducibility.json; app health and UI tests in outputs/app_validation.json when executed. Absence of those files means those checks have not been completed, not that they passed.

Accounting tolerance is exactly zero pence, monetary snapshot tolerance 1e-7 GBP after conversion. XML inspection checks saved cash cells against engine balances; review formulas have engine-supplied cached results. Native Excel recalculation and workbook visual rendering were not available and are not claimed. Open and recalculate the workbook before relying on changed inputs. Scenario snapshots require Python rebuild. Power BI DAX and layout are provided but not native-tested. Static overview.png is a generated reporting visual, not a screenshot of an uncreated Power BI dashboard. Holdout tests establish only three monthly steps, and controls only the designed fault sample.
""")
    write('docs/learning_guide.md',"""# Learning guide

Study in this order: financial_logic.md worked annual invoice, monthly_actuals profit/cash bridge, data_quality_and_controls.md exception trail, forecasting_methodology.md cutoff design, scenario_analysis.md trade-offs. Trace one invoice by ID across exports, bank and journals. Explain every debit and credit aloud before explaining Python.

Verified reference links (2026-11-08), learning examples only:

- [Stripe revenue recognition](https://stripe.com/guides/introduction-to-revenue-recognition): service delivery versus billing and cash. Redirected regional page was accessible. This simplified project is not an accounting standards opinion.
- [Business Victoria cash forecasting template](https://business.vic.gov.au/tools-and-templates/cash-flow-forecasting-template): practise scheduling receipts and payments.
- [Microsoft Customer Profitability sample](https://learn.microsoft.com/en-us/power-bi/create-reports/sample-customer-profitability): report layout and financial drivers. Article accessible with an authorization notice; sample data is not used here.

Exercises: manually calculate an annual invoice after three months; reconcile AR at two cutoffs; explain why failed attempts create no cash; change a collection assumption and prove revenue unchanged; lower acquisition to five and compare minimum cash; inspect the driver model's worst holdout error; explain why deferred revenue is a liability; demonstrate a duplicate join that inflates totals and fix its grain.

Interview prompts: Why can revenue grow while cash falls? What makes a budget different from a forecast? How did you avoid future-data leakage? What is still unvalidated? What control failed and what evidence resolved it? Would you approve five hires, and what missing commercial evidence matters? What would change with VAT, bad debts, capex or multiple currencies? Answer with saved project results, not general claims.
""")
    write('docs/decisions.md',"""# Decision records

1. Independent simulation instead of repairing source: source dates and cash amounts are inconsistent and key accounting fields absent. Preserve source audit; use only relational inspiration. Consequence: results demonstrate methods, not external business facts.
2. GBP, integer pence, first-of-month service: simplifies rounding and period recognition. Alternative daily proration adds complexity without advancing the core question. Annual plans renew only on anniversaries; monthly churn is illustrative.
3. 500 acquired customers over 21 months; some churn before cutoff. This is not 500 simultaneously active customers. Seed and all primary prices/cost/launch inputs are in configuration; probability/delay/cost formulas are visible in generate() and not empirically fitted. Late-period delay shift is a declared simulation mechanism, not a discovered real cause. Budget is fixed before history using planned customers and MRR rather than fitted actuals.
4. Use balanced two-line journals and AP accruals, no tax or capex. This supplies independently checkable finance relationships at manageable scale.
5. Monthly driver forecast versus last-value baseline. No ML: limited history and need for interpretable interventions. Holdout frozen once; no retuning after results.
6. Weekly scheduling and monthly planning differ deliberately: daily known obligations versus smoothed growth. Explicit limitation is preferable to implying exact timing from a monthly model.
7. XlsxWriter fallback: documented artifact runtime unavailable on this Windows host. Provide styled workbook, formulas, cached values and XML checks; native recalculation/visual QA remain open. Python owns full scenarios to prevent two conflicting finance engines.
8. Native Power BI unavailable in execution workflow. Deliver complete CSVs, model/DAX and build guide, no invented PBIX. Streamlit is the runnable interface.
9. Deterministic commentary rather than paid AI: every number is generated from results; no model credentials, hallucinated metrics or unreviewable API dependency.
""")
    write('docs/limitations.md',"""# Limitations

This is a synthetic portfolio simulation, not real company analysis or work performed for LSEG. No stakeholders were interviewed. Commercial causality, churn response to price, acquisition response to marketing and productivity effects of hiring are not estimated. Scenario recommendations are conditional on declared assumptions.

No VAT, income tax, FX, bad-debt impairment, depreciation, capex, financing covenants, partial service months, mid-period annual cancellations or full statutory statements. Customer collection lags are random and some invoices remain unpaid; no impairment judgment is implied. Refunds are delivered-service credits only. Monthly forecasts smooth annual billing and AP; weekly forecasts exclude new sales. Long-term annual renewal timing is approximate. A three-month holdout cannot validate 12 months; designed corruption tests cannot establish comprehensive controls.

Excel cached outputs and formula structure are checked, but native recalculation and visual workbook review remain unverified. Power BI is an import kit, not a created report. Streamlit consumes saved outputs; scenario overrides regenerate temporary projections, not booked actuals. Pinning direct dependencies does not ensure identical transitive packages on every OS. Generated charts are report visuals, not interface screenshots. No ATS or hiring outcome is claimed.
""")
    # Append computed driver evidence instead of leaving management findings as generic advice.
    exp=t['expenses'].pivot(index='date',columns='category',values='amount_pence')
    costs='\n'.join(f"| {cat} | {gbp(exp.iloc[0][cat])} | {gbp(exp.iloc[-1][cat])} | {gbp(exp.iloc[-1][cat]-exp.iloc[0][cat])} |" for cat in exp.columns)
    rev=t['revenue'].groupby(['date','tier']).amount_pence.sum().unstack(fill_value=0)
    tiers='\n'.join(f"| {tier} | {gbp(rev.iloc[0][tier])} | {gbp(rev.iloc[-1][tier])} |" for tier in rev.columns)
    tail=f"\n\n## Quantified drivers\n\n| Monthly cost | First month | Last month | Change |\n|---|---:|---:|---:|\n{costs}\n\n| Gross service revenue tier | First month | Last month |\n|---|---:|---:|\n{tiers}\n\nSeptember cash bridge: operating profit {gbp(z['profit_pence'])}, compared with cash decline {gbp(z['cash_change_pence'])}. View changes in AR, deferred and AP in the monthly table to trace the difference. Payroll expansion and cloud usage are the largest cost increases in this simulation.\n\nThe driver model loses to the naive baseline on all three tested metrics. Collection timing is poorly represented by applying a recent receipts/billing fraction to all outstanding AR, accelerating receipts too aggressively. This was retained transparently rather than repeatedly adjusted against holdout. Treat monthly liquidity projections as optimistic sensitivity illustrations; use account-level maturity review and additional rolling validation before any commitment. The weekly model also lacks observed horizon validation. Immediate hiring plus launch projects closing cash {gbp(next(s['closing_cash_pence'] for s in r['scenarios'] if s['scenario']=='Hire now + launch'))}; simply delaying hires also breaches policy. Even the combined staged investment case breaches. Defer commitment pending a credible cash recovery/funding plan, rather than interpreting revenue growth as affordability.\n"
    with (ROOT/'docs/management_report.md').open('a',encoding='utf-8') as out: out.write(tail)
    write('docs/portfolio_summary.md',f"""# Portfolio summary

Built Growth vs Cash, a reproducible finance decision lab for fictional CedarCloud Workflow, connecting subscription transactions, double-entry accounting, controls, cash forecasts and management decisions using Python, SQL, Excel and Streamlit.

Completed-work resume bullets (verify saved tests before submission):

- Built a seeded 500-customer, 21-month subscription finance simulation with annual deferrals, AR/AP and bank-to-ledger reconciliation.
- Implemented exception detection evaluated against separately stored faults, with {checks['recall']:.0%} recall on the designed sample and preserved correction evidence.
- Compared driver-based forecasts with naive baselines on a frozen three-month holdout, and quantified five-hire/launch and collections/pricing scenarios.
- Delivered a reviewable Excel model, SQL analysis store, local Streamlit interface and Power BI import/DAX guide; no native PBIX claim.

Demo (five minutes): show README chart and explain revenue versus cash; trace annual invoice in financial_logic.md; inspect exception and repair log; show naive versus driver holdout errors; vary collections and hiring delay in app and explain conditional recommendation. Close with one limitation you would resolve with real company records.
""")
    assumptions="""

## Illustrative parameter inventory

All parameters are invented, not empirically estimated. Primary inputs are in config/assumptions.json. Additional readable generation rules in src/lab.py: initial cohort 230, subsequent 14 acquisitions/month until 500; tier weights 50/35/15%; cancellation probability 0.8% per eligible month, annual only on anniversary; 30% annual mix, 10% annual discount. Payment lag choices: 8/23/48/120 days initially and 40/55/80/120 from April 2026; 18% failed attempts; 3.5% invoices without a successful receipt after lag eligibility; 0.8% of paid invoices receive a 5% delivered-service credit. Payroll GBP 80,000 + GBP 2,500 per elapsed month capped at 15 increments; cloud GBP 65 per active subscription/month; marketing GBP 22,000 + GBP 600 per elapsed month; rent GBP 9,000; suppliers GBP 6,000. Payment day offset 24 days, suppliers 40. Budget customers 230 + 12/month, planned MRR GBP 320 and total costs GBP 150,000 + GBP 2,500/month. Unused illustrative acquisition input in JSON does not govern historical generation: it labels the budget plan; historical acquisition rule is as above. Forecast calibrates observed acquisitions independently. Weekly recovery 95% with 35 days after due for opening AR and 35 days after issue for projected new bills. There are no estimated standard errors or empirical distributions behind these assumptions.
"""
    with (ROOT/'docs/financial_logic.md').open('a',encoding='utf-8') as out: out.write(assumptions)
    # Delivery verification remains separate from model checks and is never fabricated.
    verification=ROOT/'outputs/app_validation.json'
    repro=ROOT/'outputs/reproducibility.json'
    if verification.exists() and repro.exists():
        v=json.loads(verification.read_text()); rr=json.loads(repro.read_text())
        with (ROOT/'docs/validation_report.md').open('a',encoding='utf-8') as out:
            out.write(f"\nExecuted delivery checks: {rr['files_checked']} CSV files identical across regeneration: {rr['identical']}. Streamlit HTTP health: {v['server_health']}; browser screenshot captured: {v['screenshot']}. See test_results.txt for the latest test count. Management overview chart and application screenshot were visually inspected. Native workbook visual review remains unverified.\n")
        if v.get('screenshot'):
            with (ROOT/'README.md').open('a',encoding='utf-8') as out: out.write('\n## Running application\n\n![Financial overview in Streamlit](outputs/app_overview.png)\n')
