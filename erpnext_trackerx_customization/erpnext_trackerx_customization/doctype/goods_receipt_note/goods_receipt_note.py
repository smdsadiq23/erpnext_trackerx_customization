# Copyright (c) 2025, CognitionX and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

class GoodsReceiptNote(Document):
    def before_validate(self):
        """Apply putaway rules if checkbox is enabled"""
        if self.get("items") and self.apply_putaway_rule and not self.get("is_return"):
            try:
                # Store original warehouse assignments to detect changes
                original_warehouses = {}
                for item in self.items:
                    original_warehouses[id(item)] = getattr(item, 'warehouse', None) or getattr(item, 'accepted_warehouse', None)
                
                # Prepare items for putaway rule application
                self.prepare_items_for_putaway()
                
                # Apply capacity-aware putaway rules
                self.apply_capacity_aware_putaway_rules()
                
                # Set putaway_rule field for items where warehouse was assigned
                self.set_applied_putaway_rules(original_warehouses)
                
                # Track which rules were applied
                self.track_applied_putaway_rules()
                
            except Exception as e:
                # Log error but don't block the transaction
                frappe.log_error(f"Error applying putaway rules in Goods Receipt Note {self.name}: {str(e)}")
                frappe.msgprint(_("Warning: Could not apply putaway rules. Error: {0}").format(str(e)), 
                               alert=True, indicator="orange")
    
    def prepare_items_for_putaway(self):
        """Prepare items with required fields for putaway rule application"""
        for item in self.items:
            # Add conversion_factor if missing (required by putaway rule)
            if not hasattr(item, 'conversion_factor') or not item.conversion_factor:
                item.conversion_factor = 1.0
            
            # Add rate if missing
            if not hasattr(item, 'rate') or not item.rate:
                item.rate = 0.0
            
            # Map received_quantity to qty (required by putaway rule)
            if not hasattr(item, 'qty') or not item.qty:
                if hasattr(item, 'received_quantity') and item.received_quantity:
                    item.qty = item.received_quantity
                else:
                    item.qty = 0.0
            
            # Map received_quantity to stock_qty (required by putaway rule)
            if not hasattr(item, 'stock_qty') or not item.stock_qty:
                if hasattr(item, 'received_quantity') and item.received_quantity:
                    item.stock_qty = item.received_quantity
                else:
                    item.stock_qty = 0.0
            
            # Map received_quantity to received_qty (sometimes required by putaway rule)
            if not hasattr(item, 'received_qty') or not item.received_qty:
                if hasattr(item, 'received_quantity') and item.received_quantity:
                    item.received_qty = item.received_quantity
                else:
                    item.received_qty = 0.0
            
            # Map accepted_warehouse to warehouse (if accepted_warehouse exists and warehouse doesn't)
            if not hasattr(item, 'warehouse') or not item.warehouse:
                if hasattr(item, 'accepted_warehouse') and item.accepted_warehouse:
                    item.warehouse = item.accepted_warehouse
                else:
                    item.warehouse = None
    
    def set_applied_putaway_rules(self, original_warehouses):
        """Set the putaway_rule field for items where warehouse was assigned by putaway rules"""
        for item in self.items:
            # Get current warehouse assignment
            current_warehouse = getattr(item, 'warehouse', None) or getattr(item, 'accepted_warehouse', None)
            original_warehouse = original_warehouses.get(id(item))
            
            # If warehouse was assigned/changed by putaway rule
            if current_warehouse and current_warehouse != original_warehouse:
                # Find the putaway rule that was applied
                putaway_rule = frappe.db.get_value(
                    'Putaway Rule',
                    {
                        'item_code': item.item_code,
                        'warehouse': current_warehouse,
                        'company': self.company
                    },
                    'name'
                )
                
                if putaway_rule:
                    # Set the putaway_rule field
                    item.putaway_rule = putaway_rule
                    
                    # Also update accepted_warehouse if it wasn't set
                    if not getattr(item, 'accepted_warehouse', None):
                        item.accepted_warehouse = current_warehouse
    
    def apply_capacity_aware_putaway_rules(self):
        """Apply putaway rules with capacity awareness to prevent over-allocation"""
        try:
            # Track warehouse utilization during this transaction
            warehouse_utilization = {}  # {warehouse: utilized_capacity}
            
            for item in self.items:
                if not item.item_code:
                    continue
                    
                item_qty = getattr(item, 'qty', 0) or getattr(item, 'received_quantity', 0) or getattr(item, 'stock_qty', 0)
                if not item_qty:
                    continue
                
                # Get putaway rules for this item, ordered by priority
                putaway_rules = frappe.get_all(
                    "Putaway Rule",
                    filters={
                        "item_code": item.item_code,
                        "company": self.company,
                        "disable": 0
                    },
                    fields=["name", "warehouse", "capacity", "priority"],
                    order_by="priority ASC"
                )
                
                assigned_warehouse = None
                assigned_rule = None
                
                for rule in putaway_rules:
                    warehouse = rule.warehouse
                    rule_capacity = rule.capacity or 0
                    
                    # Get warehouse capacity
                    warehouse_info = frappe.db.get_value(
                        "Warehouse", 
                        warehouse, 
                        ["capacity", "capacity_unit"], 
                        as_dict=True
                    )
                    
                    if not warehouse_info or not warehouse_info.capacity:
                        continue
                        
                    warehouse_capacity = warehouse_info.capacity
                    
                    # Calculate current stock in warehouse
                    try:
                        from erpnext.stock.utils import get_stock_balance
                        current_stock = get_stock_balance(item.item_code, warehouse)
                    except:
                        current_stock = 0
                    
                    # Calculate utilization including items already processed in this transaction
                    transaction_utilization = warehouse_utilization.get(warehouse, 0)
                    total_after_assignment = current_stock + transaction_utilization + item_qty
                    
                    # Check if this assignment would exceed capacity
                    if total_after_assignment <= warehouse_capacity:
                        # Assign this warehouse
                        assigned_warehouse = warehouse
                        assigned_rule = rule.name
                        
                        # Track utilization for subsequent items
                        warehouse_utilization[warehouse] = transaction_utilization + item_qty
                        
                        frappe.msgprint(
                            _("Item {0}: Assigned to {1} (Capacity: {2}/{3})").format(
                                item.item_code, warehouse, total_after_assignment, warehouse_capacity
                            ),
                            alert=True,
                            indicator="green"
                        )
                        break
                    else:
                        # This warehouse would exceed capacity, try next rule
                        frappe.msgprint(
                            _("Item {0}: Warehouse {1} would exceed capacity ({2}/{3}), trying next rule...").format(
                                item.item_code, warehouse, total_after_assignment, warehouse_capacity
                            ),
                            alert=True,
                            indicator="orange"
                        )
                        continue
                
                # Assign the warehouse if found
                if assigned_warehouse:
                    item.warehouse = assigned_warehouse
                    item.accepted_warehouse = assigned_warehouse
                    # The putaway_rule field will be set by set_applied_putaway_rules
                else:
                    # No suitable warehouse found with capacity
                    frappe.throw(
                        _("No warehouse with sufficient capacity found for item {0} (quantity: {1}). "
                          "Available putaway rules could not accommodate this item without exceeding warehouse capacity.").format(
                            item.item_code, item_qty
                        ),
                        title=_("Insufficient Warehouse Capacity"),
                        exc=frappe.ValidationError
                    )
            
            # Log the final warehouse utilization
            frappe.msgprint(
                _("Warehouse Utilization Summary: {0}").format(
                    "; ".join([f"{wh}: +{util}" for wh, util in warehouse_utilization.items()])
                ),
                alert=True,
                indicator="blue"
            )
                        
        except frappe.ValidationError:
            raise
        except Exception as e:
            frappe.log_error(f"Error in capacity-aware putaway rule application: {str(e)}")
            frappe.throw(_("Error applying capacity-aware putaway rules: {0}").format(str(e)))
    
    def track_applied_putaway_rules(self):
        """Track which putaway rules were applied to items"""
        applied_rules = []
        
        for item in self.items:
            # Get the warehouse (could be warehouse or accepted_warehouse)
            assigned_warehouse = getattr(item, 'warehouse', None) or getattr(item, 'accepted_warehouse', None)
            # Get the quantity (could be qty, received_quantity, or stock_qty)
            item_qty = getattr(item, 'qty', 0) or getattr(item, 'received_quantity', 0) or getattr(item, 'stock_qty', 0)
            
            # Check if putaway rule was applied
            if hasattr(item, 'putaway_rule') and item.putaway_rule:
                applied_rules.append({
                    'item_code': item.item_code,
                    'warehouse': assigned_warehouse or 'Not Assigned',
                    'putaway_rule': item.putaway_rule,
                    'qty': item_qty
                })
            elif assigned_warehouse:
                # Check if warehouse was assigned (even without explicit putaway_rule field)
                putaway_rule = frappe.db.get_value('Putaway Rule', 
                    {'item_code': item.item_code, 'warehouse': assigned_warehouse}, 
                    'name')
                
                if putaway_rule:
                    applied_rules.append({
                        'item_code': item.item_code,
                        'warehouse': assigned_warehouse,
                        'putaway_rule': putaway_rule,
                        'qty': item_qty
                    })
        
        if applied_rules:
            # Show user-friendly message
            message = _("Putaway rules applied:\n")
            for rule in applied_rules:
                message += _("• {0}: {1} units → {2} (Rule: {3})\n").format(
                    rule['item_code'], rule['qty'], rule['warehouse'], rule['putaway_rule']
                )
            
            frappe.msgprint(message, alert=True, indicator="green", title=_("Putaway Rules Applied"))
            
            # Store for later reference
            self._applied_putaway_rules = applied_rules
        else:
            frappe.msgprint(_("No putaway rules were applied. Check if putaway rules exist for the items."), 
                          alert=True, indicator="orange")
    
    def validate(self):
        """Additional validation for Goods Receipt Note"""
        # Don't call super().validate() as Document doesn't have validate method
        
        self.validate_goods_receipt_note_no()

        # ALWAYS validate warehouse capacities (universal check)
        self.validate_all_warehouse_capacities()
        
        # Validate putaway rule application if enabled
        if self.apply_putaway_rule and self.get("items"):
            self.validate_putaway_rule_items()


    def validate_goods_receipt_note_no(self):
        if self.goods_receipt_note_no:
            existing = frappe.db.exists(
                "Goods Receipt Note",  # ✅ Correct doctype
                {
                    "goods_receipt_note_no": self.goods_receipt_note_no,
                    "name": ("!=", self.name)
                }
            )
            if existing:
                frappe.throw(
                    _("Goods Receipt Note with Number '{0}' already exists.").format(
                        self.goods_receipt_note_no
                    ),
                    title=_("Duplicate Goods Receipt Note No")
                )

    
    def validate_putaway_rule_items(self):
        """Validate items after putaway rule application"""
        try:
            # Check if any items have putaway_rule field populated
            items_with_putaway = [item for item in self.items if getattr(item, 'putaway_rule', None)]
            
            if items_with_putaway:
                frappe.msgprint(_("Applied putaway rules to {0} items").format(len(items_with_putaway)), 
                               alert=True, indicator="green")
            
            # Validate warehouse capacity if rules were applied
            for item in self.items:
                # Check both warehouse and accepted_warehouse fields
                item_warehouse = getattr(item, 'warehouse', None) or getattr(item, 'accepted_warehouse', None)
                if item_warehouse:
                    self.validate_item_warehouse_capacity(item)
                    
        except Exception as e:
            frappe.log_error(f"Error validating putaway rule items: {str(e)}")
    
    def validate_all_warehouse_capacities(self):
        """Universal warehouse capacity validation for ALL GRN saves (regardless of putaway rules)"""
        if not self.get("items"):
            return
            
        try:
            # Group items by warehouse and calculate total quantities
            warehouse_totals = {}  # {warehouse: {'items': [items], 'total_qty': total, 'capacity': capacity}}
            
            for item in self.items:
                # Get warehouse (could be warehouse, accepted_warehouse, or selected_warehouse)
                item_warehouse = (getattr(item, 'warehouse', None) or 
                                getattr(item, 'accepted_warehouse', None) or 
                                getattr(item, 'selected_warehouse', None))
                
                if not item_warehouse:
                    continue  # Skip items without warehouse assignment
                
                # Get item quantity
                item_qty = (getattr(item, 'qty', 0) or 
                          getattr(item, 'received_quantity', 0) or 
                          getattr(item, 'stock_qty', 0))
                
                if not item_qty:
                    continue  # Skip items without quantity
                
                # Initialize warehouse tracking
                if item_warehouse not in warehouse_totals:
                    warehouse_info = frappe.db.get_value(
                        "Warehouse", 
                        item_warehouse, 
                        ["capacity", "capacity_unit"], 
                        as_dict=True
                    )
                    
                    warehouse_totals[item_warehouse] = {
                        'items': [],
                        'total_qty': 0,
                        'capacity': warehouse_info.capacity if warehouse_info and warehouse_info.capacity else None,
                        'capacity_unit': warehouse_info.capacity_unit if warehouse_info else None
                    }
                
                # Add item to warehouse tracking
                warehouse_totals[item_warehouse]['items'].append({
                    'item_code': item.item_code,
                    'qty': item_qty
                })
                warehouse_totals[item_warehouse]['total_qty'] += item_qty
            
            # Check each warehouse for capacity violations
            capacity_violations = []
            
            for warehouse, data in warehouse_totals.items():
                if not data['capacity']:
                    continue  # Skip warehouses without capacity limits
                
                # Get current stock in warehouse
                try:
                    from erpnext.stock.utils import get_stock_balance
                    current_stock = 0
                    for item_data in data['items']:
                        current_stock += get_stock_balance(item_data['item_code'], warehouse)
                except:
                    current_stock = 0
                
                # Calculate total after this GRN
                total_after_grn = current_stock + data['total_qty']
                warehouse_capacity = data['capacity']
                
                if total_after_grn > warehouse_capacity:
                    # Capacity violation found
                    utilization_pct = (total_after_grn / warehouse_capacity) * 100
                    
                    violation_data = {
                        'warehouse': warehouse,
                        'current_stock': current_stock,
                        'grn_quantity': data['total_qty'],
                        'total_after': total_after_grn,
                        'capacity': warehouse_capacity,
                        'capacity_unit': data['capacity_unit'],
                        'utilization_pct': utilization_pct,
                        'excess': total_after_grn - warehouse_capacity,
                        'items': data['items']
                    }
                    capacity_violations.append(violation_data)
            
            # If violations found, throw detailed error
            if capacity_violations:
                self._throw_capacity_violation_error(capacity_violations)
                
        except frappe.ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            frappe.log_error(f"Error in universal warehouse capacity validation: {str(e)}")
            # Don't block transaction for unexpected errors, just log
            frappe.msgprint(
                _("Warning: Could not validate warehouse capacities. Error: {0}").format(str(e)),
                alert=True, 
                indicator="orange"
            )
    
    def _throw_capacity_violation_error(self, violations):
        """Throw detailed capacity violation error with enhanced formatting"""
        if len(violations) == 1:
            # Single warehouse violation
            violation = violations[0]
            
            # Build item details
            item_details = ""
            for item_data in violation['items']:
                item_details += f"• {item_data['item_code']}: {item_data['qty']} units<br>"
            
            error_msg = _(
                "🚫 <strong>Warehouse Capacity Exceeded</strong><br><br>"
                "🏢 <strong>Warehouse:</strong> {warehouse}<br>"
                "📊 <strong>Capacity:</strong> {capacity} {unit}<br>"
                "📦 <strong>Current Stock:</strong> {current}<br>"
                "📈 <strong>GRN Quantity:</strong> {grn_qty}<br>"
                "📊 <strong>Total After GRN:</strong> {total} ({utilization:.1f}%)<br>"
                "⚠️ <strong>Excess:</strong> {excess} units over capacity<br><br>"
                "📋 <strong>Items in this GRN:</strong><br>{items}<br>"
                "💡 <strong>Solution:</strong> Reduce quantities, choose different warehouse, or increase warehouse capacity."
            ).format(
                warehouse=violation['warehouse'],
                capacity=violation['capacity'],
                unit=violation['capacity_unit'] or 'units',
                current=violation['current_stock'],
                grn_qty=violation['grn_quantity'],
                total=violation['total_after'],
                utilization=violation['utilization_pct'],
                excess=violation['excess'],
                items=item_details
            )
            
            frappe.throw(
                error_msg,
                title=_("Warehouse Capacity Exceeded"),
                exc=frappe.ValidationError
            )
        else:
            # Multiple warehouse violations
            violation_summary = ""
            total_excess = 0
            
            for violation in violations:
                violation_summary += _(
                    "🏢 <strong>{warehouse}:</strong> {total}/{capacity} = {utilization:.1f}% "
                    "(+{excess} over capacity)<br>"
                ).format(
                    warehouse=violation['warehouse'],
                    total=violation['total_after'],
                    capacity=violation['capacity'],
                    utilization=violation['utilization_pct'],
                    excess=violation['excess']
                )
                total_excess += violation['excess']
            
            error_msg = _(
                "🚫 <strong>Multiple Warehouses Exceed Capacity</strong><br><br>"
                "{violations}<br>"
                "📊 <strong>Total Excess:</strong> {total_excess} units<br><br>"
                "💡 <strong>Solution:</strong> Redistribute items, reduce quantities, or increase warehouse capacities."
            ).format(
                violations=violation_summary,
                total_excess=total_excess
            )
            
            frappe.throw(
                error_msg,
                title=_("Multiple Warehouse Capacity Violations"),
                exc=frappe.ValidationError
            )
    
    def validate_item_warehouse_capacity(self, item):
        """Validate individual item against warehouse capacity"""
        try:
            # Get warehouse (could be warehouse or accepted_warehouse)
            item_warehouse = getattr(item, 'warehouse', None) or getattr(item, 'accepted_warehouse', None)
            if not item_warehouse:
                return
                
            # Get warehouse capacity
            warehouse_capacity = frappe.db.get_value("Warehouse", item_warehouse, "capacity")
            
            if warehouse_capacity:
                # Get current stock in warehouse
                from erpnext.stock.utils import get_stock_balance
                current_stock = get_stock_balance(item.item_code, item_warehouse)
                
                # Get item quantity (could be qty, received_quantity, or stock_qty)
                item_qty = getattr(item, 'qty', 0) or getattr(item, 'received_quantity', 0) or getattr(item, 'stock_qty', 0)
                
                # Calculate new total after this receipt
                new_total = current_stock + item_qty
                
                # Check if exceeds capacity
                if new_total > warehouse_capacity:
                    # Throw a validation error to block submission
                    frappe.throw(
                        _("Warehouse Capacity Exceeded: Item {0} in warehouse {1} will exceed capacity.<br><br>"
                          "Current Stock: {2}<br>"
                          "Adding Quantity: {3}<br>"
                          "Total After Receipt: {4}<br>"
                          "Warehouse Capacity: {5}<br><br>"
                          "Please reduce the quantity or choose a different warehouse.").format(
                            item.item_code, item_warehouse, current_stock, item_qty, new_total, warehouse_capacity
                        ),
                        title=_("Warehouse Capacity Validation Error"),
                        exc=frappe.ValidationError
                    )
                    
        except frappe.ValidationError:
            # Re-raise validation errors to block submission
            raise
        except Exception as e:
            frappe.log_error(f"Error validating warehouse capacity for item {item.item_code}: {str(e)}")

    def on_submit(self):
        """Actions to perform on document submission"""
        if self.apply_putaway_rule and self.get("items"):
            self.create_putaway_rule_log()
    
    def create_putaway_rule_log(self):
        """Create a log entry for putaway rule application"""
        try:
            items_with_rules = []
            for item in self.items:
                if hasattr(item, 'putaway_rule') and item.putaway_rule:
                    items_with_rules.append({
                        "item_code": item.item_code,
                        "warehouse": item.warehouse,
                        "putaway_rule": item.putaway_rule,
                        "qty": item.qty
                    })
            
            if items_with_rules:
                # Create a simple log (you can enhance this with custom DocType if needed)
                log_message = f"Putaway rules applied in Goods Receipt Note {self.name}:\n"
                for item_data in items_with_rules:
                    log_message += f"- {item_data['item_code']}: {item_data['qty']} to {item_data['warehouse']} (Rule: {item_data['putaway_rule']})\n"
                
                frappe.log_error(log_message, "Putaway Rule Application Log")
                
        except Exception as e:
            frappe.log_error(f"Error creating putaway rule log: {str(e)}")

@frappe.whitelist()
def apply_putaway_rules_manually(doc_name):
    """
    Manually apply putaway rules to a Goods Receipt Note
    
    Args:
        doc_name: Name of the Goods Receipt Note document
    
    Returns:
        dict: Result of putaway rule application
    """
    try:
        doc = frappe.get_doc("Goods Receipt Note", doc_name)
        
        if not doc.get("items"):
            frappe.throw(_("No items found in the document"))
        
        if doc.docstatus == 1:
            frappe.throw(_("Cannot modify submitted document"))
        
        # Apply putaway rules
        from erpnext.stock.doctype.putaway_rule.putaway_rule import apply_putaway_rule
        
        original_items_count = len(doc.items)
        apply_putaway_rule(doc.doctype, doc.get("items"), doc.company)
        new_items_count = len(doc.items)
        
        # Save the document
        doc.save()
        
        return {
            "success": True,
            "message": _("Putaway rules applied successfully"),
            "original_items": original_items_count,
            "new_items": new_items_count,
            "items_added": new_items_count - original_items_count
        }
        
    except Exception as e:
        frappe.log_error(f"Error in manual putaway rule application: {str(e)}")
        frappe.throw(_("Failed to apply putaway rules: {0}").format(str(e)))

@frappe.whitelist()
def get_goods_receipt_putaway_summary(doc_name):
    """
    Get summary of putaway rule application for a Goods Receipt Note
    
    Args:
        doc_name: Name of the Goods Receipt Note document
    
    Returns:
        dict: Summary of putaway rule application
    """
    try:
        doc = frappe.get_doc("Goods Receipt Note", doc_name)
        
        putaway_summary = {
            "total_items": len(doc.items),
            "items_with_putaway": 0,
            "unique_warehouses": set(),
            "putaway_rules_used": set(),
            "capacity_warnings": []
        }
        
        for item in doc.items:
            # Get warehouse (could be warehouse or accepted_warehouse)
            item_warehouse = getattr(item, 'warehouse', None) or getattr(item, 'accepted_warehouse', None)
            
            if hasattr(item, 'putaway_rule') and item.putaway_rule:
                putaway_summary["items_with_putaway"] += 1
                putaway_summary["putaway_rules_used"].add(item.putaway_rule)
            
            if item_warehouse:
                putaway_summary["unique_warehouses"].add(item_warehouse)
                
                # Check capacity warnings
                warehouse_capacity = frappe.db.get_value("Warehouse", item_warehouse, "capacity")
                if warehouse_capacity:
                    from erpnext.stock.utils import get_stock_balance
                    current_stock = get_stock_balance(item.item_code, item_warehouse)
                    utilization = (current_stock / warehouse_capacity) * 100
                    
                    if utilization > 80:  # Warning threshold
                        putaway_summary["capacity_warnings"].append({
                            "warehouse": item_warehouse,
                            "item": item.item_code,
                            "utilization": utilization,
                            "current_stock": current_stock,
                            "capacity": warehouse_capacity
                        })
        
        # Convert sets to lists for JSON serialization
        putaway_summary["unique_warehouses"] = list(putaway_summary["unique_warehouses"])
        putaway_summary["putaway_rules_used"] = list(putaway_summary["putaway_rules_used"])
        
        return {
            "success": True,
            "putaway_summary": putaway_summary
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting putaway summary: {str(e)}")
        return {"success": False, "error": str(e)}
