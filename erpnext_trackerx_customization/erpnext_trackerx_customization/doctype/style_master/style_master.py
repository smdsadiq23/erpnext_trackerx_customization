# Copyright (c) 2025, CognitionX and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document


class StyleMaster(Document):
	pass


@frappe.whitelist()
def sync_on_image_upload(style_master_name, image_url):
    # Get Items linked to this Style Master
    items = frappe.get_all(
        "Item",
        filters={"custom_style_master": style_master_name},
        pluck="name"
    )
    if not items:
        return

    # Update Items
    for item in items:
        frappe.db.set_value("Item", item, "image", image_url, update_modified=False)

    # Get BOMs linked to those Items (standard linkage)
    boms = frappe.get_all(
        "BOM",
        filters={"item": ["in", items], "docstatus": ["!=", 2]},
        pluck="name"
    )

    # Update BOMs
    for bom in boms:
        frappe.db.set_value("BOM", bom, "image", image_url, update_modified=False)

    frappe.db.commit()
    return {"items_updated": len(items), "boms_updated": len(boms)}