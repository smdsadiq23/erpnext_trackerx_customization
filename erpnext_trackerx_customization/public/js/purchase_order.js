// Purchase Order Client Script
// File: erpnext_trackerx_customization/public/js/purchase_order.js

frappe.ui.form.on('Purchase Order', {
    onload: function(frm) {
        // Remove existing Material Request get_items button
        setInterval(function()  {
            frm.remove_custom_button(__('Material Request'), __('Get Items From'));
        }, 300);
        frm.remove_custom_button(__('Material Request'), __('Get Items From'));
        
        // Add custom get items button for Material Requirement Plan
        frm.add_custom_button(__('Material Requirement Plan'), function() {
            // Open dialog to select Material Requirement Plan
            let dialog = new frappe.ui.Dialog({
                title: __('Select Material Requirement Plan'),
                fields: [
                    {
                        fieldname: 'material_requirement_plan',
                        fieldtype: 'Link',
                        label: __('Material Requirement Plan'),
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
                    },
                    // {
                    //     fieldname: 'source_table',
                    //     fieldtype: 'Select',
                    //     label: __('Source Table'),
                    //     options: 'Items\nItems Summary',
                    //     default: 'Items',
                    //     reqd: 1,
                    //     description: __('Select which table to pull items from')
                    // }
                ],
                primary_action_label: __('Get Items'),
                primary_action: function() {
                    let values = dialog.get_values();
                    if (values) {
                        get_items_from_material_requirement_plan(frm, values);
                        dialog.hide();
                    }
                }
            });
            dialog.show();
        }, __('Get Items From'));
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
                
                frappe.msgprint(__('Items added successfully'));
            }
        }
    });
}