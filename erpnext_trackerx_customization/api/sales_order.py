import frappe
from frappe.utils import flt, now_datetime
from frappe import _

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

@frappe.whitelist()
def get_sales_order_line_items_detailed(sales_orders, production_item):
    """
    Get detailed line items for the dialog with all necessary information
    """
    sales_orders = frappe.parse_json(sales_orders) if isinstance(sales_orders, str) else sales_orders
    
    if not sales_orders or not production_item:
        return {"line_items": [], "total_pending_qty": 0}
    
    # Get all sales order items with pending quantity
    line_items = frappe.db.sql("""
        SELECT 
            soi.name as sales_order_item,
            soi.parent as sales_order,
            soi.custom_lineitem as line_item_no,
            soi.custom_size as size,
            soi.qty as total_qty,
            soi.custom_pending_qty_for_work_order as pending_qty,
            soi.custom_allocated_qty_for_work_order as already_allocated_qty
        FROM `tabSales Order Item` soi
        INNER JOIN `tabSales Order` so ON soi.parent = so.name
        WHERE soi.parent IN ({0})
        AND soi.item_code = %s
        AND soi.custom_pending_qty_for_work_order > 0
        AND so.docstatus = 1
        ORDER BY soi.parent, soi.custom_lineitem, soi.custom_size
    """.format(', '.join(['%s'] * len(sales_orders))), 
    sales_orders + [production_item], as_dict=True)
    
    total_pending_qty = sum(flt(item.pending_qty) for item in line_items)
    
    # Add default allocate_qty and select_item
    for item in line_items:
        item.allocate_qty = min(1.0, flt(item.pending_qty))
        item.select_item = 0  # Default unselected
    
    return {
        "line_items": line_items,
        "total_pending_qty": total_pending_qty
    }

@frappe.whitelist()
def create_work_order_from_line_items(line_items, production_item, company=None, bom_no=None, planned_start_date=None, creation_strategy='single'):
    """
    Create a single work order from selected line items
    """
    line_items = frappe.parse_json(line_items) if isinstance(line_items, str) else line_items
    
    if not line_items or not production_item:
        frappe.throw(_("Line items and Production Item are required"))
    
    # Get unique sales orders from line items
    sales_orders = list(set([item['sales_order'] for item in line_items]))
    
    # Create Work Order
    work_order = frappe.new_doc("Work Order")
    work_order.production_item = production_item
    work_order.company = company or frappe.defaults.get_user_default('Company')
    work_order.bom_no = bom_no
    
    # Get item details
    item_doc = frappe.get_doc("Item", production_item)
    work_order.item_name = item_doc.item_name
    work_order.description = item_doc.description
    work_order.stock_uom = item_doc.stock_uom
    work_order.uom = item_doc.stock_uom
    
    # Set other required fields
    work_order.planned_start_date = planned_start_date or now_datetime()
    work_order.use_multi_level_bom = 1
    
    # Add selected sales orders to custom_sales_orders child table
    for sales_order in sales_orders:
        sales_order_row = work_order.append("custom_sales_orders")
        sales_order_row.sales_order = sales_order
    
    # Add line items to custom_work_order_line_items
    total_qty = 0
    for item in line_items:
        line_item = work_order.append("custom_work_order_line_items")
        line_item.sales_order_item = item['sales_order_item']
        line_item.line_item_no = item['line_item_no']
        line_item.size = item['size']
        line_item.qty = item['total_qty']
        line_item.already_allocated_qty = item.get('already_allocated_qty', 0)
        line_item.pending_qty = item['pending_qty']
        line_item.work_order_allocated_qty = flt(item['allocate_qty'])
        line_item.sales_order = item['sales_order']
        
        total_qty += flt(item['allocate_qty'])
    
    # Update total quantity
    work_order.qty = total_qty
    
    # Save the work order
    work_order.insert()
    work_order.save()
    
    return work_order.name

@frappe.whitelist()
def create_work_orders_bulk(grouped_items=None, individual_items=None, production_item=None, company=None, bom_no=None, planned_start_date=None, creation_strategy='by_line_item'):
    """
    Create multiple work orders based on strategy
    """
    if isinstance(grouped_items, str):
        grouped_items = frappe.parse_json(grouped_items)
    if isinstance(individual_items, str):
        individual_items = frappe.parse_json(individual_items)
    
    created_work_orders = []
    errors = []
    
    try:
        if creation_strategy == 'by_line_item' and grouped_items:
            # Create one work order per line item number
            for line_item_no, items in grouped_items.items():
                try:
                    wo_name = create_work_order_from_line_items(
                        items,
                        production_item,
                        company,
                        bom_no,
                        planned_start_date
                    )
                    created_work_orders.append(wo_name)
                except Exception as e:
                    errors.append({
                        "line_item_no": line_item_no,
                        "error": str(e)
                    })
        
        elif creation_strategy == 'by_row' and individual_items:
            # Create one work order per row
            for item in individual_items:
                try:
                    wo_name = create_work_order_from_line_items(
                        [item],
                        production_item,
                        company,
                        bom_no,
                        planned_start_date
                    )
                    created_work_orders.append(wo_name)
                except Exception as e:
                    errors.append({
                        "item": item,
                        "error": str(e)
                    })
        
        return {
            "created_work_orders": created_work_orders,
            "errors": errors,
            "success_count": len(created_work_orders),
            "error_count": len(errors)
        }
    
    except Exception as e:
        frappe.throw(_("Error creating work orders: {0}").format(str(e)))

@frappe.whitelist()
def get_production_items_from_sales_orders(sales_orders):
    """
    Get unique production items from selected sales orders
    """
    sales_orders = frappe.parse_json(sales_orders) if isinstance(sales_orders, str) else sales_orders
    
    if not sales_orders:
        return []
    
    # Get all items from selected sales orders
    items = frappe.get_all(
        "Sales Order Item",
        filters={
            "parent": ["in", sales_orders],
            "custom_pending_qty_for_work_order": [">", 0]  # Only items with pending quantity
        },
        fields=["item_code", "item_name"],
        group_by="item_code"
    )
    
    return items

@frappe.whitelist()
def get_sales_order_summary(sales_orders):
    """
    Get summary information about selected sales orders
    """
    sales_orders = frappe.parse_json(sales_orders) if isinstance(sales_orders, str) else sales_orders
    
    if not sales_orders:
        return {}
    
    # Get sales order details
    orders_data = frappe.get_all(
        "Sales Order",
        filters={"name": ["in", sales_orders]},
        fields=["name", "customer", "transaction_date", "delivery_date", "grand_total"]
    )
    
    # Get item summary
    items_data = frappe.db.sql("""
        SELECT 
            soi.item_code,
            soi.item_name,
            SUM(soi.custom_pending_qty_for_work_order) as total_pending_qty,
            COUNT(DISTINCT soi.parent) as order_count
        FROM `tabSales Order Item` soi
        WHERE soi.parent IN ({0})
        AND soi.custom_pending_qty_for_work_order > 0
        GROUP BY soi.item_code, soi.item_name
        ORDER BY soi.item_code
    """.format(', '.join(['%s'] * len(sales_orders))), sales_orders, as_dict=True)
    
    return {
        "orders": orders_data,
        "items": items_data,
        "total_orders": len(orders_data),
        "total_value": sum(order.grand_total for order in orders_data)
    }

@frappe.whitelist()
def validate_orders_for_work_order(sales_orders):
    """
    Validate that selected sales orders are eligible for work order creation
    """
    sales_orders = frappe.parse_json(sales_orders) if isinstance(sales_orders, str) else sales_orders
    
    if not sales_orders:
        return {"valid": False, "message": "No sales orders selected"}
    
    # Check if orders are submitted
    unsubmitted = frappe.get_all(
        "Sales Order",
        filters={
            "name": ["in", sales_orders],
            "docstatus": ["!=", 1]
        },
        fields=["name"]
    )
    
    if unsubmitted:
        return {
            "valid": False, 
            "message": f"These orders are not submitted: {', '.join([o.name for o in unsubmitted])}"
        }
    
    # Check if orders have items with pending quantity
    orders_with_pending = frappe.db.sql("""
        SELECT DISTINCT soi.parent
        FROM `tabSales Order Item` soi
        WHERE soi.parent IN ({0})
        AND soi.custom_pending_qty_for_work_order > 0
    """.format(', '.join(['%s'] * len(sales_orders))), sales_orders)
    
    orders_with_pending = [row[0] for row in orders_with_pending]
    orders_without_pending = set(sales_orders) - set(orders_with_pending)
    
    if orders_without_pending:
        return {
            "valid": False,
            "message": f"These orders have no pending items: {', '.join(orders_without_pending)}"
        }
    
    # Check for cancelled/closed orders
    invalid_status = frappe.get_all(
        "Sales Order",
        filters={
            "name": ["in", sales_orders],
            "status": ["in", ["Cancelled", "Closed", "On Hold"]]
        },
        fields=["name", "status"]
    )
    
    if invalid_status:
        return {
            "valid": False,
            "message": f"These orders have invalid status: {', '.join([f'{o.name} ({o.status})' for o in invalid_status])}"
        }
    
    return {"valid": True, "message": "All selected orders are valid for work order creation"}

@frappe.whitelist()
def get_work_order_preview(sales_orders, production_item):
    """
    Get preview of what the work order would look like before creation
    """
    sales_orders = frappe.parse_json(sales_orders) if isinstance(sales_orders, str) else sales_orders
    
    if not sales_orders or not production_item:
        return {}
    
    # Get line items that would be created
    line_items = []
    total_qty = 0
    
    all_items = frappe.get_all(
        "Sales Order Item",
        filters={
            "parent": ["in", sales_orders],
            "item_code": production_item,
            "custom_pending_qty_for_work_order": [">", 0]
        },
        fields=[
            "name", "parent", "custom_lineitem", "custom_size", "qty",
            "custom_allocated_qty_for_work_order", "custom_pending_qty_for_work_order"
        ]
    )
    
    for item in all_items:
        line_items.append({
            "sales_order": item.parent,
            "line_item_no": item.custom_lineitem,
            "size": item.custom_size,
            "total_qty": item.qty,
            "pending_qty": item.custom_pending_qty_for_work_order,
            "suggested_allocation": min(1.0, flt(item.custom_pending_qty_for_work_order))
        })
        total_qty += min(1.0, flt(item.custom_pending_qty_for_work_order))
    
    # Get BOM info
    bom_info = frappe.db.get_value(
        "BOM",
        {"item": production_item, "is_active": 1, "docstatus": 1},
        ["name", "quantity", "uom"],
        as_dict=True
    )
    
    return {
        "line_items": line_items,
        "total_qty": total_qty,
        "bom_info": bom_info,
        "production_item": production_item,
        "sales_orders_count": len(sales_orders)
    }

@frappe.whitelist()
def get_related_work_orders(sales_order):
    """
    Get existing work orders that reference this sales order
    """
    related_work_orders = frappe.db.sql("""
        SELECT wo.name, wo.status, wo.qty, wo.produced_qty, wo.creation
        FROM `tabWork Order` wo
        INNER JOIN `tabWork Order Sales Orders` woso ON wo.name = woso.parent
        WHERE woso.sales_order = %s
        ORDER BY wo.creation DESC
    """, sales_order, as_dict=True)
    
    return related_work_orders

def populate_work_order_line_items(work_order_doc):
    """
    Populate work order line items based on selected sales orders
    This mimics the client-side sync_work_order_line_items function
    """
    if not work_order_doc.custom_sales_orders or not work_order_doc.production_item:
        return
    
    sales_orders = [row.sales_order for row in work_order_doc.custom_sales_orders]
    
    # Get sales order items using the same API method
    so_items = get_sales_order_items(
        work_order_doc.name,
        sales_orders,
        work_order_doc.production_item
    )
    
    # Clear existing line items
    work_order_doc.custom_work_order_line_items = []
    
    # Add line items
    total_qty = 0
    for item in so_items:
        line_item = work_order_doc.append("custom_work_order_line_items")
        line_item.sales_order_item = item.name
        line_item.line_item_no = item.custom_lineitem
        line_item.size = item.custom_size
        line_item.qty = item.qty
        line_item.already_allocated_qty = item.custom_allocated_qty_for_work_order
        line_item.pending_qty = item.custom_pending_qty_for_work_order
        line_item.work_order_allocated_qty = min(1.0, flt(item.custom_pending_qty_for_work_order))  # Default to 1 or pending qty, whichever is smaller
        line_item.sales_order = item.parent
        
        total_qty += line_item.work_order_allocated_qty
    
    # Update total quantity
    work_order_doc.qty = total_qty