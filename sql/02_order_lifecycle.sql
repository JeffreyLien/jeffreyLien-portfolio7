-- End-to-end order lifecycle coverage and timeliness.
WITH lifecycle AS (
    SELECT
        o.order_id,
        o.order_date,
        o.supplier_id,
        o.distributor_id,
        o.order_amount,
        a.ack_status,
        a.ack_timestamp,
        s.ship_date,
        i.invoice_date,
        i.invoice_amount,
        CASE WHEN a.order_id IS NOT NULL THEN 1 ELSE 0 END AS has_ack,
        CASE WHEN s.order_id IS NOT NULL THEN 1 ELSE 0 END AS has_ship_notice,
        CASE WHEN i.order_id IS NOT NULL THEN 1 ELSE 0 END AS has_invoice,
        CASE
            WHEN s.order_id IS NOT NULL
             AND julianday(s.ship_date) - julianday(o.order_date) <= o.requested_ship_days
            THEN 1 ELSE 0
        END AS shipped_on_time
    FROM orders o
    LEFT JOIN acknowledgments a ON o.order_id = a.order_id
    LEFT JOIN shipments s ON o.order_id = s.order_id
    LEFT JOIN invoices i ON o.order_id = i.order_id
)
SELECT
    COUNT(*) AS order_count,
    ROUND(100.0 * AVG(has_ack), 2) AS ack_coverage_pct,
    ROUND(100.0 * AVG(has_ship_notice), 2) AS shipment_notice_coverage_pct,
    ROUND(100.0 * AVG(has_invoice), 2) AS invoice_coverage_pct,
    ROUND(100.0 * AVG(shipped_on_time), 2) AS on_time_ship_pct
FROM lifecycle;
