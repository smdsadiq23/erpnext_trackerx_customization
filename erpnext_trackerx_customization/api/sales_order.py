# my_app/api/sales_order.py
import frappe

@frappe.whitelist()
def get_sales_order_items(work_order_name, sales_orders, item_code):
    return frappe.get_all(
        "Sales Order Item",
        filters={
            "parent": ["in", frappe.parse_json(sales_orders)],
            "item_code": item_code,
            "custom_pending_qty_for_work_order": [">", 0]
        },
        fields=[
            "name", "parent", "custom_lineitem", "custom_size", "qty",
            "custom_allocated_qty_for_work_order",
            "custom_pending_qty_for_work_order"
        ],
        limit_page_length=1000
    )
