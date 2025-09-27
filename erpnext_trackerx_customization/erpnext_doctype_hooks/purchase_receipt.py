# your_custom_app/overrides/purchase_receipt.py

import frappe
from frappe import _
from frappe.model.naming import set_name_by_naming_series

def autoname(doc, method):
    """
    Set document name:
    - If custom_purchase_receipt_no is provided, use it as the doc name.
    - Otherwise, use the standard naming series.
    """
    if doc.custom_purchase_receipt_no:
        doc.name = doc.custom_purchase_receipt_no
    else:
        # Use naming series defined in Purchase Receipt doctype
        set_name_by_naming_series(doc)


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