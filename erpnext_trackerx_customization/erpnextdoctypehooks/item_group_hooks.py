# apps/customize_erpnext_app/customize_erpnext_app/item_group_hooks.py

import frappe
from frappe import _

# Define the list of protected Item Group names that should not be deleted
PROTECTED_ITEM_GROUPS = ["All Item Groups","Trims","Raw Materials","Fabrics","Knitted Fabrics","Single Jersey","Rib Knit","Interlock","Pique Knit","Fleece","Jacquard Knit","Mesh Knit","French Terry","Finished Goods"]

def prevent_item_group_deletion(doc, method):
    """
    This function is hooked to the 'before_delete' event of the Item Group DocType.
    It checks if the Item Group being deleted is one of the protected groups.
    If it is, it raises a PermissionError to prevent the deletion.
    """
    frappe.log_error("Item Group Deletion Check", f"Attempting to delete Item Group: {doc.name}")

    if doc.name in PROTECTED_ITEM_GROUPS:
        frappe.throw(_(f"Deletion of Item Group '{doc.name}' is not allowed as it is a protected system group."),
                     frappe.PermissionError)
    else:
        frappe.msgprint(_(f"Item Group '{doc.name}' is allowed to be deleted."))
