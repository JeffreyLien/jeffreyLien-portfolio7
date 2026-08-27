from src.edi_like_parser import parse_edi_like, validate_message

def test_valid_order_message():
    text = "DOC*850~ORDER_ID*ORD0000001~CUSTOMER_ID*CUS0001~DISTRIBUTOR_ID*DST001~SUPPLIER_ID*SUP001~AMOUNT*1250.00~"
    msg = parse_edi_like(text)
    assert msg.document_type == "850"
    assert validate_message(msg) == []

def test_missing_required_field():
    text = "DOC*810~ORDER_ID*ORD0000001~INVOICE_ID*INV0000001~"
    msg = parse_edi_like(text)
    assert "Missing AMOUNT" in validate_message(msg)
