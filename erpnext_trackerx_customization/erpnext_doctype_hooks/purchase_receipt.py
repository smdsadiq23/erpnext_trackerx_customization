# your_custom_app/overrides/purchase_receipt.py

import frappe
from frappe import _

def validate(doc, method):
    if doc.custom_purchase_receipt_no:
        # Check if another Purchase Receipt (excluding current one) has the same custom number
        existing = frappe.db.exists(
            "Purchase Receipt",
            {
                "custom_purchase_receipt_no": doc.custom_purchase_receipt_no,
                "name": ("!=", doc.name)  # exclude current doc
            }
        )
        if existing:
            frappe.throw(
                _("Purchase Receipt with Number '{0}' already exists.").format(
                    doc.custom_purchase_receipt_no, existing
                ),
                title=_("Duplicate Purchase Receipt No")
            )