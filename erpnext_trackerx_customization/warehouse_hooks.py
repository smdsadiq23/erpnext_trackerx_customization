# Copyright (c) 2025, CognitionX and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, today, add_days

def on_warehouse_create(doc, method):
    """
    Hook triggered when a new warehouse is created
    Auto-create putaway rules if warehouse has capacity
    """
    try:
        if hasattr(doc, 'capacity') and doc.capacity and not doc.is_group:
            # Get active stock items for the company
            items = frappe.get_all("Item", 
                                 filters={
                                     "disabled": 0, 
                                     "is_stock_item": 1
                                 }, 
                                 fields=["name"],
                                 limit=10)  # Limit to prevent too many rules
            
            if items:
                from erpnext_trackerx_customization.erpnext_trackerx_customization.doctype.warehouse_capacity_manager.warehouse_capacity_manager import auto_create_putaway_rules_from_warehouse
                
                # Create putaway rules for selected items
                result = auto_create_putaway_rules_from_warehouse(doc.name, items)
                
                if result.get("success"):
                    frappe.msgprint(_("Auto-created {0} putaway rules for warehouse {1}").format(
                        result.get("created_rules", 0), doc.name
                    ), alert=True)
                    
    except Exception as e:
        frappe.log_error(f"Error in on_warehouse_create hook: {str(e)}")

def on_warehouse_update(doc, method):
    """
    Hook triggered when warehouse is updated
    Sync capacity changes with existing putaway rules
    """
    try:
        # Check if capacity was changed
        if doc.has_value_changed('capacity') and hasattr(doc, 'capacity') and doc.capacity:
            # Update all putaway rules for this warehouse
            putaway_rules = frappe.get_all("Putaway Rule", 
                                         filters={"warehouse": doc.name},
                                         fields=["name"])
            
            updated_rules = 0
            for rule in putaway_rules:
                rule_doc = frappe.get_doc("Putaway Rule", rule.name)
                rule_doc.capacity = doc.capacity
                rule_doc.uom = getattr(doc, 'capacity_unit', 'Meter')
                rule_doc.save(ignore_permissions=True)
                updated_rules += 1
            
            if updated_rules > 0:
                frappe.msgprint(_("Updated capacity in {0} putaway rules for warehouse {1}").format(
                    updated_rules, doc.name
                ), alert=True)
                
    except Exception as e:
        frappe.log_error(f"Error in on_warehouse_update hook: {str(e)}")

def daily_capacity_sync():
    """
    Daily scheduled job to sync warehouse capacity with putaway rules
    """
    try:
        from erpnext_trackerx_customization.erpnext_trackerx_customization.doctype.warehouse_capacity_manager.warehouse_capacity_manager import sync_warehouse_capacity_with_putaway_rules
        
        result = sync_warehouse_capacity_with_putaway_rules()
        
        if result.get("success") and result.get("total_rules_updated", 0) > 0:
            # Send email notification to administrators
            send_capacity_sync_notification(result)
            
    except Exception as e:
        frappe.log_error(f"Error in daily_capacity_sync: {str(e)}")

def weekly_capacity_report():
    """
    Weekly scheduled job to generate capacity utilization report
    """
    try:
        from erpnext_trackerx_customization.erpnext_trackerx_customization.doctype.warehouse_capacity_manager.warehouse_capacity_manager import get_warehouse_capacity_summary
        
        result = get_warehouse_capacity_summary()
        
        if result.get("success"):
            generate_weekly_capacity_report(result.get("capacity_summary", []))
            
    except Exception as e:
        frappe.log_error(f"Error in weekly_capacity_report: {str(e)}")

def send_capacity_sync_notification(sync_result):
    """Send email notification about capacity sync results"""
    try:
        # Get system managers
        recipients = frappe.get_all("Has Role", 
                                  filters={"role": "System Manager"}, 
                                  fields=["parent"])
        
        if not recipients:
            return
        
        recipient_emails = [r.parent for r in recipients]
        
        subject = "Daily Warehouse Capacity Sync Report"
        message = f"""
        <h3>Warehouse Capacity Sync Completed</h3>
        <p><strong>Date:</strong> {today()}</p>
        <p><strong>Synchronized Warehouses:</strong> {sync_result.get('synced_warehouses', 0)}</p>
        <p><strong>Updated Putaway Rules:</strong> {sync_result.get('total_rules_updated', 0)}</p>
        <p><strong>Status:</strong> Success</p>
        """
        
        frappe.sendmail(
            recipients=recipient_emails,
            subject=subject,
            message=message
        )
        
    except Exception as e:
        frappe.log_error(f"Error sending capacity sync notification: {str(e)}")

def generate_weekly_capacity_report(capacity_data):
    """Generate and send weekly capacity utilization report"""
    try:
        if not capacity_data:
            return
        
        # Calculate summary statistics
        total_warehouses = len(capacity_data)
        high_utilization_warehouses = [w for w in capacity_data if w.get('utilization_percent', 0) > 80]
        low_utilization_warehouses = [w for w in capacity_data if w.get('utilization_percent', 0) < 20]
        
        # Get recipients
        recipients = frappe.get_all("Has Role", 
                                  filters={"role": "Stock Manager"}, 
                                  fields=["parent"])
        
        if not recipients:
            return
        
        recipient_emails = [r.parent for r in recipients]
        
        subject = "Weekly Warehouse Capacity Utilization Report"
        
        # Build HTML message
        message = f"""
        <h2>Weekly Warehouse Capacity Report</h2>
        <p><strong>Report Date:</strong> {today()}</p>
        
        <h3>Summary</h3>
        <ul>
            <li>Total Warehouses: {total_warehouses}</li>
            <li>High Utilization (&gt;80%): {len(high_utilization_warehouses)}</li>
            <li>Low Utilization (&lt;20%): {len(low_utilization_warehouses)}</li>
        </ul>
        """
        
        # High utilization warnings
        if high_utilization_warehouses:
            message += """
            <h3 style="color: #d9534f;">⚠️ High Utilization Warehouses</h3>
            <table border="1" style="border-collapse: collapse; width: 100%;">
                <tr style="background-color: #f5f5f5;">
                    <th>Warehouse</th>
                    <th>Utilization %</th>
                    <th>Current Stock</th>
                    <th>Capacity</th>
                    <th>Available Space</th>
                </tr>
            """
            for wh in high_utilization_warehouses:
                message += f"""
                <tr>
                    <td>{wh.get('warehouse', '')}</td>
                    <td>{wh.get('utilization_percent', 0):.1f}%</td>
                    <td>{wh.get('current_stock', 0)}</td>
                    <td>{wh.get('capacity', 0)}</td>
                    <td>{wh.get('available_space', 0)}</td>
                </tr>
                """
            message += "</table>"
        
        message += "<p><em>This is an automated report generated by the Warehouse Capacity Management System.</em></p>"
        
        frappe.sendmail(
            recipients=recipient_emails,
            subject=subject,
            message=message
        )
        
        # Also create a log
        frappe.log_error(f"Weekly capacity report sent to {len(recipient_emails)} recipients", 
                        "Weekly Capacity Report")
        
    except Exception as e:
        frappe.log_error(f"Error generating weekly capacity report: {str(e)}")