from dataclasses import dataclass

REQUIRED_FIELDS = {
    "850": ["ORDER_ID", "CUSTOMER_ID", "DISTRIBUTOR_ID", "SUPPLIER_ID", "AMOUNT"],
    "855": ["ORDER_ID", "ACK_STATUS"],
    "856": ["ORDER_ID", "SHIP_ID", "TRACKING_NUMBER"],
    "810": ["ORDER_ID", "INVOICE_ID", "AMOUNT"],
}

@dataclass
class EdiLikeMessage:
    document_type: str
    fields: dict[str, str]

def parse_edi_like(text: str) -> EdiLikeMessage:
    fields = {}
    for segment in text.strip().split("~"):
        if not segment:
            continue
        parts = segment.split("*", 1)
        if len(parts) == 2:
            fields[parts[0].strip()] = parts[1].strip()
    doc_type = fields.pop("DOC", "")
    return EdiLikeMessage(document_type=doc_type, fields=fields)

def validate_message(message: EdiLikeMessage) -> list[str]:
    issues = []
    if message.document_type not in REQUIRED_FIELDS:
        return [f"Unsupported document type: {message.document_type}"]
    for field in REQUIRED_FIELDS[message.document_type]:
        if not message.fields.get(field):
            issues.append(f"Missing {field}")
    return issues
