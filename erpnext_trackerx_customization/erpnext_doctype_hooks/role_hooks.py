

import frappe
from frappe import _

# Define the list of protected Role names that should not be deleted
PROTECTED_ROLES = ["Finished Goods Master","Fabrics Master","Trims Master", "Accessories Master", "Machine Master", "Packing Materials Master", "Labels Master", "Spare Parts Master", "Vendor AQL Audit Supervisor"]

def prevent_role_deletion(doc, method):
    """
    This function is hooked to the 'before_delete' event of the Role DocType.
    It checks if the Role being deleted is one of the protected groups.
    If it is, it raises a PermissionError to prevent the deletion.
    """
    frappe.log_error("Role Deletion Check", f"Attempting to delete Role: {doc.name}")

    if doc.name in PROTECTED_ROLES:
        frappe.throw(_(f"Deletion of Role '{doc.name}' is not allowed as it is a protected system group."),
                     frappe.PermissionError)
    else:
        frappe.msgprint(_(f"Role '{doc.name}' is allowed to be deleted."))

