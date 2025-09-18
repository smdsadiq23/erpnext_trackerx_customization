# apps/customize_erpnext_app/customize_erpnext_app/item_group_hooks.py

import frappe
from frappe import _

PROTECTED_WS= ["QR/Barcode Cut Bundle Activation"]

def on_trash(doc, method):


    if doc.name in PROTECTED_WS:
        frappe.throw(_(f"Deletion of Workstation '{doc.name}' is not allowed as it is a protected system operation."),
                     frappe.PermissionError)
    else:
        frappe.msgprint(_(f"Workstation'{doc.name}' is allowed to be deleted."))


def before_save(doc, method):

    if doc.name in PROTECTED_WS:
        frappe.throw(_(f"Modification to Workstation '{doc.name}' is not allowed as it is a protected system operation."),
                     frappe.PermissionError)
    else:
        frappe.msgprint(_(f"Workstation'{doc.name}' is allowed to be modify."))


def before_rename(doc, method, a, b, c):

    if doc.name in PROTECTED_WS:
        frappe.throw(_(f"Modification to Workstation '{doc.name}' is not allowed as it is a protected system operation."),
                     frappe.PermissionError)
    else:
        frappe.msgprint(_(f"Workstation'{doc.name}' is allowed to be modify."))