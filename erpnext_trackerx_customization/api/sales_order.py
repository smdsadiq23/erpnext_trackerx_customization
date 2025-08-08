# my_app/api/sales_order.py
import frappe
from frappe.utils import flt

@frappe.whitelist()
def get_sales_order_items(work_order_name, sales_orders, item_code):
    sales_orders = frappe.parse_json(sales_orders)
    
    # Get current work order's existing allocations
    current_wo_allocations = {}
    if work_order_name and work_order_name not in ['new-work-order-1', None]:
        existing_line_items = frappe.get_all(
            "Work Order Line Item",
            filters={
                "parent": work_order_name,
                "parenttype": "Work Order"
            },
            fields=["sales_order_item", "work_order_allocated_qty"]
        )
        
        for item in existing_line_items:
            current_wo_allocations[item.sales_order_item] = flt(item.work_order_allocated_qty)
    
    # Get all sales order items (including those with 0 pending qty)
    all_items = frappe.get_all(
        "Sales Order Item",
        filters={
            "parent": ["in", sales_orders],
            "item_code": item_code
        },
        fields=[
            "name", "parent", "custom_lineitem", "custom_size", "qty",
            "custom_allocated_qty_for_work_order",
            "custom_pending_qty_for_work_order"
        ],
        limit_page_length=1000
    )
    
    # Filter items based on adjusted pending quantity
    filtered_items = []
    for item in all_items:
        current_allocation = current_wo_allocations.get(item.name, 0)
        adjusted_pending_qty = flt(item.custom_pending_qty_for_work_order) + current_allocation
        
        # Include item if it has adjusted pending qty > 0 OR is already allocated in current WO
        if adjusted_pending_qty > 0 or current_allocation > 0:
            # Adjust the values for display
            item.custom_pending_qty_for_work_order = adjusted_pending_qty
            item.custom_allocated_qty_for_work_order = flt(item.custom_allocated_qty_for_work_order) - current_allocation
            filtered_items.append(item)
    
    return filtered_items