import frappe
from frappe.utils import flt

def validate(doc, method):
    calculate_total_qty(doc)
    validate_and_update_sales_order_items(doc)

def on_submit(doc, method):
    pass

def calculate_total_qty(doc):
    doc.qty = sum(flt(item.work_order_allocated_qty) for item in doc.custom_work_order_line_items)

def validate_and_update_sales_order_items(doc):
    if not doc.sales_order:
        return

    # Fetch all saved Work Orders except current one
    existing_wos = frappe.get_all("Work Order", filters={"sales_order": doc.sales_order, "name": ["!=", doc.name]}, fields=["name"])
    
    allocations = {}

    # Include current work order lines
    for line in doc.custom_work_order_line_items:
        key = (line.line_item_no, line.size)
        allocations.setdefault(key, 0)
        allocations[key] += flt(line.work_order_allocated_qty)

    # Include saved work orders
    for wo in existing_wos:
        wo_doc = frappe.get_doc("Work Order", wo.name)
        for line in wo_doc.custom_work_order_line_items:
            key = (line.line_item_no, line.size)
            allocations.setdefault(key, 0)
            allocations[key] += flt(line.work_order_allocated_qty)

    # Update matching Sales Order Items
    for (line_item_no, size), total_allocated in allocations.items():
        soi = frappe.get_all(
            "Sales Order Item",
            filters={
                "parent": doc.sales_order,
                "custom_lineitem": line_item_no,
                "custom_size": size
            },
            fields=["name", "qty"]
        )

        if not soi:
            continue

        soi_name = soi[0].name
        original_qty = flt(soi[0].qty)
        pending_qty = original_qty - total_allocated

        if pending_qty < 0:
            frappe.throw(
                f"Pending Qty for Line Item {line_item_no} (Size: {size}) is < 0 after allocation. Please adjust Work Orders."
            )

        frappe.db.set_value("Sales Order Item", soi_name, "custom_pending_qty_for_work_order", pending_qty)
        frappe.db.set_value("Sales Order Item", soi_name, "custom_allocated_qty_for_work_order", total_allocated)
