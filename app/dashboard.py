from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

st.set_page_config(
    page_title="B2B Supply Chain Data Ops",
    page_icon="📦",
    layout="wide",
)

st.title("B2B Supply Chain Data Operations")
st.caption(
    "Synthetic portfolio environment for transaction monitoring, partner performance, "
    "exception management, and resource allocation."
)

orders = pd.read_csv(RAW / "orders.csv", parse_dates=["order_date"])
products = pd.read_csv(RAW / "products.csv")
acks = pd.read_csv(RAW / "acknowledgments.csv", parse_dates=["ack_timestamp"])
shipments = pd.read_csv(RAW / "shipments.csv", parse_dates=["ship_date"])
invoices = pd.read_csv(RAW / "invoices.csv", parse_dates=["invoice_date"])
transfer = pd.read_csv(RAW / "transfer_log.csv", parse_dates=["event_timestamp"])
exceptions = pd.read_csv(PROCESSED / "exceptions.csv")
score = pd.read_csv(PROCESSED / "partner_scorecard.csv")
queue = pd.read_csv(PROCESSED / "daily_issue_queue.csv")

orders["month"] = orders["order_date"].dt.to_period("M").astype(str)
orders_with_category = orders.merge(products[["sku", "category"]], on="sku", how="left")

total_value = orders["order_amount"].sum()
transfer_success = transfer["status"].eq("SUCCESS").mean()
ack_coverage = orders["order_id"].isin(acks["order_id"]).mean()
ship_coverage = orders["order_id"].isin(shipments["order_id"]).mean()
invoice_coverage = orders["order_id"].isin(invoices["order_id"]).mean()

tab_overview, tab_flow, tab_partner, tab_queue, tab_resource = st.tabs(
    [
        "Overview",
        "Transaction Flow",
        "Partner Performance",
        "Exception Queue",
        "Resource Allocation",
    ]
)

with tab_overview:
    st.subheader("Network overview")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Orders", f"{len(orders):,}")
    c2.metric("Order Value", f"USD {total_value / 1_000_000:.1f}M")
    c3.metric("Operational Exceptions", f"{len(exceptions):,}")
    c4.metric("Transfer Success", f"{100 * transfer_success:.1f}%")

    st.subheader("Monthly order value")
    monthly_value = (
        orders.groupby("month", as_index=False)["order_amount"]
        .sum()
        .set_index("month")
    )
    st.bar_chart(monthly_value)

    left, right = st.columns(2)
    with left:
        st.subheader("Exception mix")
        exception_mix = (
            exceptions["exception_type"]
            .value_counts()
            .rename_axis("exception_type")
            .to_frame("count")
        )
        st.bar_chart(exception_mix)
    with right:
        st.subheader("Order value by product category")
        category_value = (
            orders_with_category.groupby("category")["order_amount"]
            .sum()
            .sort_values(ascending=False)
            .to_frame("order_value")
        )
        st.bar_chart(category_value)

with tab_flow:
    st.subheader("Document lifecycle coverage")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("850-like Orders", f"{len(orders):,}")
    c2.metric("855-like Ack Coverage", f"{100 * ack_coverage:.1f}%")
    c3.metric("856-like Ship Coverage", f"{100 * ship_coverage:.1f}%")
    c4.metric("810-like Invoice Coverage", f"{100 * invoice_coverage:.1f}%")

    st.subheader("Transfer health by month")
    transfer["month"] = transfer["event_timestamp"].dt.to_period("M").astype(str)
    transfer_month = (
        transfer.assign(
            success=lambda x: x["status"].eq("SUCCESS").astype(int),
            failure=lambda x: x["status"].eq("FAILED").astype(int),
        )
        .groupby("month")[["success", "failure"]]
        .sum()
    )
    st.bar_chart(transfer_month)

    left, right = st.columns(2)
    with left:
        st.subheader("Failures by transport")
        transport_failures = (
            transfer.loc[transfer["status"].eq("FAILED"), "transport"]
            .value_counts()
            .to_frame("failures")
        )
        st.bar_chart(transport_failures)
    with right:
        st.subheader("Failures by document type")
        document_failures = (
            transfer.loc[transfer["status"].eq("FAILED"), "document_type"]
            .astype(str)
            .value_counts()
            .to_frame("failures")
        )
        st.bar_chart(document_failures)

    st.subheader("Recent failed transfers")
    failure_view = transfer.loc[
        transfer["status"].eq("FAILED"),
        [
            "event_timestamp",
            "partner_id",
            "transport",
            "document_type",
            "error_code",
        ],
    ].sort_values("event_timestamp", ascending=False)
    st.dataframe(failure_view.head(250), use_container_width=True, hide_index=True)

with tab_partner:
    st.subheader("Supplier performance")
    st.caption(
        "High-value partners with elevated exception rates can be prioritized for "
        "mapping fixes, connection support, or operational review."
    )

    scatter = score[
        ["partner_id", "order_value", "exceptions_per_100_orders", "exception_count"]
    ].copy()
    st.scatter_chart(
        scatter,
        x="order_value",
        y="exceptions_per_100_orders",
        size="exception_count",
    )

    st.subheader("Highest exception-rate suppliers")
    top_risk = score.sort_values(
        ["exceptions_per_100_orders", "order_value"], ascending=[False, False]
    )
    st.dataframe(
        top_risk[
            [
                "partner_id",
                "order_count",
                "order_value",
                "exception_count",
                "exceptions_per_100_orders",
                "health_band",
            ]
        ].head(20),
        use_container_width=True,
        hide_index=True,
    )

with tab_queue:
    st.subheader("Daily issue queue")
    st.caption(
        "The queue combines exception severity with transaction value so analysts "
        "can work the highest-impact issues first."
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Critical", f"{queue['priority_band'].eq('Critical').sum():,}")
    c2.metric("High", f"{queue['priority_band'].eq('High').sum():,}")
    c3.metric("Normal", f"{queue['priority_band'].eq('Normal').sum():,}")

    priority_filter = st.multiselect(
        "Priority",
        ["Critical", "High", "Normal"],
        default=["Critical", "High"],
    )
    exception_filter = st.multiselect(
        "Exception Type",
        sorted(queue["exception_type"].dropna().unique()),
    )

    filtered = queue.copy()
    if priority_filter:
        filtered = filtered[filtered["priority_band"].isin(priority_filter)]
    if exception_filter:
        filtered = filtered[filtered["exception_type"].isin(exception_filter)]

    st.dataframe(
        filtered[
            [
                "exception_id",
                "order_id",
                "partner_id",
                "exception_type",
                "severity",
                "order_value",
                "priority_score",
                "priority_band",
                "recommended_action",
            ]
        ].head(1000),
        use_container_width=True,
        hide_index=True,
    )

with tab_resource:
    st.subheader("Resource allocation")
    st.caption(
        "A support team can allocate analyst time using both partner business value "
        "and recurring operational burden."
    )

    supplier_orders = (
        orders.groupby("supplier_id")
        .agg(order_count=("order_id", "count"), order_value=("order_amount", "sum"))
        .reset_index()
        .rename(columns={"supplier_id": "partner_id"})
    )
    supplier_exc = (
        exceptions.loc[exceptions["partner_id"].astype(str).str.startswith("SUP")]
        .groupby("partner_id")
        .size()
        .rename("exception_count")
        .reset_index()
    )
    allocation = supplier_orders.merge(supplier_exc, on="partner_id", how="left")
    allocation["exception_count"] = allocation["exception_count"].fillna(0)
    allocation["support_priority_score"] = (
        allocation["order_value"] / 100_000
        + 2.5 * allocation["exception_count"]
    ).round(1)
    allocation = allocation.sort_values(
        "support_priority_score", ascending=False
    )

    st.subheader("Top partners for operational support")
    st.bar_chart(
        allocation.head(15).set_index("partner_id")[["support_priority_score"]]
    )

    st.dataframe(
        allocation[
            [
                "partner_id",
                "order_count",
                "order_value",
                "exception_count",
                "support_priority_score",
            ]
        ].head(25),
        use_container_width=True,
        hide_index=True,
    )

st.divider()
st.caption(
    "All data in this dashboard is synthetic. EDI-like examples are simplified "
    "training representations and are not production ANSI X12 specifications."
)
