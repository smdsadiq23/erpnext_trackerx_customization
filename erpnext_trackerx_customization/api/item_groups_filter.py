import frappe

@frappe.whitelist()
def get_items_under_group_and_children(item_group):
    if not item_group:
        return []

    groups = frappe.get_all("Item Group", {
        "lft": (">=", frappe.db.get_value("Item Group", item_group, "lft")),
        "rgt": ("<=", frappe.db.get_value("Item Group", item_group, "rgt"))
    }, pluck="name")

    return groups
