import frappe
from frappe.model.document import Document
from frappe.utils import nowdate

def validate_allocation(roll_no, allocated_length):
    roll = frappe.get_doc("Fabric Roll", roll_no)
    if roll.is_allocated:
        frappe.throw(f"Roll {roll_no} is already allocated.")
    if roll.inspection_status != "Passed":
        frappe.throw(f"Roll {roll_no} not passed inspection.")
    if allocated_length > roll.length:
        frappe.throw("Allocated length exceeds roll length.")

@frappe.whitelist()
def allocate_roll_to_work_order(work_order, item_code, roll_no, allocated_length):
    validate_allocation(roll_no, allocated_length)
    roll = frappe.get_doc("Fabric Roll", roll_no)
    allocation = frappe.new_doc("Roll Allocation Map")
    allocation.work_order = work_order
    allocation.item_code = item_code
    allocation.roll_no = roll_no
    allocation.shade_code = roll.shade_code
    allocation.allocated_length = allocated_length
    allocation.remaining_length = roll.length - allocated_length
    allocation.allocation_date = nowdate()
    allocation.insert(ignore_permissions=True)
    # Mark as allocated
    roll.is_allocated = 1
    roll.length = allocation.remaining_length
    roll.save(ignore_permissions=True)
    return allocation.name
