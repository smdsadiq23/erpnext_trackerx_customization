# Copyright (c) 2025, CognitionX and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, cint
import json

class WarehouseCapacityManager(Document):
    """
    Manager class for handling warehouse capacity and putaway rule integration
    """
    pass

@frappe.whitelist()
def auto_create_putaway_rules_from_warehouse(warehouse_name, items_data=None):
    """
    Auto-create putaway rules based on warehouse capacity
    
    Args:
        warehouse_name: Warehouse name
        items_data: JSON string of items to create rules for, if None creates for all active items
    
    Returns:
        dict: Success status and created rules count
    """
    try:
        # Get warehouse details
        warehouse = frappe.get_doc("Warehouse", warehouse_name)
        
        # Check if warehouse has capacity defined
        if not hasattr(warehouse, 'capacity') or not warehouse.capacity:
            frappe.throw(_("Warehouse {0} does not have capacity defined").format(warehouse_name))
        
        # Get items to create rules for
        if items_data:
            items = json.loads(items_data) if isinstance(items_data, str) else items_data
        else:
            # Get all active items
            items = frappe.get_all("Item", 
                                 filters={"disabled": 0, "is_stock_item": 1}, 
                                 fields=["name", "item_name", "stock_uom"])
        
        created_rules = 0
        updated_rules = 0
        
        for item in items:
            item_code = item.get("name") or item.get("item_code")
            
            # Check if putaway rule already exists
            existing_rule = frappe.db.exists("Putaway Rule", {
                "item_code": item_code,
                "warehouse": warehouse_name
            })
            
            if existing_rule:
                # Update existing rule with warehouse capacity
                rule_doc = frappe.get_doc("Putaway Rule", existing_rule)
                rule_doc.capacity = warehouse.capacity
                rule_doc.uom = getattr(warehouse, 'capacity_unit', 'Meter')
                rule_doc.save(ignore_permissions=True)
                updated_rules += 1
            else:
                # Create new putaway rule
                rule_doc = frappe.get_doc({
                    "doctype": "Putaway Rule",
                    "item_code": item_code,
                    "warehouse": warehouse_name,
                    "company": warehouse.company,
                    "capacity": warehouse.capacity,
                    "uom": getattr(warehouse, 'capacity_unit', 'Meter'),
                    "priority": get_item_priority(item_code, warehouse.company),
                    "disable": 0
                })
                rule_doc.insert(ignore_permissions=True)
                created_rules += 1
        
        frappe.db.commit()
        
        return {
            "success": True,
            "message": _("Created {0} new rules and updated {1} existing rules for warehouse {2}").format(
                created_rules, updated_rules, warehouse_name
            ),
            "created_rules": created_rules,
            "updated_rules": updated_rules
        }
        
    except Exception as e:
        frappe.log_error(f"Error in auto_create_putaway_rules_from_warehouse: {str(e)}")
        frappe.throw(_("Failed to create putaway rules: {0}").format(str(e)))

def get_item_priority(item_code, company):
    """
    Determine item priority for putaway rules based on item characteristics
    
    Args:
        item_code: Item code
        company: Company name
    
    Returns:
        int: Priority value (1 = highest priority)
    """
    try:
        item = frappe.get_doc("Item", item_code)
        
        # Priority logic based on item characteristics
        if hasattr(item, 'item_group'):
            priority_mapping = {
                "Raw Material": 1,      # Highest priority
                "Work In Progress": 2,
                "Finished Goods": 3,
                "Consumable": 4,
                "Trading Goods": 5      # Lowest priority
            }
            
            item_group = frappe.get_value("Item Group", item.item_group, "name")
            
            # Check if item group matches any priority category
            for category, priority in priority_mapping.items():
                if category.lower() in item_group.lower():
                    return priority
        
        # Default priority
        return 3
        
    except Exception as e:
        frappe.log_error(f"Error getting item priority for {item_code}: {str(e)}")
        return 3  # Default priority

@frappe.whitelist()
def sync_warehouse_capacity_with_putaway_rules(company=None):
    """
    Sync all warehouse capacities with existing putaway rules
    
    Args:
        company: Company to sync for, if None syncs for all companies
    
    Returns:
        dict: Sync results
    """
    try:
        filters = {}
        if company:
            filters["company"] = company
        
        # Get all warehouses with capacity
        warehouses = frappe.get_all("Warehouse", 
                                   filters=filters,
                                   fields=["name", "company", "capacity", "capacity_unit"])
        
        synced_warehouses = 0
        total_rules_updated = 0
        
        for warehouse in warehouses:
            if not hasattr(warehouse, 'capacity') or not warehouse.capacity:
                continue
            
            # Get all putaway rules for this warehouse
            putaway_rules = frappe.get_all("Putaway Rule",
                                         filters={"warehouse": warehouse.name},
                                         fields=["name", "capacity", "uom"])
            
            rules_updated_for_warehouse = 0
            for rule in putaway_rules:
                rule_doc = frappe.get_doc("Putaway Rule", rule.name)
                
                # Update capacity if different
                if flt(rule_doc.capacity) != flt(warehouse.capacity):
                    rule_doc.capacity = warehouse.capacity
                    rule_doc.uom = warehouse.get("capacity_unit", "Meter")
                    rule_doc.save(ignore_permissions=True)
                    rules_updated_for_warehouse += 1
            
            if rules_updated_for_warehouse > 0:
                synced_warehouses += 1
                total_rules_updated += rules_updated_for_warehouse
        
        frappe.db.commit()
        
        return {
            "success": True,
            "message": _("Synchronized {0} warehouses and updated {1} putaway rules").format(
                synced_warehouses, total_rules_updated
            ),
            "synced_warehouses": synced_warehouses,
            "total_rules_updated": total_rules_updated
        }
        
    except Exception as e:
        frappe.log_error(f"Error in sync_warehouse_capacity_with_putaway_rules: {str(e)}")
        frappe.throw(_("Failed to sync warehouse capacity: {0}").format(str(e)))

@frappe.whitelist()
def get_warehouse_capacity_summary(warehouse=None, company=None):
    """
    Get comprehensive warehouse capacity summary
    
    Args:
        warehouse: Specific warehouse name (optional)
        company: Company filter (optional)
    
    Returns:
        dict: Warehouse capacity summary
    """
    try:
        filters = {"is_group": 0}  # Only actual storage warehouses
        if warehouse:
            filters["name"] = warehouse
        if company:
            filters["company"] = company
        
        warehouses = frappe.get_all("Warehouse", 
                                   filters=filters,
                                   fields=["name", "company", "capacity", "capacity_unit"])
        
        capacity_summary = []
        
        for wh in warehouses:
            # Get putaway rules count
            putaway_rules_count = frappe.db.count("Putaway Rule", {"warehouse": wh.name})
            
            # Get current stock levels (aggregate across all items)
            stock_data = frappe.db.sql("""
                SELECT 
                    COALESCE(SUM(actual_qty), 0) as total_qty,
                    COUNT(DISTINCT item_code) as unique_items
                FROM `tabBin` 
                WHERE warehouse = %s AND actual_qty > 0
            """, (wh.name,), as_dict=True)
            
            total_stock = stock_data[0].get("total_qty", 0) if stock_data else 0
            unique_items = stock_data[0].get("unique_items", 0) if stock_data else 0
            
            # Calculate utilization
            capacity = wh.get("capacity", 0)
            utilization_percent = (flt(total_stock) / flt(capacity) * 100) if capacity else 0
            
            capacity_summary.append({
                "warehouse": wh.name,
                "company": wh.company,
                "capacity": capacity,
                "capacity_unit": wh.get("capacity_unit", "Meter"),
                "current_stock": total_stock,
                "unique_items": unique_items,
                "utilization_percent": utilization_percent,
                "putaway_rules_count": putaway_rules_count,
                "available_space": capacity - total_stock if capacity else 0
            })
        
        return {
            "success": True,
            "capacity_summary": capacity_summary,
            "total_warehouses": len(capacity_summary)
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_warehouse_capacity_summary: {str(e)}")
        return {"success": False, "error": str(e)}