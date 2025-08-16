import frappe
import json
import frappe
from frappe import _

def get_constants():
    constants_path = frappe.get_app_path('erpnext_trackerx_customization', 'config', 'constants.json')
    with open(constants_path) as f:
        return json.load(f)
    



def boot_session(bootinfo):
    bootinfo.item_constants = get_constants()

    
