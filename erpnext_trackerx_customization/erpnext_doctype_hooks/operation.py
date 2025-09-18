# apps/customize_erpnext_app/customize_erpnext_app/item_group_hooks.py

import frappe
from frappe import _

# Define the list of protected Item Group names that should not be deleted
PROTECTED_OPERATION = ["QR/Barcode Cut Bundle Activation"]

def on_trash(doc, method):


    if doc.name in PROTECTED_OPERATION:
        frappe.throw(_(f"Deletion of Operation '{doc.name}' is not allowed as it is a protected system operation."),
                     frappe.PermissionError)
    else:
        frappe.msgprint(_(f"Operation'{doc.name}' is allowed to be deleted."))


def before_save(doc, method):

    if doc.name in PROTECTED_OPERATION:
        frappe.throw(_(f"Modification to Operation '{doc.name}' is not allowed as it is a protected system operation."),
                     frappe.PermissionError)
    else:
        frappe.msgprint(_(f"Operation'{doc.name}' is allowed to be modify."))

def before_rename(doc, method, a, b, c):

    if doc.name in PROTECTED_OPERATION:
        frappe.throw(_(f"Modification to Operation '{doc.name}' is not allowed as it is a protected system operation."),
                     frappe.PermissionError)
    else:
        frappe.msgprint(_(f"Operation'{doc.name}' is allowed to be modify."))