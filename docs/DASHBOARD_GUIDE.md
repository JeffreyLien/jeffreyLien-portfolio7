# Dashboard Guide

The Streamlit app is organized around the kinds of questions a business data analyst would answer in a B2B distributor network.

## 1. Overview

Answers:
- How much transaction volume is flowing through the network?
- What is the total order value?
- How many operational exceptions were detected?
- Which product categories and months drive the most activity?

Visuals:
- KPI cards
- monthly order-value trend
- exception mix
- order value by product category

## 2. Transaction Flow

Answers:
- Are 850/855/856/810-like documents completing the expected lifecycle?
- Which transport channels show the most failures?
- Which document types are failing?
- Which partners and error codes need investigation?

Visuals:
- lifecycle coverage metrics
- monthly transfer success/failure
- failures by AS2/SFTP/VAN label
- failures by document type
- recent transfer-failure table

## 3. Partner Performance

Answers:
- Which suppliers have elevated exception rates?
- Are high-error partners also high-value partners?
- Where should partner-management attention be focused?

Visuals:
- supplier order value vs. exceptions-per-100-orders scatter
- top-risk supplier scorecard

## 4. Exception Queue

Answers:
- Which individual issues should be worked first?
- What is the affected transaction value?
- What troubleshooting action is recommended?

The queue uses a simple severity + transaction-value score and supports filters for priority band and exception type.

## 5. Resource Allocation

Answers:
- Which suppliers consume the most operational support?
- How can analyst capacity be prioritized using business value and issue burden?

Visuals:
- partner support-priority ranking
- supporting order value, order volume, and exception counts

## Run

```bash
python src/generate_synthetic_data.py
python src/validate_transactions.py
python src/build_issue_queue.py
streamlit run app/dashboard.py
```

All records are synthetic and the EDI-like examples are simplified training representations, not production ANSI X12 messages.
