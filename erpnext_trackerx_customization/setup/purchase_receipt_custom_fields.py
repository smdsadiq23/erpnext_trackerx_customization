import frappe

def execute():
    custom_fields = [
        {
            "dt": "Purchase Receipt",
            "fieldname": "linked_grn",
            "label": "Linked GRN",
            "fieldtype": "Link",
            "options": "Goods Receipt Note",
            "insert_after": "supplier",
        },
        {
            "dt": "Purchase Receipt",
            "fieldname": "linked_mir",
            "label": "Linked MIR",
            "fieldtype": "Link",
            "options": "Material Inspection Report",
            "insert_after": "linked_grn",
        },
        {
            "dt": "Purchase Receipt",
            "fieldname": "rejected_items_section",
            "label": "Rejected Items",
            "fieldtype": "Section Break",
            "insert_after": "items",
        },
        {
            "dt": "Purchase Receipt",
            "fieldname": "rejected_items",
            "label": "Rejected Items",
            "fieldtype": "Table",
            "options": "Purchase Receipt Rejected Item",
            "insert_after": "rejected_items_section",
        }
    ]
    
    for field in custom_fields:
        if not frappe.db.exists("Custom Field", f"{field['dt']}-{field['fieldname']}"):
            frappe.get_doc({
                "doctype": "Custom Field",
                "dt": field["dt"],
                "fieldname": field["fieldname"],
                "label": field["label"],
                "fieldtype": field["fieldtype"],
                "options": field.get("options", ""),
                "insert_after": field["insert_after"],
            }).insert(ignore_permissions=True)
    
    frappe.db.commit()
    frappe.msgprint("Custom fields added to Purchase Receipt.")
