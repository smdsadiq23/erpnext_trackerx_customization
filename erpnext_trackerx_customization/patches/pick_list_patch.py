import frappe
from frappe import _
from frappe.utils import flt
import erpnext.stock.doctype.pick_list.pick_list as pick_list_module

def custom_validate_picked_materials(item_code, required_qty, locations, picked_item_details=None):
    for location in list(locations):
        if location["qty"] < 0:
            locations.remove(location)

    total_qty_available = sum(location.get("qty") for location in locations)
    remaining_qty = required_qty - total_qty_available

    if frappe.flags.in_submit and remaining_qty > 0:
        if picked_item_details:
            frappe.msgprint(
                ("{0} units of Item {1} is picked in another Pick List...").format(
                    remaining_qty, pick_list_module.get_link_to_form("Item", item_code)
                ),
                title=_("Already Picked"),
            )

        else:
            frappe.msgprint(
                ("{0} units of Item {1} is not available in any of the warehouses...").format(
                    remaining_qty, pick_list_module.get_link_to_form("Item", item_code)
                ),
                title=_("Insufficient Stock"),
            )