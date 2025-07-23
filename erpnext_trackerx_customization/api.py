import frappe
import json
from frappe import _
import os

import frappe
from erpnext_trackerx_customization.utils.constants import get_constants

@frappe.whitelist()
def get_item_constants():
    return get_constants()