from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

st.set_page_config(page_title="B2B Supply Chain Data Ops", layout="wide")
st.title("B2B Supply Chain Data Operations Monitor")
st.caption("Synthetic portfolio project: transaction flow, partner health, and exception management")

orders = pd.read_csv(RAW / "orders.csv", parse_dates=["order_date"])
exceptions = pd.read_csv(PROCESSED / "exceptions.csv")
score = pd.read_csv(PROCESSED / "partner_scorecard.csv")
transfer = pd.read_csv(RAW / "transfer_log.csv", parse_dates=["event_timestamp"])

c1, c2, c3, c4 = st.columns(4)
c1.metric("Orders", f"{len(orders):,}")
c2.metric("Order Value", f"${orders.order_amount.sum()/1_000_000:.1f}M")
c3.metric("Exceptions", f"{len(exceptions):,}")
c4.metric("Transfer Success", f"{100 * (transfer.status.eq('SUCCESS').mean()):.1f}%")

st.subheader("Exception volume by type")
exc_counts = exceptions["exception_type"].value_counts().sort_values(ascending=True)
st.bar_chart(exc_counts)

st.subheader("Supplier exception scorecard")
show = score[["partner_id", "order_count", "order_value", "exception_count", "exceptions_per_100_orders", "health_band"]].copy()
st.dataframe(show, use_container_width=True, hide_index=True)

st.subheader("File-transfer failures over time")
failures = transfer.loc[transfer.status.eq("FAILED")].copy()
failures["date"] = failures["event_timestamp"].dt.date
trend = failures.groupby("date").size().rename("failed_transfers")
st.line_chart(trend)

st.subheader("Exception explorer")
selected = st.multiselect("Exception type", sorted(exceptions.exception_type.unique()))
view = exceptions if not selected else exceptions[exceptions.exception_type.isin(selected)]
st.dataframe(view.head(1000), use_container_width=True, hide_index=True)
