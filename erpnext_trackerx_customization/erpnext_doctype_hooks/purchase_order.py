# your_custom_app/overrides/purchase_order.py

import frappe
from frappe import _
from frappe.model.naming import set_name_by_naming_series

def autoname(doc, method):
    """
    Set document name:
    - If custom_purchase_order_no is provided, use it as the doc name.
    - Otherwise, use the standard naming series.
    """
    if doc.custom_purchase_order_no:
        doc.name = doc.custom_purchase_order_no
    else:
        # Use naming series defined in Purchase Order doctype
        set_name_by_naming_series(doc)
        

def validate(doc, method):
    """
    Ensure custom_purchase_order_no is unique if provided.
    """
    if doc.custom_purchase_order_no:
        existing = frappe.db.exists(
            "Purchase Order",
            {
                "custom_purchase_order_no": doc.custom_purchase_order_no,
                "name": ("!=", doc.name)
            }
        )
        if existing:
            frappe.throw(
                _("Purchase Order with Number '{0}' already exists.").format(doc.custom_purchase_order_no),
                title=_("Duplicate Purchase Order No")
            )