import json
import frappe
from frappe import _
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt

@frappe.whitelist()
def custom_create_pick_list(source_name, target_doc=None, for_qty=None):
    for_qty = for_qty or json.loads(target_doc).get("for_qty")
    max_finished_goods_qty = frappe.db.get_value("Work Order", source_name, "qty")

    def update_item_quantity(source, target, source_parent):
        pending_to_issue = flt(source.required_qty) - flt(source.transferred_qty)
        desire_to_transfer = flt(source.required_qty) / max_finished_goods_qty * flt(for_qty)

        qty = 0
        if desire_to_transfer <= pending_to_issue:
            qty = desire_to_transfer
        elif pending_to_issue > 0:
            qty = pending_to_issue

        if qty:
            target.qty = qty
            target.stock_qty = qty
            target.uom = frappe.get_value("Item", source.item_code, "stock_uom")
            target.stock_uom = target.uom
            target.conversion_factor = 1
        else:
            target.delete()

    doc = get_mapped_doc(
        "Work Order",
        source_name,
        {
            "Work Order": {
                "doctype": "Pick List",
                "validation": {"docstatus": ["=", 1]}
            },
            "Work Order Item": {
                "doctype": "Pick List Item",
                "postprocess": update_item_quantity,
                "condition": lambda doc: abs(doc.transferred_qty) < abs(doc.required_qty),
            },
        },
        target_doc,
    )

    doc.for_qty = for_qty

    # Commenting set_item_locations for debug
    # doc.set_item_locations()

    return doc
