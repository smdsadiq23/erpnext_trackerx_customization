// Copyright (c) 2025, CognitionX and contributors
// For license information, please see license.txt

frappe.ui.form.on("Style Master", {
    image: function(frm) {
        // Trigger sync as soon as image is uploaded
        if (frm.doc.image && !frm.is_new()) {
            frappe.call({
                method: "erpnext_trackerx_customization.erpnext_trackerx_customization.doctype.style_master.style_master.sync_on_image_upload",
                args: {
                    style_master_name: frm.doc.name,
                    image_url: frm.doc.image
                }
            });
        }
    }    
});
