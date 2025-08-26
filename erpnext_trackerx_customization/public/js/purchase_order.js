// Purchase Order Client Script
// File: erpnext_trackerx_customization/public/js/purchase_order.js

frappe.ui.form.on('Purchase Order', {
    onload: function(frm) {
        // Remove existing Material Request get_items button
        setInterval(function()  {
            frm.remove_custom_button(('Material Request'), ('Get Items From'));
        }, 300);
        frm.remove_custom_button(('Material Request'), ('Get Items From'));
                
        // Add custom get items button for Material Requirement Plan
        frm.add_custom_button(('Material Requirement Plan'), function() {
            // Open dialog to select Material Requirement Plan
            let dialog = new frappe.ui.Dialog({
                title: ('Select Material Requirement Plan'),
                fields: [
                    {
                        fieldname: 'material_requirement_plan',
                        fieldtype: 'Link',
                        label: ('Material Requirement Plan'),
                        options: 'Material Requirement Plan',
                        reqd: 1,
                        get_query: function() {
                            return {
                                filters: {
                                    'docstatus': 1,  // Only submitted documents
                                    'status': ['!=', 'Stopped']
                                }
                            };
                        }
                    }
                ],
                primary_action_label: ('Get Items'),
                primary_action: function() {
                    let values = dialog.get_values();
                    if (values) {
                        get_items_from_material_requirement_plan(frm, values);
                        dialog.hide();
                    }
                }
            });
            dialog.show();
        }, ('Get Items From'));
        
        // Add custom button to create Goods Receipt Note
        frm.add_custom_button(('Goods Receipt Note'), function() {
            create_goods_receipt_note(frm);
        }, ('Create'));
    },
    
    refresh: function(frm) {
        // Add button only if PO is submitted and not fully received
        if (frm.doc.docstatus === 1 && frm.doc.per_received < 100) {
            frm.add_custom_button(('Goods Receipt Note'), function() {
                create_goods_receipt_note(frm);
            }, ('Create'));
        }
    }
});

function get_items_from_material_requirement_plan(frm, values) {
    frappe.call({
        method: 'erpnext_trackerx_customization.api.purchase_order.get_items_from_material_requirement_plan',
        args: {
            material_requirement_plan: values.material_requirement_plan,
            source_table: values.source_table,
            purchase_order: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                // Clear existing items
                frm.clear_table('items');
                                
                // Add new items
                r.message.forEach(function(item) {
                    let row = frm.add_child('items');
                    Object.assign(row, item);
                });
                                
                // Refresh the items table
                frm.refresh_field('items');
                // frm.save();
                                
                frappe.msgprint(('Items added successfully'));
            }
        }
    });
}

function create_goods_receipt_note(frm) {
    // Check if PO is submitted
    if (frm.doc.docstatus !== 1) {
        frappe.msgprint(__('Please submit the Purchase Order first'));
        return;
    }
    
    // Check if already fully received
    if (frm.doc.per_received >= 100) {
        frappe.msgprint(__('Purchase Order is already fully received'));
        return;
    }
    
    // Create new Goods Receipt Note
    frappe.model.open_mapped_doc({
        method: 'erpnext_trackerx_customization.api.purchase_order.make_goods_receipt_note',
        frm: frm,
        run_link_triggers: true
    });
}

// Alternative implementation if the mapped doc approach doesn't work
function create_goods_receipt_note_alternative(frm) {
    // Check if PO is submitted
    if (frm.doc.docstatus !== 1) {
        frappe.msgprint(__('Please submit the Purchase Order first'));
        return;
    }
    
    // Check if already fully received
    if (frm.doc.per_received >= 100) {
        frappe.msgprint(__('Purchase Order is already fully received'));
        return;
    }
    
    // Create new Goods Receipt Note
    frappe.call({
        method: 'erpnext_trackerx_customization.api.purchase_order.make_goods_receipt_note',
        args: {
            source_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                frappe.set_route('Form', 'Goods Receipt Note', r.message);
            }
        }
    });
}