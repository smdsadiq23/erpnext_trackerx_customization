// Copyright (c) 2025, CognitionX and contributors
// For license information, please see license.txt

frappe.ui.form.on("Goods Receipt Note", {
    purchase_order(frm) {
        if (!frm.doc.purchase_order) return;

        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Purchase Order',
                name: frm.doc.purchase_order
            },
            callback(r) {
                if (r.message) {
                    const po = r.message;
                    const items = po.items || [];

                    // Clear existing items
                    frm.clear_table('items');

                    items.forEach(item => {
                        const row = frm.add_child('items');
                        frappe.model.set_value(row.doctype, row.name, 'item_code', item.item_code);
                        frappe.model.set_value(row.doctype, row.name, 'item_name', item.item_name);
                        frappe.model.set_value(row.doctype, row.name, 'ordered_quantity', item.qty);
                        frappe.model.set_value(row.doctype, row.name, 'rate', item.rate);
                        frappe.model.set_value(row.doctype, row.name, 'uom', item.uom);

                        // Set accepted_warehouse from parent if available
                        if (frm.doc.set_warehouse) {
                            frappe.model.set_value(row.doctype, row.name, 'accepted_warehouse', frm.doc.set_warehouse);
                        }
                    });

                    frm.refresh_field('items');
                }
            }
        });
    },

    // When Accepted Warehouse (set_warehouse) is changed
    set_warehouse(frm) {
        if (!frm.doc.set_warehouse) return;

        // Update all existing rows
        (frm.doc.items || []).forEach(row => {
            frappe.model.set_value(row.doctype, row.name, 'accepted_warehouse', frm.doc.set_warehouse);
        });

        // Refresh the table
        frm.refresh_field('items');
    }
});

frappe.ui.form.on("Goods Receipt Item", {
// When received_quantity or rate changes → recalculate amount
    received_quantity(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        const amount = (row.received_quantity || 0) * (row.rate || 0);
        frappe.model.set_value(cdt, cdn, 'amount', amount);
    },
    rate(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        const amount = (row.received_quantity || 0) * (row.rate || 0);
        frappe.model.set_value(cdt, cdn, 'amount', amount);
    },

    // When a new row is added → set accepted_warehouse from parent
    items_add(frm, cdt, cdn) {
        if (frm.doc.set_warehouse) {
            frappe.model.set_value(cdt, cdn, 'accepted_warehouse', frm.doc.set_warehouse);
        }
    }
});
