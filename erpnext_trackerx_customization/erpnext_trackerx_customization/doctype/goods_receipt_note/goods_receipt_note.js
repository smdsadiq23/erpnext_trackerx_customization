// Copyright (c) 2025, CognitionX and contributors
// For license information, please see license.txt

frappe.ui.form.on("Goods Receipt Note", {
    refresh(frm) {
        // Only run for new documents
        if (frm.doc.__islocal && (frm.doc.document_checklist?.length || 0) === 0) {
            const standard_docs = [
                'Delivery Challan / Invoice',
                'Packing List',
                'Material Test Certificate (MTC)',
                'Inspection Report',
                'Gate Entry Register / Inward Register'
            ];

            const optional_docs = [
                'Purchase Order',
                'GRN Document (System-Generated)',
                'Advance Shipping Notice (ASN)',
                'Waybill / Transport Document',
                'Certificate of Conformance (CoC)'
            ];

            // Add standard (required) documents
            standard_docs.forEach(doc => {
                const row = frm.add_child('document_checklist');
                frappe.model.set_value(row.doctype, row.name, 'document_type', doc);
                frappe.model.set_value(row.doctype, row.name, 'is_required', 1);
            });

            // Add optional documents (not mandatory)
            optional_docs.forEach(doc => {
                const row = frm.add_child('document_checklist');
                frappe.model.set_value(row.doctype, row.name, 'document_type', doc);
                frappe.model.set_value(row.doctype, row.name, 'is_required', 0);
            });

            frm.refresh_field('document_checklist');
        }
        set_item_code_query(frm);
    },

    validate(frm) {
        const missing_required = [];
        const missing_date = [];

        (frm.doc.document_checklist || []).forEach(function(row) {
            if (row.is_required && !row.received) {
                missing_required.push(row.document_type);
            }
            if (row.received && !row.received_date) {
                missing_date.push(row.document_type);
            }
        });

        if (missing_required.length > 0) {
            frappe.throw(__("The following required documents are not marked as received:<br>{0}", [missing_required.map(d => `<li>${d}</li>`).join('')]));
        }

        if (missing_date.length > 0) {
            frappe.throw(__("Received Date is mandatory for:<br>{0}", [missing_date.map(d => `<li>${d}</li>`).join('')]));
        }
    },

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
                    const po_items = po.items || [];

                    frm.clear_table('items');

                    // Build a promise for each item fetch from Item master
                    let promises = po_items.map(po_item => {
                        return frappe.db.get_doc('Item', po_item.item_code)
                            .then(item_doc => {
                                const row = frm.add_child('items');
                                frappe.model.set_value(row.doctype, row.name, 'item_code', po_item.item_code);
                                frappe.model.set_value(row.doctype, row.name, 'item_name', po_item.item_name);
                                frappe.model.set_value(row.doctype, row.name, 'ordered_quantity', po_item.qty);
                                frappe.model.set_value(row.doctype, row.name, 'amount', po_item.rate);
                                frappe.model.set_value(row.doctype, row.name, 'uom', po_item.uom);

                                // Fetch from Item doctype (custom field)
                                frappe.model.set_value(row.doctype, row.name, 'color', item_doc.custom_colour_name);
                                frappe.model.set_value(row.doctype, row.name, 'composition', item_doc.custom_material_composition);
                                frappe.model.set_value(row.doctype, row.name, 'material_type', item_doc.custom_select_master);

                                // You can fetch other fields similarly, e.g.:
                                // frappe.model.set_value(row.doctype, row.name, 'your_field', item_doc.your_field);

                                if (frm.doc.set_warehouse) {
                                    frappe.model.set_value(row.doctype, row.name, 'accepted_warehouse', frm.doc.set_warehouse);
                                }
                            });
                    });

                    // After all items are added
                    Promise.all(promises).then(() => {
                        frm.refresh_field('items');
                        set_item_code_query(frm);
                    });
                }
            }
        });
    },

    set_warehouse(frm) {
        if (!frm.doc.set_warehouse) return;

        (frm.doc.items || []).forEach(row => {
            frappe.model.set_value(row.doctype, row.name, 'accepted_warehouse', frm.doc.set_warehouse);
        });

        frm.refresh_field('items');
    },

    before_save(frm) {
        (frm.doc.document_checklist || []).forEach(row => {
            if (row.photo_upload && row.document_type === 'Photo Evidence') {
                frappe.model.set_value(row.doctype, row.name, 'attached_to_doctype', 'Goods Receipt Note');
                frappe.model.set_value(row.doctype, row.name, 'attached_to_name', frm.doc.name);
            }
        });
    },

    items_add(frm, cdt, cdn) {
        if (frm.doc.set_warehouse) {
            frappe.model.set_value(cdt, cdn, 'accepted_warehouse', frm.doc.set_warehouse);
        }
        set_item_code_query(frm);
    }
});

// Only allow PO items as item_code
function set_item_code_query(frm) {
    let po = frm.doc.purchase_order;
    if (!po) {
        frm.fields_dict['items'].grid.get_field('item_code').get_query = function() { return {}; };
        return;
    }
    frappe.call({
        method: "frappe.client.get",
        args: {
            doctype: "Purchase Order",
            name: po
        },
        callback: function(r) {
            if (r.message) {
                let valid_items = (r.message.items || []).map(item => item.item_code);
                frm.fields_dict['items'].grid.get_field('item_code').get_query = function(doc, cdt, cdn) {
                    return {
                        filters: [
                            ['Item', 'item_code', 'in', valid_items]
                        ]
                    };
                };
                frm.refresh_field('items');
            }
        }
    });
}

// --- Goods Receipt Item Child Table Events ---
frappe.ui.form.on("Goods Receipt Item", {
    received_quantity(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        const amount = (row.received_quantity || 0) * (row.rate || 0);
        frappe.model.set_value(cdt, cdn, 'amount', amount);
    },
    rate(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        const amount = (row.received_quantity || 0) * (row.rate || 0);
        frappe.model.set_value(cdt, cdn, 'amount', amount);
    }
    // items_add is handled in parent
});

// --- Checklist Table Events ---
frappe.ui.form.on('Goods Receipt Document Checklist', {
    received(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.received) {
            const default_date = frm.doc.transaction_date || frappe.datetime.nowdate();
            if (!row.received_date) {
                frappe.model.set_value(cdt, cdn, 'received_date', default_date);
            }
        } else {
            if (row.received_date) {
                frappe.model.set_value(cdt, cdn, 'received_date', '');
            }
        }
    },

    received_date(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.received && !row.received_date) {
            frappe.msgprint(__('Received Date is mandatory when document is marked as received.'));
            frappe.model.set_value(cdt, cdn, 'received', 0);
        }
    }
});
