import frappe
from frappe import _

@frappe.whitelist()
def get_context(context):
    """Get context for quality dashboard page"""
    context.no_cache = 1
    context.show_sidebar = True
    
    # Get current user roles
    user_roles = frappe.get_roles(frappe.session.user)
    
    context.is_quality_inspector = "Quality Inspector" in user_roles
    context.is_quality_manager = "Quality Manager" in user_roles
    context.is_system_user = "Administrator" in user_roles or "System Manager" in user_roles
    
    return context

@frappe.whitelist()
def get_pending_fabric_inspections():
    """Get fabric inspections pending for Quality Inspector"""
    try:
        inspections = frappe.get_all(
            "Fabric Inspection",
            filters={
                "inspection_status": ["in", ["Draft", "In Progress", "Hold", "In Review"]],
                "docstatus": ["<", 2]
            },
            fields=["name", "inspection_date", "supplier", "item_code", "total_quantity", "inspection_status"],
            order_by="creation desc",
            limit=20
        )
        return inspections
    except Exception as e:
        frappe.log_error(f"Error fetching fabric inspections: {str(e)}")
        return []

@frappe.whitelist()
def get_pending_trims_inspections():
    """Get trims inspections pending for Quality Inspector"""
    try:
        inspections = frappe.get_all(
            "Trims Inspection",
            filters={
                "inspection_status": ["in", ["Draft", "In Progress", "Hold", "In Review"]],
                "docstatus": ["<", 2]
            },
            fields=["name", "inspection_date", "supplier", "item_code", "total_quantity", "inspection_status"],
            order_by="creation desc",
            limit=20
        )
        return inspections
    except Exception as e:
        frappe.log_error(f"Error fetching trims inspections: {str(e)}")
        return []

@frappe.whitelist()
def get_completed_fabric_inspections():
    """Get completed fabric inspections for Quality Manager"""
    try:
        inspections = frappe.get_all(
            "Fabric Inspection",
            filters={
                "inspection_status": ["in", ["Accepted", "Rejected", "Conditional Accept"]],
                "docstatus": ["<", 2]
            },
            fields=["name", "inspection_date", "supplier", "item_code", "total_quantity", "inspection_status"],
            order_by="creation desc",
            limit=20
        )
        return inspections
    except Exception as e:
        frappe.log_error(f"Error fetching completed fabric inspections: {str(e)}")
        return []

@frappe.whitelist()
def get_completed_trims_inspections():
    """Get completed trims inspections for Quality Manager"""
    try:
        inspections = frappe.get_all(
            "Trims Inspection",
            filters={
                "inspection_status": ["in", ["Accepted", "Rejected", "Conditional Accept"]],
                "docstatus": ["<", 2]
            },
            fields=["name", "inspection_date", "supplier", "item_code", "total_quantity", "inspection_status"],
            order_by="creation desc",
            limit=20
        )
        return inspections
    except Exception as e:
        frappe.log_error(f"Error fetching completed trims inspections: {str(e)}")
        return []