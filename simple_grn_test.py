import frappe

def test_grn():
    # Get GRN
    grn = frappe.get_doc("Goods Receipt Note", "GRN-PRE-2025-00018")
    print(f"GRN docstatus: {grn.docstatus}")
    print(f"Items count: {len(grn.items)}")
    
    # Check first item
    item = grn.items[0]
    item_doc = frappe.get_doc("Item", item.item_code)
    inspection_required = getattr(item_doc, 'inspection_required_before_purchase', 0)
    print(f"Item: {item.item_code}")
    print(f"Material Type: {item.material_type}")
    print(f"Inspection Required: {inspection_required}")
    
    if grn.docstatus == 0:
        print("Submitting GRN...")
        grn.submit()
        print("GRN submitted!")
    
    # Check Purchase Receipts
    prs = frappe.get_all("Purchase Receipt", 
                        filters={"creation": [">", "2025-08-15"]},
                        fields=["name", "supplier"])
    print(f"Purchase Receipts created: {len(prs)}")
    for pr in prs:
        print(f"  - {pr.name} - {pr.supplier}")

test_grn()