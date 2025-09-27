// Copyright (c) 2025, CognitionX and contributors
// For license information, please see license.txt

frappe.ui.form.on("Production Target Configuration", {
	refresh(frm) {

	},
    onload: function(frm)
    {
        if(frm.is_new())
        {
            frappe.set_route("production_target_2");
        }
    }
});
