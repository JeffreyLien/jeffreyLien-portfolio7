# Troubleshooting Runbook

## 1. Missing acknowledgment
**Signal:** order has no 855-like record.

**Checks:**
1. Confirm the order exists and has a valid supplier ID.
2. Review transfer log for failures near the order timestamp.
3. Check whether the supplier sent a rejection under a different reference.
4. Confirm required IDs are mapped consistently.
5. Escalate to the trading partner if no inbound document is present.

## 2. Rejected acknowledgment
**Signal:** `ack_status = REJECTED`.

**Common synthetic causes:**
- SKU not mapped
- price mismatch
- invalid customer
- format error

**Action:** isolate the order, compare order fields with the partner mapping, document the root cause, and retest after correction.

## 3. Missing or late shipment notice
**Signal:** no 856-like record or ship date beyond requested window.

**Checks:**
- Was the order accepted?
- Did the supplier produce a shipment event?
- Did the transfer fail?
- Is the order reference consistent across documents?

## 4. Invoice mismatch
**Signal:** invoice amount differs from order amount.

**Checks:**
- Confirm quantity and unit price.
- Check for duplicate invoices.
- Check whether the invoice references the correct order.
- Quantify variance and prioritize high-value exceptions first.

## 5. Transfer failure
**Signal:** `status = FAILED` in `transfer_log`.

**Common synthetic causes:** timeout, authentication failure, schema error, connection reset.

**Triage:**
1. Group failures by partner, transport, and document type.
2. Identify whether the event is isolated or recurring.
3. Prioritize partners with high order value and repeated failures.
4. Record the issue, resolution, and prevention step in the central runbook.

## Escalation rule

High-priority cases are those with high transaction value, repeated failures, or downstream impact across multiple documents. See `sql/04_resource_allocation.sql` for a simple prioritization score.
