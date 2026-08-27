-- Supplier-facing operational scorecard.
WITH order_base AS (
    SELECT supplier_id AS partner_id,
           COUNT(*) AS order_count,
           SUM(order_amount) AS order_value
    FROM orders
    GROUP BY supplier_id
),
late_shipments AS (
    SELECT o.supplier_id AS partner_id,
           COUNT(*) AS late_shipments
    FROM orders o
    JOIN shipments s ON o.order_id = s.order_id
    WHERE julianday(s.ship_date) - julianday(o.order_date) > o.requested_ship_days
    GROUP BY o.supplier_id
),
rejections AS (
    SELECT supplier_id AS partner_id,
           COUNT(*) AS rejected_acks
    FROM acknowledgments
    WHERE ack_status = 'REJECTED'
    GROUP BY supplier_id
),
transfer_failures AS (
    SELECT partner_id,
           COUNT(*) AS transfer_failures
    FROM transfer_log
    WHERE status = 'FAILED'
      AND partner_id LIKE 'SUP%'
    GROUP BY partner_id
)
SELECT
    o.partner_id,
    o.order_count,
    ROUND(o.order_value, 2) AS order_value,
    COALESCE(l.late_shipments, 0) AS late_shipments,
    COALESCE(r.rejected_acks, 0) AS rejected_acks,
    COALESCE(t.transfer_failures, 0) AS transfer_failures,
    ROUND(100.0 * COALESCE(l.late_shipments, 0) / o.order_count, 2) AS late_ship_rate_pct
FROM order_base o
LEFT JOIN late_shipments l USING(partner_id)
LEFT JOIN rejections r USING(partner_id)
LEFT JOIN transfer_failures t USING(partner_id)
ORDER BY late_ship_rate_pct DESC, order_value DESC;
