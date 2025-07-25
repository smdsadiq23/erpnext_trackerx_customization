import frappe
from frappe import _

@frappe.whitelist()
def get_mr_items_from_sales_order(sales_order):
    """
    Get Material Request Items from Sales Order
    Uses bom_no from each Sales Order Item to expand BOM if set
    Respects custom_size matching but does NOT include size in output
    """
    so = frappe.get_doc("Sales Order", sales_order)
    items = []

    for so_item in so.items:
        if so_item.bom_no:
            items += _get_items_from_bom_for_so_item(so_item)
        else:
            # Fallback: Direct copy (without custom_size)
            items.append({
                "item_code": so_item.item_code,
                "qty": so_item.qty,
                "uom": so_item.uom,
                "stock_uom": so_item.stock_uom,
                "conversion_factor": so_item.conversion_factor,
                "description": so_item.description,
                "sales_order_item": so_item.name
            })

    return items


def _get_items_from_bom_for_so_item(so_item):
    """Expand BOM and calculate component quantities"""
    bom = frappe.get_doc("BOM", so_item.bom_no)
    if not bom.is_active or bom.docstatus != 1:
        frappe.throw(_("BOM {0} is not active or submitted").format(bom.name))

    items = []
    so_qty = so_item.qty
    so_custom_size = so_item.custom_size

    for bom_item in bom.items:
        # Skip if custom_size is set and doesn't match
        if so_custom_size and bom_item.custom_size and bom_item.custom_size != so_custom_size:
            continue

        required_qty = bom_item.qty * so_qty

        items.append({
            "item_code": bom_item.item_code,
            "qty": required_qty,
            "uom": bom_item.uom,
            "stock_uom": bom_item.stock_uom,
            "conversion_factor": bom_item.conversion_factor,
            "description": bom_item.description,
            "bom_no": bom.name,
            "sales_order_item": so_item.name
            # ❌ custom_size is NOT included
        })

    return items