import frappe
from frappe import _

def get_context(context):
    """
    Context function for the Quality Dashboard page
    This creates the page accessible at /app/quality_dashboard
    """
    
    context.no_cache = 1
    context.show_sidebar = True
    context.page_title = "Quality Dashboard"
    
    # Get current user roles
    user_roles = frappe.get_roles(frappe.session.user)
    
    # Check if user has quality roles
    context.is_quality_inspector = "Quality Inspector" in user_roles
    context.is_quality_manager = "Quality Manager" in user_roles
    context.is_system_user = "Administrator" in user_roles or "System Manager" in user_roles
    
    # If user doesn't have quality roles, show access denied
    if not (context.is_quality_inspector or context.is_quality_manager or context.is_system_user):
        frappe.throw(_("You don't have permission to access the Quality Dashboard"))
    
    # Get dashboard data
    context.pending_fabric_inspections = get_pending_fabric_inspections()
    context.pending_trims_inspections = get_pending_trims_inspections()
    
    if context.is_quality_manager or context.is_system_user:
        context.completed_fabric_inspections = get_completed_fabric_inspections()
        context.completed_trims_inspections = get_completed_trims_inspections()
    
    return context

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