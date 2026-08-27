# Data Dictionary

## `orders.csv`
- `order_id`: synthetic unique purchase order identifier
- `order_date`: order creation date
- `customer_id`: end business customer
- `distributor_id`: distributor handling the account
- `supplier_id`: supplier fulfilling the order
- `sku`: product identifier
- `quantity`: ordered units
- `unit_price`: unit price
- `order_amount`: calculated transaction amount
- `requested_ship_days`: requested fulfillment window

## `acknowledgments.csv`
- `ack_id`: acknowledgment identifier
- `order_id`: referenced order
- `supplier_id`: responding supplier
- `ack_timestamp`: acknowledgment timestamp
- `ack_status`: accepted or rejected
- `reject_reason`: simulated reject reason

## `shipments.csv`
- `ship_id`: shipment notice identifier
- `order_id`: referenced order
- `supplier_id`: supplier
- `distributor_id`: distributor
- `requested_ship_days`: target window copied for analysis
- `ship_date`: actual ship date
- `carrier`: carrier name
- `tracking_number`: synthetic tracking number

## `invoices.csv`
- `invoice_id`: invoice identifier
- `order_id`: referenced order; some intentionally malformed
- `supplier_id`: billing supplier
- `invoice_date`: invoice date
- `invoice_amount`: billed amount; some intentionally mismatched

## `transfer_log.csv`
- `event_id`: transfer event
- `event_timestamp`: event timestamp
- `partner_id`: trading partner
- `transport`: AS2, SFTP, or VAN label used for synthetic routing
- `document_type`: 850/855/856/810-like document code
- `status`: success or failure
- `error_code`: synthetic technical failure category

## Processed outputs
- `exceptions.csv`: union of operational exceptions
- `partner_scorecard.csv`: supplier-level issue burden
- `exception_summary.csv`: counts by exception type
- `supply_chain.db`: SQLite database used by SQL examples
