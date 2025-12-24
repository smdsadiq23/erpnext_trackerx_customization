import frappe
from frappe import _
from frappe.utils import flt
from frappe.model.naming import set_name_by_naming_series

from cuttingx.cuttingx.utils.process_map_ops import (
    get_operations_from_process_map_core,
    build_operation_map_from_process_map,
    populate_physical_cell_first_and_last_operations,
)

def autoname(doc, method):
    """
    Set document name:
    - If custom_work_order_no is provided, use it as the doc name.
    - Otherwise, use the standard naming series.
    """
    if doc.custom_work_order_no:
        doc.name = doc.custom_work_order_no
    else:
        # Use naming series defined in Work Order doctype
        set_name_by_naming_series(doc)


def validate(doc, method):
    validate_work_order_no(doc)
    calculate_total_qty(doc)
    validate_and_update_sales_order_items(doc)
    validate_work_order(doc)    

    #copy sales orders to sales order
    if doc.custom_work_order_line_items:
        if doc.custom_work_order_line_items[0].sales_order:
            doc.sales_order = doc.custom_work_order_line_items[0].sales_order

def before_submit(doc, method):
    """
    On submit:
    - If TrackerX Live Settings.op_map_source == 'Work Order'
      and custom_operation_map_name is set, build Operation Map rows
      and populate Physical Cell first/last operations for this Work Order.
    """

    validate_operation_map_required(doc) 

    try:
        settings = frappe.get_single("TrackerX Live Settings")
        op_map_source = getattr(settings, "op_map_source", None) or "Cut Kit Plan"
    except Exception:
        op_map_source = "Cut Kit Plan"

    # Only act in Work Order mode
    if op_map_source != "Work Order":
        return

    # # If no Process Map selected on Work Order, just skip (not required as we are validating the same via validate_operation_map_required)
    # if not getattr(doc, "custom_operation_map_name", None):
    #     return

    # 1) Build Operation Map rows under this Work Order from Process Map
    #    Uses cuttingx.cuttingx.utils.process_map_ops.build_operation_map_from_process_map
    build_operation_map_from_process_map(
        doc,
        process_map_field="custom_operation_map_name",
        op_map_child_table="custom_operation_map_list",
        last_operation_field="custom_last_operation",
        # If you later add a production_type on WO, pass it here:
        # production_type=getattr(doc, "custom_production_type", None),
    )

    # 2) Populate Physical Cell first & last operations from the Operation Map
    populate_physical_cell_first_and_last_operations(
        doc,
        op_map_child_table="custom_operation_map_list",
        dest_child_table="custom_physical_cell_first_and_last_operation",
        physical_cell_field="physical_cell",
        first_op_field="first_operation",
        last_op_field="last_operation",
    )

def on_submit(doc, method):
    pass    

def on_trash(doc, method):
    manage_work_order_delete(doc, method)

def validate_work_order_no(doc):
    if doc.custom_work_order_no:
        existing = frappe.db.exists(
            "Work Order",
            {
                "custom_work_order_no": doc.custom_work_order_no,
                "name": ("!=", doc.name)
            }
        )
        if existing:
            frappe.throw(
                _("Work Order with Number '{0}' already exists.").format(
                    doc.custom_work_order_no, existing
                ),
                title=_("Duplicate Work Order No")
            )    

def manage_work_order_delete(doc, method):
    update_sales_order_pending_qty_by_work_order(doc)

def update_sales_order_pending_qty_by_work_order(doc):
    if not doc.custom_work_order_line_items:
        return

    for line in doc.custom_work_order_line_items:
        if not line.sales_order or not line.sales_order_item:
            continue

        # Get existing allocated and pending qty from Sales Order Item
        soi = frappe.db.get_value(
            "Sales Order Item",
            line.sales_order_item,
            ["custom_allocated_qty_for_work_order", "custom_pending_qty_for_work_order"],
            as_dict=True
        )

        if not soi:
            continue

        updated_allocated = flt(soi.custom_allocated_qty_for_work_order) - flt(line.work_order_allocated_qty)
        updated_pending = flt(soi.custom_pending_qty_for_work_order) + flt(line.work_order_allocated_qty)

        # Ensure we don't go below zero
        updated_allocated = max(updated_allocated, 0)
        updated_pending = max(updated_pending, 0)

        frappe.db.set_value("Sales Order Item", line.sales_order_item, {
            "custom_allocated_qty_for_work_order": updated_allocated,
            "custom_pending_qty_for_work_order": updated_pending
        })

    sales_orders = list(set(d.sales_order for d in doc.custom_work_order_line_items if d.sales_order))

    if not sales_orders:
        return
    
    recalculate_work_orders_pending_qty(sales_orders)


def calculate_total_qty(doc):
    doc.qty = sum(flt(item.work_order_allocated_qty) for item in doc.custom_work_order_line_items)


def validate_work_order(doc):
    """
    Defensive validation for Work Order:

    - Normalize None to 0.0 for available qty fields
    - Ensure available qty fields are non-negative numbers
    - Optionally ensure required_qty <= total available qty
    - Clean up bad warehouse values like 0 -> None / ""
    """
    for row in doc.get("required_items") or []:
        # --- 1) Normalize and validate available qty fields ---
        for field in ("available_qty_at_source_warehouse", "available_qty_at_wip_warehouse"):
            raw_val = row.get(field)

            # Treat None / empty string as 0
            if raw_val in (None, ""):
                val = 0.0
            else:
                val = flt(raw_val)

            # Disallow negative values
            if val < 0:
                frappe.throw(
                    _("Row #{0}: {1} cannot be negative (value: {2}) for item {3}.").format(
                        row.idx,
                        frappe.bold(field),
                        val,
                        frappe.bold(row.item_code or row.name)
                    )
                )

            setattr(row, field, val)

        # --- 2) Clean up bad warehouse values like 0 (int) ---
        # In your JSON we saw `"source_warehouse": 0`, which is not a valid Link.
        if getattr(row, "source_warehouse", None) == 0:
            row.source_warehouse = None
        if getattr(row, "wip_warehouse", None) == 0:
            row.wip_warehouse = None

        # # --- 3) Business rule: required qty vs available qty (optional but recommended) ---
        # required_qty = flt(row.get("required_qty"))
        # total_available = flt(row.available_qty_at_source_warehouse) + flt(row.available_qty_at_wip_warehouse)

        # # If you want hard validation (no over-allocation), keep this block.
        # # If you only want a warning, you can use frappe.msgprint instead.
        # if required_qty > total_available and required_qty > 0:
        #     frappe.throw(
        #         _(
        #             "Row #{0}: Required Qty {1} for item {2} "
        #             "cannot be greater than total available qty ({3}) "
        #             "at Source + WIP warehouses."
        #         ).format(
        #             row.idx,
        #             frappe.bold(required_qty),
        #             frappe.bold(row.item_code or row.name),
        #             frappe.bold(total_available),
        #         )
        #     )

        # # --- 4) At least one warehouse must be set if required_qty > 0 ---
        # if required_qty > 0 and not (row.get("source_warehouse") or row.get("wip_warehouse")):
        #     frappe.throw(
        #         _(
        #             "Row #{0}: Either Source Warehouse or WIP Warehouse must be set "
        #             "for item {1} when Required Qty is greater than 0."
        #         ).format(
        #             row.idx,
        #             frappe.bold(row.item_code or row.name),
        #         )
        #     )
 

def validate_and_update_sales_order_items(doc):
    if not doc.custom_work_order_line_items:
        return

    # Step 1: Extract sales orders from current doc's line items
    sales_orders = list(set(d.sales_order for d in doc.custom_work_order_line_items if d.sales_order))

    if not sales_orders:
        return

    # Step 2: Get all other Work Orders that reference these sales orders (excluding current one)
    related_wo_names = frappe.get_all(
        "Work Order Sales Orders",
        filters={"sales_order": ["in", sales_orders]},
        fields=["parent"]
    )

    other_wo_names = list(set([r.parent for r in related_wo_names if r.parent != doc.name]))

    allocations = {}

    # Step 3: Include current Work Order lines
    for line in doc.custom_work_order_line_items:
        key = (line.sales_order, line.sales_order_item, line.line_item_no, line.size)
        allocations[key] = allocations.get(key, 0) + flt(line.work_order_allocated_qty)

    # Step 4: Include allocations from other Work Orders
    for wo_name in other_wo_names:
        wo_doc = frappe.get_doc("Work Order", wo_name)
        for line in wo_doc.custom_work_order_line_items:
            key = (line.sales_order, line.sales_order_item, line.line_item_no, line.size)
            allocations[key] = allocations.get(key, 0) + flt(line.work_order_allocated_qty)

    # Step 5: Update Sales Order Items
    sales_order_items_pending_qty = {}
    for (sales_order, sales_order_item, line_item_no, size), total_allocated in allocations.items():
        soi = frappe.get_all(
            "Sales Order Item",
            filters={
                "parent": sales_order,
                "name": sales_order_item,
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

        sales_order_items_pending_qty[soi_name] = pending_qty

    
    # Step 6: Update all work order line items including this workorder that uses the sales order line item, updatepending qty, qty and already allocated qty
    recalculate_work_orders_pending_qty(sales_orders)

    # Step 7 update for current work order line items since its not saved
    for row in doc.custom_work_order_line_items:
        row.pending_qty = sales_order_items_pending_qty[row.sales_order_item]
        row.already_allocated_qty = row.qty - row.pending_qty


def validate_operation_map_required(doc):
    """
    If TrackerX Live Settings.op_map_source == 'Work Order',
    then Work Order.custom_operation_map_name is mandatory.
    """
    try:
        settings = frappe.get_single("TrackerX Live Settings")
        op_map_source = getattr(settings, "op_map_source", None) or "Cut Kit Plan"
    except Exception:
        # If settings not available, default to CKP and don't block
        op_map_source = "Cut Kit Plan"

    if op_map_source == "Work Order" and not getattr(doc, "custom_operation_map_name", None):
        frappe.throw(
            _("Operation Map is mandatory for Work Order when route source is set to 'Work Order' "
              "in TrackerX Live Settings."),
            title=_("Operation Map Required")
        )        


def recalculate_work_orders_pending_qty(sales_orders):
    if not sales_orders:
        return

    # Get all relevant Work Order Line Items and their linked sales_order_item
    work_order_line_items = frappe.get_all(
        "Work Order Line Item",
        filters={"sales_order": ["in", sales_orders]},
        fields=["name", "sales_order_item"]
    )

    for item in work_order_line_items:
        if not item.sales_order_item:
            continue
        
        # Fetch Sales Order Item document
        soi = frappe.db.get_value(
            "Sales Order Item",
            item.sales_order_item,
            ["custom_pending_qty_for_work_order", "custom_allocated_qty_for_work_order", "qty"],
            as_dict=True
        )

        if not soi:
            continue

        frappe.db.set_value("Work Order Line Item", item.name, {
            "pending_qty": flt(soi.custom_pending_qty_for_work_order),
            "already_allocated_qty": flt(soi.custom_allocated_qty_for_work_order),
            "qty": flt(soi.qty)  # if you want to sync qty too
        })


@frappe.whitelist()
def get_operations_from_process_map(process_map_name):
    """
    Whitelisted wrapper that delegates to the shared util.

    For Work Order client scripts, call:

      erpnext_trackerx_customization.overrides.work_order.get_operations_from_process_map

    to get the ordered list of operations from the selected Process Map.
    """
    if not process_map_name:
        return []
    return get_operations_from_process_map_core(process_map_name)        