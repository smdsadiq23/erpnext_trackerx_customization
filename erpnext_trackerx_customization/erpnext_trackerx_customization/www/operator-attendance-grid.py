
import frappe

def get_context(context):

    """Set context for the Operator Attendance dashboard page"""
    
    # Check if user has permission to view warehouse data
    if not frappe.has_permission("Operator Attendance", "read"):
        frappe.throw("Insufficient permissions to view Operator Attendance data", frappe.PermissionError)
    
    # Set page context
    context.page_title = "Operator Attendance Dashboard"
    context.show_sidebar = False
    
    context.no_cache = 1
    return context