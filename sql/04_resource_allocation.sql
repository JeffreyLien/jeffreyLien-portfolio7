-- Triage framework: prioritize operational support where transaction value and failure burden are highest.
WITH supplier_value AS (
    SELECT supplier_id AS partner_id,
           COUNT(*) AS orders,
           SUM(order_amount) AS order_value
    FROM orders
    GROUP BY supplier_id
),
failures AS (
    SELECT partner_id,
           COUNT(*) AS transfer_failures
    FROM transfer_log
    WHERE status = 'FAILED' AND partner_id LIKE 'SUP%'
    GROUP BY partner_id
),
rejections AS (
    SELECT supplier_id AS partner_id,
           COUNT(*) AS rejected_documents
    FROM acknowledgments
    WHERE ack_status = 'REJECTED'
    GROUP BY supplier_id
)
SELECT
    v.partner_id,
    v.orders,
    ROUND(v.order_value, 2) AS order_value,
    COALESCE(f.transfer_failures, 0) AS transfer_failures,
    COALESCE(r.rejected_documents, 0) AS rejected_documents,
    ROUND(
        (v.order_value / 100000.0)
        + 3.0 * COALESCE(f.transfer_failures, 0)
        + 2.0 * COALESCE(r.rejected_documents, 0),
        2
    ) AS support_priority_score
FROM supplier_value v
LEFT JOIN failures f USING(partner_id)
LEFT JOIN rejections r USING(partner_id)
ORDER BY support_priority_score DESC;
