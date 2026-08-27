from __future__ import annotations

from pathlib import Path
import random
import numpy as np
import pandas as pd

SEED = 42
rng = np.random.default_rng(SEED)
random.seed(SEED)

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

N_SUPPLIERS = 40
N_DISTRIBUTORS = 60
N_CUSTOMERS = 120
N_ORDERS = 8000

START_DATE = pd.Timestamp("2026-01-01")
END_DATE = pd.Timestamp("2026-06-30")


def make_partners() -> pd.DataFrame:
    rows = []
    for i in range(1, N_SUPPLIERS + 1):
        rows.append({
            "partner_id": f"SUP{i:03d}",
            "partner_type": "supplier",
            "partner_name": f"Supplier {i:03d}",
            "integration_method": random.choice(["AS2", "SFTP", "VAN"]),
            "active": True,
        })
    for i in range(1, N_DISTRIBUTORS + 1):
        rows.append({
            "partner_id": f"DST{i:03d}",
            "partner_type": "distributor",
            "partner_name": f"Distributor {i:03d}",
            "integration_method": random.choice(["AS2", "SFTP", "VAN"]),
            "active": True,
        })
    return pd.DataFrame(rows)


def make_customers() -> pd.DataFrame:
    segments = ["Healthcare", "Manufacturing", "Education", "Hospitality", "Government", "Commercial"]
    states = ["AL", "GA", "TN", "MS", "FL", "TX", "NC", "SC"]
    return pd.DataFrame({
        "customer_id": [f"CUS{i:04d}" for i in range(1, N_CUSTOMERS + 1)],
        "customer_name": [f"Business Customer {i:04d}" for i in range(1, N_CUSTOMERS + 1)],
        "segment": rng.choice(segments, N_CUSTOMERS),
        "state": rng.choice(states, N_CUSTOMERS),
    })


def make_products() -> pd.DataFrame:
    cats = {
        "Janitorial": (12, 240),
        "Packaging": (8, 180),
        "Safety": (15, 320),
        "Foodservice": (10, 250),
        "Office": (4, 80),
        "MRO": (20, 500),
    }
    rows = []
    sku = 1
    for cat, (lo, hi) in cats.items():
        for _ in range(50):
            rows.append({
                "sku": f"SKU{sku:05d}",
                "category": cat,
                "unit_price": round(float(rng.uniform(lo, hi)), 2),
            })
            sku += 1
    return pd.DataFrame(rows)


def random_dates(n: int) -> pd.Series:
    days = (END_DATE - START_DATE).days
    return START_DATE + pd.to_timedelta(rng.integers(0, days + 1, n), unit="D")


def main() -> None:
    partners = make_partners()
    customers = make_customers()
    products = make_products()

    suppliers = partners.query("partner_type == 'supplier'")["partner_id"].to_numpy()
    distributors = partners.query("partner_type == 'distributor'")["partner_id"].to_numpy()
    customer_ids = customers["customer_id"].to_numpy()
    product_skus = products["sku"].to_numpy()
    price_map = products.set_index("sku")["unit_price"].to_dict()

    order_dates = random_dates(N_ORDERS)
    skus = rng.choice(product_skus, N_ORDERS)
    qty = rng.integers(1, 75, N_ORDERS)
    unit_price = np.array([price_map[s] for s in skus])
    amount = np.round(qty * unit_price, 2)

    orders = pd.DataFrame({
        "order_id": [f"ORD{i:07d}" for i in range(1, N_ORDERS + 1)],
        "order_date": order_dates,
        "customer_id": rng.choice(customer_ids, N_ORDERS),
        "distributor_id": rng.choice(distributors, N_ORDERS),
        "supplier_id": rng.choice(suppliers, N_ORDERS),
        "sku": skus,
        "quantity": qty,
        "unit_price": unit_price,
        "order_amount": amount,
        "requested_ship_days": rng.choice([1, 2, 3, 5, 7], N_ORDERS, p=[0.08, 0.22, 0.35, 0.25, 0.10]),
    })

    ack_mask = rng.random(N_ORDERS) > 0.025
    acks = orders.loc[ack_mask, ["order_id", "supplier_id"]].copy()
    acks["ack_id"] = [f"ACK{i:07d}" for i in range(1, len(acks) + 1)]
    acks["ack_timestamp"] = pd.to_datetime(orders.loc[ack_mask, "order_date"].values) + pd.to_timedelta(rng.integers(1, 36, len(acks)), unit="h")
    acks["ack_status"] = rng.choice(["ACCEPTED", "ACCEPTED", "ACCEPTED", "REJECTED"], len(acks), p=[0.31, 0.31, 0.31, 0.07])
    acks["reject_reason"] = np.where(acks["ack_status"].eq("REJECTED"), rng.choice(["SKU_NOT_MAPPED", "PRICE_MISMATCH", "INVALID_CUSTOMER", "FORMAT_ERROR"], len(acks)), "")

    ship_mask = rng.random(N_ORDERS) > 0.035
    ships = orders.loc[ship_mask, ["order_id", "supplier_id", "distributor_id", "order_date", "requested_ship_days"]].copy()
    extra_delay = rng.choice([0, 0, 0, 1, 2, 4, 7], len(ships), p=[0.34, 0.18, 0.12, 0.14, 0.10, 0.07, 0.05])
    ships["ship_id"] = [f"SHP{i:07d}" for i in range(1, len(ships) + 1)]
    ships["ship_date"] = pd.to_datetime(ships["order_date"]) + pd.to_timedelta(ships["requested_ship_days"] + extra_delay, unit="D")
    ships["carrier"] = rng.choice(["UPS", "FedEx", "LTL Carrier A", "LTL Carrier B"], len(ships))
    ships["tracking_number"] = [f"TRK{i:010d}" for i in range(1, len(ships) + 1)]
    ships = ships.drop(columns=["order_date"])

    inv_mask = rng.random(N_ORDERS) > 0.02
    invoices = orders.loc[inv_mask, ["order_id", "supplier_id", "order_date", "order_amount"]].copy()
    invoices["invoice_id"] = [f"INV{i:07d}" for i in range(1, len(invoices) + 1)]
    invoices["invoice_date"] = pd.to_datetime(invoices["order_date"]) + pd.to_timedelta(rng.integers(2, 14, len(invoices)), unit="D")
    invoices["invoice_amount"] = invoices["order_amount"].astype(float)

    mismatch_idx = rng.choice(invoices.index, size=int(len(invoices) * 0.035), replace=False)
    invoices.loc[mismatch_idx, "invoice_amount"] = np.round(invoices.loc[mismatch_idx, "invoice_amount"] * rng.uniform(0.92, 1.12, len(mismatch_idx)), 2)

    malformed_idx = rng.choice(invoices.index.difference(mismatch_idx), size=int(len(invoices) * 0.01), replace=False)
    invoices.loc[malformed_idx, "order_id"] = "BADREF" + invoices.loc[malformed_idx, "invoice_id"].str[-4:]

    duplicate_rows = invoices.sample(frac=0.008, random_state=SEED).copy()
    duplicate_rows["invoice_id"] = duplicate_rows["invoice_id"] + "DUP"
    invoices = pd.concat([invoices, duplicate_rows], ignore_index=True)
    invoices = invoices.drop(columns=["order_date", "order_amount"])

    dates = pd.date_range(START_DATE, END_DATE, freq="D")
    log_rows = []
    event = 1
    for d in dates:
        for _ in range(int(rng.integers(18, 45))):
            p = partners.sample(1, random_state=int(rng.integers(1, 10_000_000))).iloc[0]
            doc = rng.choice(["850", "855", "856", "810"], p=[0.34, 0.22, 0.20, 0.24])
            status = rng.choice(["SUCCESS", "SUCCESS", "SUCCESS", "SUCCESS", "FAILED"], p=[0.24, 0.24, 0.24, 0.23, 0.05])
            log_rows.append({
                "event_id": f"EVT{event:08d}",
                "event_timestamp": d + pd.to_timedelta(int(rng.integers(0, 1440)), unit="m"),
                "partner_id": p["partner_id"],
                "transport": p["integration_method"],
                "document_type": doc,
                "status": status,
                "error_code": rng.choice(["TIMEOUT", "AUTH_FAILURE", "SCHEMA_ERROR", "CONNECTION_RESET"]) if status == "FAILED" else "",
            })
            event += 1
    transfer_log = pd.DataFrame(log_rows)

    partners.to_csv(RAW / "trading_partners.csv", index=False)
    customers.to_csv(RAW / "customers.csv", index=False)
    products.to_csv(RAW / "products.csv", index=False)
    orders.to_csv(RAW / "orders.csv", index=False)
    acks.to_csv(RAW / "acknowledgments.csv", index=False)
    ships.to_csv(RAW / "shipments.csv", index=False)
    invoices.to_csv(RAW / "invoices.csv", index=False)
    transfer_log.to_csv(RAW / "transfer_log.csv", index=False)

    print(f"Generated {len(orders):,} orders, {len(acks):,} acknowledgments, {len(ships):,} shipments, {len(invoices):,} invoices, and {len(transfer_log):,} transfer events.")


if __name__ == "__main__":
    main()
