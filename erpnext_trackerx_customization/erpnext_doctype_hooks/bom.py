
import frappe

def validate_bom(doc, method):
    # validate_for_duplicate_bom_item_size(doc);
    pass




def validate_for_duplicate_bom_item_size(doc):
    seen_items = set()
    seen_item_codes_no_size = set()

    for row in doc.items:
        item_code = row.item_code
        size = row.custom_size.strip() if row.custom_size else ""

        key = f"{item_code}::{size}"

        if size:
            if key in seen_items:
                frappe.throw(f"Duplicate item with same Item Code and Size found: {item_code} - {size}. Increase the quantity instead")
            seen_items.add(key)
        else:
            if item_code in seen_item_codes_no_size:
                frappe.throw(f"Item Code {item_code} without Size can be added only once. Increase the quantity instead")
            seen_item_codes_no_size.add(item_code)