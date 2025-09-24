
import frappe
from frappe import _

def validate(doc, method):
    validate_sales_order_no(doc)
    validate_unique_item_combinations(doc)
    copy_qty_pending_qty(doc, method)


def on_submit(doc, method):
    pass


def validate_sales_order_no(doc):
    if doc.custom_sales_order_no:
        existing = frappe.db.exists(
            "Sales Order",
            {
                "custom_sales_order_no": doc.custom_sales_order_no,
                "name": ("!=", doc.name)
            }
        )
        if existing:
            frappe.throw(
                _("Sales Order with Number '{0}' already exists.").format(
                    doc.custom_sales_order_no, existing
                ),
                title=_("Duplicate Sales Order No")
            )


def validate_unique_item_combinations(doc):
    """
    Checks for duplicate combinations of item_code, custom_lineitem, and custom_size
    in the Sales Order items table.
    """

    item_codes = list(set(i.item_code for i in doc.items if i.item_code))
    if len(item_codes) > 1:
        frappe.throw(
                "Sales Order cannot have multiple Finished Good"
            )

    
    seen_combinations = set()
    for item in doc.items: # 'items' is the default fieldname for the child table
        # Ensure custom fields exist on the Sales Order Item DocType
        # Replace 'custom_lineitem' and 'custom_size' with your actual custom field names
        # if they are different.
        line_item_value = item.get('custom_lineitem') or ''
        size_value = item.get('custom_size') or ''
        combination = (item.item_code, line_item_value, size_value)
        if combination in seen_combinations:

            frappe.throw(
                f"Duplicate item combination found: Item Code '{item.item_code}', "
                f"Line Item '{line_item_value}', Size '{size_value}'. "
                "Please ensure each item combination is unique."
            )
        seen_combinations.add(combination)
    

def copy_qty_pending_qty(doc, method):
    for item in doc.items:
        item.custom_pending_qty_for_work_order = item.qty



