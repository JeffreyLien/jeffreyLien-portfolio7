# B2B Supply Chain Data Operations

Synthetic portfolio project modeling the daily data-operations work behind a B2B procurement and distributor network.

The project follows transactions from **business customer → distributor → supplier** and monitors purchase orders, acknowledgments, shipment notices, invoices, and file-transfer events. It demonstrates SQL troubleshooting, data validation, operational monitoring, partner support, resource prioritization, and technical documentation.

> **Portfolio note:** All data is synthetic. This project is inspired by publicly described B2B distribution workflows and is not affiliated with AFFLINK, Performance Food Group, or any other company. The 850/855/856/810 files are simplified EDI-like training examples, not production ANSI X12 specifications.

## Business problem

A transaction can fail even when an order itself is valid: a supplier can reject an order, an acknowledgment may never arrive, a ship notice can be late, an invoice can reference the wrong order, or an AS2/SFTP/VAN transfer can fail.

This project answers:
- Is data moving successfully between trading partners?
- Which orders are incomplete or inconsistent?
- What caused the failure?
- Which partner issues should be addressed first?
- Are errors concentrated by supplier, document type, or transport method?
- How can troubleshooting be standardized?

## Synthetic environment

- 40 suppliers
- 60 distributors
- 120 B2B customers
- 8,000 orders
- Purchase Order → Acknowledgment → Shipment Notice → Invoice lifecycle
- AS2 / SFTP / VAN-labeled transfer events
- Intentionally injected operational exceptions

## What it detects

- Missing acknowledgments
- Rejected acknowledgments
- Missing or late shipment notices
- Missing invoices
- Invoice amount mismatches
- Invalid order references
- Transfer failures

## Components

- `src/generate_synthetic_data.py` — generates synthetic customers, suppliers, distributors, products, orders, documents, and transfer logs.
- `src/validate_transactions.py` — loads data to SQLite and runs repeatable data-quality controls.
- `src/build_issue_queue.py` — prioritizes exceptions by severity and transaction value.
- `src/edi_like_parser.py` — validates simplified 850/855/856/810-like documents.
- `sql/` — reusable SQL for exception monitoring, lifecycle analysis, partner performance, and resource allocation.
- `app/dashboard.py` — Streamlit operations dashboard.
- `docs/` — business-process documentation, data dictionary, troubleshooting runbook, and interview talk track.
- `tests/` — automated validation tests.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python src/generate_synthetic_data.py
python src/validate_transactions.py
python src/build_issue_queue.py
pytest -q
streamlit run app/dashboard.py
```

Or:

```bash
make all
make app
```

## Example analyst workflow

1. Daily monitoring identifies a spike in failed invoice transfers.
2. SQL groups errors by supplier, transport method, and error code.
3. High-value affected orders move to the top of the issue queue.
4. The analyst validates order references and invoice amounts.
5. Recurring schema or connection issues are escalated.
6. Resolution steps are documented in the troubleshooting runbook.
7. Partner performance is monitored for recurring patterns.

## Skills demonstrated

**SQL · Python · SQLite · Data Validation · Data Integration · B2B Operations · Supply Chain Analytics · Transaction Monitoring · Data Quality · Root-Cause Analysis · Resource Allocation · Partner Performance · Operational Reporting · Technical Documentation · EDI-adjacent Workflows · AS2/SFTP/VAN Concepts**

## Resume-ready bullet

> Built a synthetic B2B supply-chain data operations pipeline covering 8,000 orders across suppliers and distributors; used SQL and Python to detect transaction failures, missing documents, invoice mismatches, and fulfillment exceptions, then developed partner scorecards and a prioritized issue queue to support operational troubleshooting and resource allocation.
