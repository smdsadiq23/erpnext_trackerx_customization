import frappe
from frappe import _

# Define the list of protected Item Group names that should not be deleted
PROTECTED_SUPPLIER_GROUPS = ["Sub Contractors"]


def before_delete(doc, method):
    prevent_item_group_deletion(doc, method)

def prevent_item_group_deletion(doc, method):
   
    frappe.log_error("Supplier Group Deletion Check", f"Attempting to delete Item Group: {doc.name}")

    if doc.name in PROTECTED_SUPPLIER_GROUPS:
        frappe.throw(_(f"Deletion of Supplier Group '{doc.name}' is not allowed as it is a protected system group."),
                     frappe.PermissionError)
    else:
        frappe.msgprint(_(f"Supplier Group '{doc.name}' is allowed to be deleted."))

