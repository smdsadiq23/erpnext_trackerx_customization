# Copyright (c) 2025, CognitionX and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SupplierFGItems(Document):
	pass


@frappe.whitelist()
def get_item_bom_operations(item: str):
    """
    Return BOM Operation rows that live under the Item doctype.
    We query by parent/parenttype so we don't need to know the fieldname.
    """
    if not item:
        return []

    # Pull only what you need
    ops = frappe.get_all(
        "BOM Operation",
        filters={
            "parenttype": "Item",
            "parent": item,
            "docstatus": ["!=", 2],  # ignore cancelled rows
        },
        fields=["custom_order_method", "custom_operation_group", "operation"]
    )
    return ops or []
