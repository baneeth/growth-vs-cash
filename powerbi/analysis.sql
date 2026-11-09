DROP VIEW IF EXISTS revenue_by_tier;
CREATE VIEW revenue_by_tier AS SELECT date AS month,tier,SUM(amount_pence) AS revenue_pence FROM revenue GROUP BY date,tier;
-- Aggregate receipts to invoice grain BEFORE joining: failed attempts and refunds are not AR settlements.
DROP VIEW IF EXISTS customer_ar;
CREATE VIEW customer_ar AS
WITH settled AS (SELECT invoice_id,SUM(amount_pence) AS paid FROM payments WHERE status='successful' GROUP BY invoice_id)
SELECT i.customer_id,SUM(i.amount_pence-COALESCE(s.paid,0)) AS ar_pence,
SUM(CASE WHEN i.due<'2026-09-30' THEN i.amount_pence-COALESCE(s.paid,0) ELSE 0 END) AS overdue_pence
FROM invoices i LEFT JOIN settled s ON i.invoice_id=s.invoice_id GROUP BY i.customer_id;
