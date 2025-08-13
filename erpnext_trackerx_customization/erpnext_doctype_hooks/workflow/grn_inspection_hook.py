# -*- coding: utf-8 -*-
"""
GRN Inspection Auto-Creation Hook

Automatically creates inspection records when GRN is submitted based on material type.
"""

import frappe
from frappe import _

def create_inspection_from_grn(doc, method=None):
    """
    Auto-create inspection records when GRN is submitted
    
    Args:
        doc: Goods Receipt Note document
        method: Method name (on_submit)
    """
    try:
        frappe.logger().info(f"GRN Inspection Hook triggered for {doc.name}")
        
        # Check if document is submitted
        if doc.docstatus != 1:
            frappe.logger().info(f"Document {doc.name} is not submitted, skipping inspection creation")
            return
        
        inspection_created = False
        
        for item in doc.items:
            frappe.logger().info(f"Processing item {item.item_code}")
            material_type = get_material_type(item.item_code, item)
            frappe.logger().info(f"Material type for {item.item_code}: {material_type}")
            
            if material_type:
                inspection_type = determine_inspection_type(material_type)
                frappe.logger().info(f"Inspection type for {material_type}: {inspection_type}")
                
                if inspection_type:
                    create_inspection_record(doc, item, inspection_type, material_type)
                    inspection_created = True
        
        if not inspection_created:
            frappe.logger().info(f"No inspections created for GRN {doc.name} - no matching material types found")
            
    except Exception as e:
        frappe.log_error(f"Error in GRN inspection hook: {str(e)}", "GRN Inspection Hook Error")
        frappe.logger().error(f"GRN inspection hook error: {str(e)}")

def get_material_type(item_code, grn_item=None):
    """Get material type from GRN item or item master"""
    try:
        # First check if material_type is available from GRN item (preferred)
        if grn_item and hasattr(grn_item, 'material_type') and grn_item.material_type:
            material_type = grn_item.material_type
            frappe.logger().info(f"Found material_type from GRN item: {material_type}")
            return material_type
            
        # Fall back to item master
        item_doc = frappe.get_doc("Item", item_code)
        
        # Check for custom material_type field in item master
        material_type = getattr(item_doc, 'material_type', None)
        if material_type:
            frappe.logger().info(f"Found material_type from item master: {material_type}")
            return material_type
        
        # Fall back to item_group
        item_group = getattr(item_doc, 'item_group', None)
        if item_group:
            frappe.logger().info(f"Using item_group as material_type: {item_group}")
            return item_group
            
        # Check item name for keywords
        item_name = (item_doc.item_name or "").lower()
        item_code_lower = item_code.lower()
        
        for text in [item_name, item_code_lower]:
            if any(keyword in text for keyword in ['fabric', 'cloth', 'textile']):
                return 'Fabric'
            elif any(keyword in text for keyword in ['trim', 'button', 'zipper', 'thread']):
                return 'Trims'  
            elif any(keyword in text for keyword in ['accessory', 'accessories', 'label', 'tag']):
                return 'Accessories'
        
        frappe.logger().info(f"No material type found for item {item_code}")
        return None
        
    except Exception as e:
        frappe.logger().error(f"Error getting material type for {item_code}: {str(e)}")
        return None

def determine_inspection_type(material_type):
    """Determine inspection type based on material type"""
    material_type_lower = material_type.lower() if material_type else ""
    
    if any(keyword in material_type_lower for keyword in ['fabric', 'cloth', 'textile']):
        return "Fabric Inspection"
    elif any(keyword in material_type_lower for keyword in ['trim', 'button', 'zipper', 'thread']):
        return "Trims Inspection"
    elif any(keyword in material_type_lower for keyword in ['accessory', 'accessories', 'label']):
        return "Accessories Inspection"
    
    return None

def create_inspection_record(grn_doc, item, inspection_type, material_type):
    """Create inspection record for the item"""
    try:
        frappe.logger().info(f"Creating {inspection_type} record for item {item.item_code}")
        
        # Get AQL configuration from item
        aql_config = get_item_aql_configuration(item.item_code)
        
        # Map inspection types to DocType names (must match JSON file names exactly)
        doctype_map = {
            "Fabric Inspection": "Fabric Inspection",
            "Trims Inspection": "Trims Inspection", 
            "Accessories Inspection": "Accessories Inspection"
        }
        
        doctype_name = doctype_map.get(inspection_type)
        if not doctype_name:
            frappe.logger().error(f"Unknown inspection type: {inspection_type}")
            return
            
        inspection_data = {
            "doctype": doctype_name,
            "inspection_date": frappe.utils.today(),
            "inspector": frappe.session.user,
            "grn_reference": grn_doc.name,
            "supplier": grn_doc.supplier,
            "inspection_status": "Draft",
            "item_code": item.item_code,
            "item_name": item.item_name or item.item_code,
            "material_type": material_type,
            "total_quantity": float(item.received_quantity or 0),
            "unit_of_measure": item.uom,
            "aql_level": aql_config.get("aql_level") or "2",  # Use valid AQL Level
            "inspection_regime": aql_config.get("inspection_regime", "Normal"),
            "aql_value": aql_config.get("aql_value") or "2.5"  # Use valid AQL Standard
        }
        
        # Add specific fields based on inspection type
        if inspection_type == "Fabric Inspection":
            inspection_data.update({
                "total_rolls": get_total_rolls(item),
            })
        else:
            # For trims and accessories
            inspection_data.update({
                "total_pieces": int(float(item.received_quantity or 0)),
            })
        
        frappe.logger().info(f"Inspection data: {inspection_data}")
        
        # Create inspection document
        inspection_doc = frappe.get_doc(inspection_data)
        inspection_doc.insert(ignore_permissions=True)
        
        frappe.logger().info(f"Created inspection document: {inspection_doc.name}")
        
        # Auto-populate specific details based on inspection type
        try:
            if inspection_type == "Fabric Inspection":
                if hasattr(inspection_doc, 'auto_populate_rolls'):
                    inspection_doc.auto_populate_rolls()
                    inspection_doc.save()
            else:
                # Auto-populate checklist for trims and accessories
                if hasattr(inspection_doc, 'auto_populate_checklist'):
                    inspection_doc.auto_populate_checklist()
                    inspection_doc.save()
        except Exception as populate_error:
            frappe.logger().error(f"Error auto-populating inspection details: {str(populate_error)}")
            # Continue even if auto-populate fails
        
        frappe.msgprint(
            _("Inspection {0} created for item {1}").format(
                inspection_doc.name, item.item_code
            )
        )
        
        frappe.logger().info(f"Successfully created inspection {inspection_doc.name}")
        
    except Exception as e:
        error_msg = f"Error creating inspection from GRN: {str(e)}"
        frappe.log_error(error_msg, "GRN Inspection Creation Error")
        frappe.logger().error(error_msg)
        frappe.msgprint(_("Could not create inspection for item {0}: {1}").format(
            item.item_code, str(e)
        ))

def get_item_aql_configuration(item_code):
    """Get AQL configuration from item master"""
    try:
        item_doc = frappe.get_doc("Item", item_code)
        
        return {
            "aql_level": getattr(item_doc, 'aql_level', "2"),
            "inspection_regime": getattr(item_doc, 'inspection_regime', "Normal"),
            "aql_value": getattr(item_doc, 'aql_value', "2.5")
        }
    except:
        # Default AQL configuration
        return {
            "aql_level": "2",
            "inspection_regime": "Normal", 
            "aql_value": "2.5"
        }

def get_total_rolls(item):
    """Calculate total rolls for fabric items"""
    # For GRN items, use received_quantity
    # This would depend on how roll information is stored
    # For now, estimating based on quantity (assuming ~100m per roll)
    qty = item.received_quantity or 0
    if qty > 100:
        return int(qty / 100) or 1
    else:
        return 1

# Hook registration function
def register_grn_hooks():
    """Register GRN hooks"""
    frappe.db.set_value("DocType", "Purchase Receipt", "has_web_view", 0)
    return True