// Copyright (c) 2025, CognitionX and contributors
// For license information, please see license.txt

frappe.ui.form.on("Digital Device", {
	refresh(frm) {

	},
    device_type(frm){
        frm.set_value("imei","");
        frm.set_value("mac","");
        frm.set_value("ipv4","");
        frm.set_value("id","");
        frm.refresh_field("imei");
        frm.refresh_field("mac");
        frm.refresh_field("ipv4");
        frm.refresh_field("id");
    }
});
