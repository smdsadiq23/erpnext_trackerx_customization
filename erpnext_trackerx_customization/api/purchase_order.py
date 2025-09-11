# API for Purchase Order customization
# File: erpnext_trackerx_customization/api/purchase_order.py

import frappe
from frappe import _
from frappe.utils import flt

@frappe.whitelist()
def get_items_from_material_requirement_plan(material_requirement_plan, source_table="Items Summary", purchase_order=None):
    """
    Get items from Material Requirement Plan and its child tables
    """
    if not material_requirement_plan:
        frappe.throw(_("Material Requirement Plan is required"))
    
    # Get the Material Requirement Plan document
    mrp_doc = frappe.get_doc('Material Requirement Plan', material_requirement_plan)
    
    items = []
    
    if source_table == "Items":
        # Get items from the main items table (Material Requirement Plan Item)
        for item in mrp_doc.items:
            items.append(prepare_po_item(item, mrp_doc))
    
    elif source_table == "Items Summary":
        # Get items from items_summary table (Material Request Items Summary)
        for item in mrp_doc.items_summary:
            items.append(prepare_po_item_from_summary(item, mrp_doc))
    
    return items

def prepare_po_item(mrp_item, mrp_doc):
    """
    Prepare Purchase Order item from Material Requirement Plan Item
    """
    # Get item details
    item_doc = frappe.get_doc('Item', mrp_item.item_code)
    
    # Calculate rate - you may want to modify this logic
    rate = get_item_rate(mrp_item.item_code, mrp_doc.company)
    
    po_item = {
        'item_code': mrp_item.item_code,
        'item_name': mrp_item.item_name,
        'description': mrp_item.description,
        'qty': mrp_item.qty,
        'uom': mrp_item.uom,
        'stock_uom': mrp_item.stock_uom,
        'conversion_factor': mrp_item.conversion_factor or 1,
        'rate': rate,
        'amount': flt(mrp_item.qty) * flt(rate),
        'schedule_date': mrp_item.schedule_date or frappe.utils.today(),
        'warehouse': mrp_item.warehouse,
        'material_requirement_plan': mrp_doc.name,
        'material_requirement_plan_item': mrp_item.name,
        'project': mrp_doc.project if hasattr(mrp_doc, 'project') else None,
        'reference_id': mrp_item.name,
        'reference_type': 'MRP',
        'custom_reference_parent_id': mrp_doc.name
    }
    
    return po_item

def prepare_po_item_from_summary(summary_item, mrp_doc):
    """
    Prepare Purchase Order item from Material Request Items Summary
    """
    # Get item details
    item_doc = frappe.get_doc('Item', summary_item.item_code)
    
    # Calculate rate
    rate = get_item_rate(summary_item.item_code, mrp_doc.company)
    
    po_item = {
        'item_code': summary_item.item_code,
        'item_name': item_doc.item_name,
        'description': summary_item.description if hasattr(summary_item, 'description') else item_doc.description,
        'qty': summary_item.quantity,
        'uom': summary_item.uom or item_doc.custom_uom or item_doc.stock_uom,
        'stock_uom': item_doc.stock_uom,
        'conversion_factor': 1,  # You may want to calculate this
        'rate': rate,
        'amount': flt(summary_item.quantity) * flt(rate),
        'schedule_date': frappe.utils.today(),  # Set appropriate date
        'warehouse': summary_item.warehouse if hasattr(summary_item, 'warehouse') else None,
        'material_requirement_plan': mrp_doc.name,
        'material_requirement_plan_summary_item': summary_item.name,
        'project': mrp_doc.project if hasattr(mrp_doc, 'project') else None,
        'required_by': summary_item.required_by if hasattr(summary_item, 'required_by') else None,
        'custom_reference_id': summary_item.name,
        'custom_reference_type': 'MRP',
        'custom_reference_parent_id': mrp_doc.name
    }
    
    return po_item

def get_item_rate(item_code, company):
    """
    Get item rate from Item Price or Last Purchase Rate
    """
    # First try to get from Item Price
    item_price = frappe.db.get_value('Item Price', {
        'item_code': item_code,
        'buying': 1,
        'currency': frappe.get_cached_value('Company', company, 'default_currency')
    }, 'price_list_rate')
    
    if item_price:
        return item_price
    
    # If no item price, try to get last purchase rate
    last_purchase_rate = frappe.db.get_value('Purchase Order Item', {
        'item_code': item_code,
        'docstatus': 1
    }, 'rate', order_by='creation desc')
    
    if last_purchase_rate:
        return last_purchase_rate
    
    # If nothing found, get valuation rate
    valuation_rate = frappe.db.get_value('Item', item_code, 'valuation_rate')
    
    return valuation_rate or 0




# File: erpnext_trackerx_customization/api/purchase_order.py

import frappe
from frappe.model.mapper import get_mapped_doc

@frappe.whitelist()
def make_goods_receipt_note(source_name, target_doc=None):
    def set_missing_values(source, target):
        target.run_method("set_missing_values")
        target.run_method("calculate_taxes_and_totals")

    def update_item(source_doc, target_doc, source_parent):
        target_doc.qty = source_doc.qty - source_doc.received_qty
        target_doc.ordered_quantity = source_doc.qty
        target_doc.received_quantity = source_doc.qty - source_doc.received_qty
        
        # Copy custom fields if they exist
        if hasattr(source_doc, 'color'):
            target_doc.color = source_doc.color
        if hasattr(source_doc, 'composition'):
            target_doc.composition = source_doc.composition
        if hasattr(source_doc, 'material_type'):
            target_doc.material_type = source_doc.material_type
        # Add other custom field mappings as needed

    doc = get_mapped_doc("Purchase Order", source_name, {
        "Purchase Order": {
            "doctype": "Goods Receipt Note",
            "field_map": {
                "supplier": "supplier",
                "supplier_name": "supplier_name",
                "company": "company",
                "currency": "currency",
                "buying_price_list": "buying_price_list",
            },
            "validation": {
                "docstatus": ["=", 1]
            }
        },
        "Purchase Order Item": {
            "doctype": "Goods Receipt Item",
            "field_map": {
                "name": "purchase_order_item",
                "parent": "purchase_order",
                "item_code": "item_code",
                "uom": "uom",
                "warehouse": "accepted_warehouse",
                "rate": "rate",
                "amount": "amount",
            },
            "postprocess": update_item,
            "condition": lambda doc: doc.received_qty < doc.qty
        }
    }, target_doc, set_missing_values)

    return doc


@frappe.whitelist()
def get_fg_components_by_item(item_code):
    """
    Returns list of component_name from Item's custom_fg_components child table.
    Safe for client-side use — no permission checks on child table.
    """
    if not item_code:
        return []

    # Fetch child table records — no permission check needed in server method
    components = frappe.get_all(
        "FG Components",  # ⚠️ REPLACE WITH YOUR ACTUAL CHILD TABLE DOCTYPE
        filters={
            "parent": item_code,
            "parentfield": "custom_fg_components",
            "parenttype": "Item"
        },
        fields=["name"],
        order_by="idx"
    )

    # Return list of names
    return [c.name for c in components]


@frappe.whitelist()
def get_suppliers_by_process_type(process_type):
    """
    Returns list of Supplier names who have given process_type in their custom_process_specialization
    """
    if not process_type:
        return []

    # Fetch suppliers from child table
    supplier_names = frappe.get_all(
        "Supplier Specialization",  # ← Child Table Doctype Name (verify this!)
        filters={
            "process_type": process_type,
            "parenttype": "Supplier",
            "parentfield": "custom_process_specialization"
        },
        fields=["parent"],
        distinct=True
    )

    return [s.parent for s in supplier_names if s.parent]


@frappe.whitelist()
def get_supplier_rate_for_process(supplier, process_type):
    """
    Returns rate_per_unit from Supplier Specialization for given supplier + process_type
    """
    if not supplier or not process_type:
        return None

    rate = frappe.db.get_value(
        "Supplier Specialization",  # ← Verify this is your actual child table doctype
        {
            "parent": supplier,
            "process_type": process_type,
            "parenttype": "Supplier",
            "parentfield": "custom_process_specialization"
        },
        "rate_per_unit"
    )

    return rate