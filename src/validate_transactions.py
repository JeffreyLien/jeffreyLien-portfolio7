from __future__ import annotations

from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
PROCESSED.mkdir(parents=True, exist_ok=True)


def load_tables() -> dict[str, pd.DataFrame]:
    names = ["trading_partners", "customers", "products", "orders", "acknowledgments", "shipments", "invoices", "transfer_log"]
    return {name: pd.read_csv(RAW / f"{name}.csv") for name in names}


def build_database(tables: dict[str, pd.DataFrame]) -> sqlite3.Connection:
    db_path = PROCESSED / "supply_chain.db"
    if db_path.exists():
        db_path.unlink()
    con = sqlite3.connect(db_path)
    for name, df in tables.items():
        df.to_sql(name, con, if_exists="replace", index=False)
    return con


def collect_exceptions(con: sqlite3.Connection) -> pd.DataFrame:
    queries = {
        "MISSING_ACK": """
            SELECT o.order_id, o.supplier_id AS partner_id, 'MISSING_ACK' AS exception_type,
                   'No 855-like acknowledgment found' AS detail
            FROM orders o LEFT JOIN acknowledgments a ON o.order_id = a.order_id
            WHERE a.order_id IS NULL
        """,
        "REJECTED_ACK": """
            SELECT a.order_id, a.supplier_id AS partner_id, 'REJECTED_ACK' AS exception_type,
                   a.reject_reason AS detail
            FROM acknowledgments a WHERE a.ack_status = 'REJECTED'
        """,
        "MISSING_SHIPMENT": """
            SELECT o.order_id, o.supplier_id AS partner_id, 'MISSING_SHIPMENT' AS exception_type,
                   'No 856-like shipment notice found' AS detail
            FROM orders o LEFT JOIN shipments s ON o.order_id = s.order_id
            WHERE s.order_id IS NULL
        """,
        "LATE_SHIPMENT": """
            SELECT o.order_id, o.supplier_id AS partner_id, 'LATE_SHIPMENT' AS exception_type,
                   CAST(julianday(s.ship_date) - julianday(o.order_date) - o.requested_ship_days AS INT) || ' days late' AS detail
            FROM orders o JOIN shipments s ON o.order_id = s.order_id
            WHERE julianday(s.ship_date) - julianday(o.order_date) > o.requested_ship_days
        """,
        "MISSING_INVOICE": """
            SELECT o.order_id, o.supplier_id AS partner_id, 'MISSING_INVOICE' AS exception_type,
                   'No 810-like invoice found' AS detail
            FROM orders o LEFT JOIN invoices i ON o.order_id = i.order_id
            WHERE i.order_id IS NULL
        """,
        "INVOICE_AMOUNT_MISMATCH": """
            SELECT o.order_id, o.supplier_id AS partner_id, 'INVOICE_AMOUNT_MISMATCH' AS exception_type,
                   'order=' || ROUND(o.order_amount,2) || ', invoice=' || ROUND(i.invoice_amount,2) AS detail
            FROM orders o JOIN invoices i ON o.order_id = i.order_id
            WHERE ABS(o.order_amount - i.invoice_amount) > 0.01
        """,
        "INVALID_ORDER_REFERENCE": """
            SELECT i.order_id, i.supplier_id AS partner_id, 'INVALID_ORDER_REFERENCE' AS exception_type,
                   'Invoice references unknown order' AS detail
            FROM invoices i LEFT JOIN orders o ON i.order_id = o.order_id
            WHERE o.order_id IS NULL
        """,
        "TRANSFER_FAILURE": """
            SELECT event_id AS order_id, partner_id, 'TRANSFER_FAILURE' AS exception_type,
                   document_type || ' via ' || transport || ': ' || error_code AS detail
            FROM transfer_log WHERE status = 'FAILED'
        """,
    }
    frames = [pd.read_sql_query(sql, con) for sql in queries.values()]
    exceptions = pd.concat(frames, ignore_index=True)
    exceptions.insert(0, "exception_id", [f"EXC{i:07d}" for i in range(1, len(exceptions) + 1)])
    return exceptions


def partner_scorecard(con: sqlite3.Connection, exceptions: pd.DataFrame) -> pd.DataFrame:
    base = pd.read_sql_query("""
        SELECT supplier_id AS partner_id,
               COUNT(*) AS order_count,
               ROUND(SUM(order_amount),2) AS order_value
        FROM orders GROUP BY supplier_id
    """, con)
    exc = exceptions[exceptions["partner_id"].str.startswith("SUP", na=False)].groupby("partner_id").size().rename("exception_count").reset_index()
    score = base.merge(exc, on="partner_id", how="left").fillna({"exception_count": 0})
    score["exception_count"] = score["exception_count"].astype(int)
    score["exceptions_per_100_orders"] = (100 * score["exception_count"] / score["order_count"]).round(2)
    score["health_band"] = pd.cut(score["exceptions_per_100_orders"], bins=[-1, 20, 35, float("inf")], labels=["Green", "Watch", "High Risk"])
    return score.sort_values(["exceptions_per_100_orders", "order_value"], ascending=[False, False])


def main() -> None:
    tables = load_tables()
    con = build_database(tables)
    exceptions = collect_exceptions(con)
    exceptions.to_csv(PROCESSED / "exceptions.csv", index=False)
    score = partner_scorecard(con, exceptions)
    score.to_csv(PROCESSED / "partner_scorecard.csv", index=False)

    summary = exceptions["exception_type"].value_counts().rename_axis("exception_type").reset_index(name="count")
    summary.to_csv(PROCESSED / "exception_summary.csv", index=False)

    print(f"Found {len(exceptions):,} exceptions across {len(tables['orders']):,} orders.")
    print(summary.to_string(index=False))
    con.close()


if __name__ == "__main__":
    main()
