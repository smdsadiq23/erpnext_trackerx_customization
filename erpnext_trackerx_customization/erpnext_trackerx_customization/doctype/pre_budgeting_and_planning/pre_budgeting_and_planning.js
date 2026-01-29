// Copyright (c) 2026, CognitionX and contributors
// For license information, please see license.txt

frappe.ui.form.on("Pre-Budgeting and Planning", {
    sales_order(frm) {
        if (!frm.doc.sales_order) return;

        // If new document, save it first
        if (frm.is_new()) {
            frm.save().then(() => {
                fetch_pre_budget_items(frm);
            });
        } else {
            fetch_pre_budget_items(frm);
        }
    }
});

function fetch_pre_budget_items(frm) {
    frappe.call({
        method: "erpnext_trackerx_customization.api.pre_budgeting.fetch_pre_budget_items",
        args: {
            pre_budget_doc: frm.doc.name
        },
        freeze: true,
        callback(r) {
            if (!r.exc) {
                frm.reload_doc();
                frappe.show_alert({
                    message: "Child table auto-filled from Sales Order and BOM",
                    indicator: "green"
                });
            }
        }
    });
}
