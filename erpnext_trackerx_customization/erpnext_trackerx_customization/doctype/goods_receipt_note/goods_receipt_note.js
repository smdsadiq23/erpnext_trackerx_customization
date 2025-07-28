// Copyright (c) 2025, CognitionX and contributors
// For license information, please see license.txt

frappe.ui.form.on("Goods Receipt Note", {
    refresh(frm) {
        // Only run for new documents
        if (frm.doc.__islocal && frm.doc.document_checklist.length === 0) {
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
                frappe.model.set_value(row.doctype, row.name, 'is_required', 1); // Mark as required
            });

            // Add optional documents (not mandatory)
            optional_docs.forEach(doc => {
                const row = frm.add_child('document_checklist');
                frappe.model.set_value(row.doctype, row.name, 'document_type', doc);
                frappe.model.set_value(row.doctype, row.name, 'is_required', 0);
            });

            frm.refresh_field('document_checklist');
        }
    },

    //Validate Document checklist Received and Received Date
    validate: function(frm) {
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
    },

    before_save(frm) {
        // Iterate through all checklist rows
        frm.doc.document_checklist.forEach(row => {
            if (row.photo_upload && row.document_type === 'Photo Evidence') {
                // Ensure files are linked to the parent document
                frappe.model.set_value(row.doctype, row.name, 'attached_to_doctype', 'Goods Receipt Note');
                frappe.model.set_value(row.doctype, row.name, 'attached_to_name', frm.doc.name);
            }
        });
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

// Handle actions on each row in the checklist
frappe.ui.form.on('Goods Receipt Document Checklist', {
    received(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.received) {
            // Auto-fill today's date (or transaction_date)
            const default_date = frm.doc.transaction_date || frappe.datetime.nowdate();
            if (!row.received_date) {
                frappe.model.set_value(cdt, cdn, 'received_date', default_date);
            }
        } else {
            // Optional: Clear date if unchecked
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
