from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

SEVERITY = {
    "TRANSFER_FAILURE": 5,
    "INVALID_ORDER_REFERENCE": 5,
    "INVOICE_AMOUNT_MISMATCH": 4,
    "REJECTED_ACK": 4,
    "MISSING_ACK": 3,
    "MISSING_INVOICE": 3,
    "MISSING_SHIPMENT": 3,
    "LATE_SHIPMENT": 2,
}


def main() -> None:
    exceptions = pd.read_csv(PROCESSED / "exceptions.csv")
    orders = pd.read_csv(RAW / "orders.csv")
    order_value = orders.set_index("order_id")["order_amount"]

    queue = exceptions.copy()
    queue["severity"] = queue["exception_type"].map(SEVERITY).fillna(1).astype(int)
    queue["order_value"] = queue["order_id"].map(order_value).fillna(0.0)
    queue["priority_score"] = (
        queue["severity"] * 20
        + (queue["order_value"].clip(upper=25000) / 25000 * 30)
    ).round(1)
    queue["priority_band"] = pd.cut(
        queue["priority_score"],
        bins=[-1, 45, 70, float("inf")],
        labels=["Normal", "High", "Critical"],
    )
    queue["recommended_action"] = queue["exception_type"].map({
        "TRANSFER_FAILURE": "Check transport/auth/schema logs; retry or escalate partner connection",
        "INVALID_ORDER_REFERENCE": "Validate cross-reference mapping before reprocessing invoice",
        "INVOICE_AMOUNT_MISMATCH": "Compare order vs invoice amount; investigate quantity/price variance",
        "REJECTED_ACK": "Review rejection reason and partner mapping; correct and retest",
        "MISSING_ACK": "Check inbound queue and partner transfer history",
        "MISSING_INVOICE": "Confirm fulfillment and expected invoice transmission",
        "MISSING_SHIPMENT": "Confirm fulfillment status and 856-like document delivery",
        "LATE_SHIPMENT": "Review supplier fulfillment performance and downstream impact",
    })
    queue = queue.sort_values(["priority_score", "order_value"], ascending=False)
    queue.to_csv(PROCESSED / "daily_issue_queue.csv", index=False)
    print(f"Wrote {len(queue):,} prioritized issues to data/processed/daily_issue_queue.csv")


if __name__ == "__main__":
    main()
