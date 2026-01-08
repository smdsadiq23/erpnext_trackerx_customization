# erpnext_trackerx_customization/utils/bom_image_sync.py

import frappe

def sync_item_image_to_boms(doc, method):
    """
    When Item image is added/updated,
    sync it to all related BOMs (except cancelled).
    Called from Item's after_save hook.
    """

    # Fetch all BOMs linked to this Item
    bom_list = frappe.get_all(
        "BOM",
        filters={
            "item": doc.name,
            "docstatus": ["!=", 2]  # exclude cancelled BOMs (docstatus = 2)
        },
        fields=["name", "image"]
    )
    
    if not bom_list:
        return
    
    # Update each BOM with the new image
    for bom in bom_list:
        # Always update, even if BOM already has image (to keep in sync)
        frappe.db.set_value(
            "BOM",
            bom["name"],
            "image",
            doc.image,
            update_modified=False  # Don't update modified timestamp
        )
    
    frappe.db.commit()
    
    # Log for debugging
    frappe.logger().info(f"Synced image from Item '{doc.name}' to {len(bom_list)} BOM(s)")