# your_custom_app/overrides/purchase_order.py

import frappe
from frappe import _

def validate(doc, method):
    if doc.custom_purchase_order_no:
        # Check if another Purchase Order (excluding current one) has the same custom number
        existing = frappe.db.exists(
            "Purchase Order",
            {
                "custom_purchase_order_no": doc.custom_purchase_order_no,
                "name": ("!=", doc.name)  # exclude current doc
            }
        )
        if existing:
            frappe.throw(
                _("Purchase Order with Number '{0}' already exists.").format(
                    doc.custom_purchase_order_no, existing
                ),
                title=_("Duplicate Purchase Order No")
            )