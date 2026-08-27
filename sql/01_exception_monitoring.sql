-- Daily exception-monitoring queries for a B2B transaction network.
-- SQLite syntax; tables are created by src/validate_transactions.py.

SELECT o.order_id, o.order_date, o.supplier_id, o.distributor_id, o.order_amount
FROM orders o
LEFT JOIN acknowledgments a ON o.order_id = a.order_id
WHERE a.order_id IS NULL;

SELECT a.order_id, a.supplier_id, a.reject_reason, a.ack_timestamp
FROM acknowledgments a
WHERE a.ack_status = 'REJECTED';

SELECT o.order_id,
       o.order_amount,
       i.invoice_amount,
       ROUND(i.invoice_amount - o.order_amount, 2) AS variance
FROM orders o
JOIN invoices i ON o.order_id = i.order_id
WHERE ABS(i.invoice_amount - o.order_amount) > 0.01
ORDER BY ABS(i.invoice_amount - o.order_amount) DESC;

SELECT date(event_timestamp) AS event_date,
       partner_id,
       transport,
       document_type,
       error_code,
       COUNT(*) AS failure_count
FROM transfer_log
WHERE status = 'FAILED'
GROUP BY 1,2,3,4,5
ORDER BY event_date DESC, failure_count DESC;
