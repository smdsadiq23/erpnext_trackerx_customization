# custom_pick_list.py
import frappe
from frappe import _
from frappe.utils import flt, cint
from erpnext.stock.doctype.pick_list.pick_list import PickList
from erpnext.stock.utils import get_stock_balance

class CustomPickList(PickList):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def validate(self):
        # Override parent validation to skip work order validations
        self.validate_trims_order()
        # self.validate_item_locations()
        # self.validate_warehouse_permission()
        
    def on_submit(self):
        # Custom validation on submit for stock availability
        self.validate_stock_availability_on_submit()
        super().on_submit()
    
    def before_save(self):
        # Skip the parent's before_save auto-location logic
        self.update_status()
        if self.get("locations"):
            # Only validate sales order percentage if applicable
            if hasattr(self, 'validate_sales_order_percentage'):
                self.validate_sales_order_percentage()
    
    def validate_trims_order(self):
        """Validate Trims Order selection and populate items"""
        if not self.custom_trims_order:
            frappe.throw(_("Please select a Trims Order"))

        # check if the pick list already created for this Trims order?
        # Block if a non-cancelled Pick List already exists
        existing = frappe.db.exists(
            "Pick List",
            {"custom_trims_order": self.custom_trims_order, "docstatus": ("!=", 2)}  # 2 = Cancelled
        )
        if existing:
            frappe.throw(f"A Pick List already exists for Trims Order {self.custom_trims_order}: {existing}")

        
        # Validate if Trims Order exists and is valid
        trims_order_doc = frappe.get_doc("Trims Order", self.custom_trims_order)
        if trims_order_doc.docstatus != 1:
            frappe.throw(_("Trims Order must be submitted before creating Pick List"))
    
    def populate_item_locations_from_trims_order(self):
        """Populate item locations based on selected Trims Order"""
        if not self.custom_trims_order:
            return
        
        # Clear existing locations
        self.set('locations', [])
        
        trims_order_doc = frappe.get_doc("Trims Order", self.custom_trims_order)
        
        for detail in trims_order_doc.table_trims_order_details:
            # Get available warehouses for the item
            warehouses = self.get_available_warehouses_for_item(detail.item_code)
            
            for warehouse_info in warehouses:
                if warehouse_info.get('actual_qty', 0) > 0:
                    self.append('locations', {
                        'item_code': detail.item_code,
                        'warehouse': warehouse_info.get('warehouse'),
                        'qty': min(warehouse_info.get('actual_qty', 0), detail.required_quantity),
                        'uom': detail.uom,
                        'stock_qty': min(warehouse_info.get('actual_qty', 0), detail.required_quantity),
                        'serial_and_batch_bundle': '',
                        # Custom fields to track trims order details
                        'trims_order': self.custom_trims_order,
                        'sales_order': detail.sales_order,
                        'line_item_no': detail.line_item_no,
                        'size': detail.size,
                        'item_type': detail.item_type,
                        'required_quantity': detail.required_quantity
                    })
    
    def get_available_warehouses_for_item(self, item_code):
        """Get warehouses with available stock for an item"""
        warehouses = frappe.db.sql("""
            SELECT 
                warehouse,
                actual_qty,
                reserved_qty,
                (actual_qty - reserved_qty) as available_qty
            FROM `tabBin`
            WHERE item_code = %s 
            AND (actual_qty - reserved_qty) > 0
            ORDER BY actual_qty DESC
        """, (item_code,), as_dict=True)
        
        return warehouses
    
    def validate_stock_availability_on_submit(self):
        """Validate stock availability when submitting pick list"""
        if not self.locations:
            frappe.throw(_("No items to pick"))
        
        insufficient_items = []
        
        # Group locations by item_code to check total required vs available
        item_qty_map = {}
        for location in self.locations:
            item_code = location.item_code
            if item_code not in item_qty_map:
                item_qty_map[item_code] = {
                    'required_qty': 0,
                    'picked_qty': 0,
                    'warehouses': []
                }
            
            item_qty_map[item_code]['picked_qty'] += flt(location.qty)
            item_qty_map[item_code]['warehouses'].append({
                'warehouse': location.warehouse,
                'qty': location.qty
            })
        
        # Get required quantities from trims order
        if self.custom_trims_order:
            trims_order_doc = frappe.get_doc("Trims Order", self.custom_trims_order)
            for detail in trims_order_doc.table_trims_order_details:
                if detail.item_code in item_qty_map:
                    item_qty_map[detail.item_code]['required_qty'] = detail.required_quantity
        
        # Validate each item
        for item_code, qty_info in item_qty_map.items():
            # Check actual available stock
            total_available = 0
            for warehouse_info in qty_info['warehouses']:
                available_qty = get_stock_balance(
                    item_code, 
                    warehouse_info['warehouse'], 
                    self.posting_date
                )
                total_available += available_qty
                
                # Check if picked quantity exceeds available quantity in warehouse
                if flt(warehouse_info['qty']) > available_qty:
                    insufficient_items.append({
                        'item_code': item_code,
                        'warehouse': warehouse_info['warehouse'],
                        'required': warehouse_info['qty'],
                        'available': available_qty,
                        'shortage': flt(warehouse_info['qty']) - available_qty
                    })
            
            # Check if total picked quantity exceeds total available
            if qty_info['picked_qty'] > total_available:
                insufficient_items.append({
                    'item_code': item_code,
                    'warehouse': 'All Warehouses',
                    'required': qty_info['picked_qty'],
                    'available': total_available,
                    'shortage': qty_info['picked_qty'] - total_available
                })
        
        # Show error message if insufficient stock found
        if insufficient_items:
            error_msg = _("Insufficient Stock Found:") + "<br><br>"
            for item in insufficient_items:
                error_msg += _("Item: {0}<br>Warehouse: {1}<br>Required: {2}<br>Available: {3}<br>Shortage: {4}<br><br>").format(
                    frappe.bold(item['item_code']),
                    item['warehouse'],
                    item['required'],
                    item['available'],
                    frappe.bold(str(item['shortage']))
                )
            
            frappe.throw(error_msg, title=_("Insufficient Stock"))

# Method to be called from client side to populate items
@frappe.whitelist()
def get_trims_order_items(trims_order):
    """Get items from Trims Order for Pick List"""
    if not trims_order:
        return []
    
    trims_order_doc = frappe.get_doc("Trims Order", trims_order)
    items = []

    frappe.log(f"get trimgs order items for {trims_order}")

    frappe.log(f"table_trims_order_details: {trims_order_doc.table_trims_order_details}")
    
    item_codes = [row.item_code for row in trims_order_doc.table_trims_order_details]
    unique_item_codes = list(set(item_codes))

    # 2. Fetch all item details in a single database call
    # This is much more efficient than looping and fetching one by one
    item_details = frappe.get_all(
        "Item",
        filters={"item_code": ["in", unique_item_codes]},
        fields=["item_code", "item_name", "item_group"]
    )

    # 3. Create a dictionary for easy lookup
    # The item_code will be the key
    item_info_dict = {d.item_code: d for d in item_details}


    for detail in trims_order_doc.table_trims_order_details:

        items.append({
                    'sales_order': detail.sales_order,
                    'line_item_no': detail.line_item_no,
                    'size': detail.size,
                    'item_type': detail.item_type,
                    'item_code': detail.item_code,
                    'item_name': item_info_dict.get(detail.item_code).item_name,
                    'item_group': item_info_dict.get(detail.item_code).item_group,
                    'uom': detail.uom,
                    'per_unit_quantity': detail.per_unit_quantity,
                    'wo_quantity': detail.wo_quantity,
                    'already_issued_quantity': detail.already_issued_quantity,
                    'trims_order_quantity': detail.trims_order_quantity,
                    'required_quantity': detail.required_quantity,
                })
        # # Get available warehouses for the item
        # warehouses = frappe.db.sql("""
        #     SELECT 
        #         warehouse,
        #         actual_qty,
        #         reserved_qty,
        #         (actual_qty - reserved_qty) as available_qty
        #     FROM `tabBin`
        #     WHERE item_code = %s 
        #     AND (actual_qty - reserved_qty) > 0
        #     ORDER BY actual_qty DESC
        # """, (detail.item_code,), as_dict=True)
        
        # for warehouse_info in warehouses:
        #     if warehouse_info.get('available_qty', 0) > 0:
        #         items.append({
        #             'item_code': detail.item_code,
        #             'warehouse': warehouse_info.get('warehouse'),
        #             'qty': min(warehouse_info.get('available_qty', 0), detail.required_quantity),
        #             'uom': detail.uom,
        #             'stock_qty': min(warehouse_info.get('available_qty', 0), detail.required_quantity),
        #             'available_qty': warehouse_info.get('available_qty', 0),
        #             'required_quantity': detail.required_quantity,
        #             'sales_order': detail.sales_order,
        #             'line_item_no': detail.line_item_no,
        #             'size': detail.size,
        #             'item_type': detail.item_type
        #         })
    
    return items

# Helper function to update pick list with trims order items
@frappe.whitelist()
def update_pick_list_items(pick_list_name, trims_order):
    """Update Pick List items based on Trims Order"""
    pick_list_doc = frappe.get_doc("Pick List", pick_list_name)
    
    # Clear existing locations
    pick_list_doc.set('locations', [])
    
    # Get items from trims order
    items = get_trims_order_items(trims_order)
    
    # Add items to pick list
    for item in items:
        pick_list_doc.append('locations', {
            'item_code': item['item_code'],
            'warehouse': item['warehouse'],
            'qty': item['qty'],
            'uom': item['uom'],
            'stock_qty': item['stock_qty']
        })
    
    pick_list_doc.trims_order = trims_order
    pick_list_doc.save()
    
    return pick_list_doc