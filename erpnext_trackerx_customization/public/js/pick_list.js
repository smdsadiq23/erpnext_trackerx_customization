// Client Script for Pick List
frappe.ui.form.on('Pick List', {
    refresh: function(frm) {
        // Hide work order field and show trims order field
        frm.set_df_property('work_order', 'hidden', 1);
        
        // Add custom button to populate items from trims order
        if (frm.doc.trims_order && !frm.doc.__islocal) {
            frm.add_custom_button(__('Get Items from Trims Order'), function() {
                populate_items_from_trims_order(frm);
            });
        }
    },
    
    custom_trims_order: function(frm) {
        console.log('Trims selected: '+frm.doc.custom_trims_order);
        if (frm.doc.custom_trims_order) {
            populate_items_from_trims_order(frm);
        } else {
            // Clear locations if trims order is cleared
            frm.clear_table('locations');
            frm.refresh_field('locations');
        }
    },
    
    onload: function(frm) {
        // Set filters for trims order field
        frm.set_query('custom_trims_order', function() {
            return {
                filters: {
                    'docstatus': 1  // Only submitted trims orders
                }
            };
        });
    }
});

function populate_items_from_trims_order(frm) {
    if (!frm.doc.custom_trims_order) {
        frappe.msgprint(__('Please select a Trims Order first'));
        return;
    }
    
    frappe.show_alert({
        message: __('Fetching items from Trims Order...'),
        indicator: 'blue'
    });
    
    frappe.call({
        method: 'erpnext_trackerx_customization.overrides.pick_list.get_trims_order_items',
        args: {
            trims_order: frm.doc.custom_trims_order
        },
        callback: function(r) {
            console.log('Response recieved');
            console.log(r);
            if (r.message) {
                // Clear existing locations
                frm.clear_table('locations');
                
                // Add items from trims order
                r.message.forEach(function(item) {
                    let row = frm.add_child('locations');
                    row.item_code = item.item_code;
                    row.warehouse = item.warehouse;
                    row.qty = item.trims_order_quantity;
                    row.uom = item.uom;
                    row.item_name = item.item_name;
                    row.item_group = item.item_group;
                    //row.stock_qty = item.stock_qty;
                    
                    // Add custom fields if they exist
                    if (item.sales_order) row.sales_order = item.sales_order;
                    if (item.line_item_no) row.custom_line_item_no = item.line_item_no;
                    if (item.size) row.custom_size = item.size;
                    if (item.item_type) row.item_type = item.item_type;
                    if (item.required_quantity) row.required_quantity = item.required_quantity;
                });
                
                frm.refresh_field('locations');
                
                frappe.show_alert({
                    message: __('Items populated successfully'),
                    indicator: 'green'
                });
            } else {
                frappe.msgprint(__('No items found for the selected Trims Order'));
            }
        },
        error: function(xhr) {
            frappe.msgprint(__('Error fetching items from Trims Order'));
        }
    });
}

// Handle item location changes
frappe.ui.form.on('Pick List Item', {
    warehouse: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.warehouse && row.item_code) {
            // Check available quantity in selected warehouse
            frappe.call({
                method: 'erpnext.stock.utils.get_stock_balance',
                args: {
                    item_code: row.item_code,
                    warehouse: row.warehouse,
                    posting_date: frm.doc.posting_date
                },
                callback: function(r) {
                    if (r.message !== undefined) {
                        let available_qty = r.message;
                        if (available_qty < row.qty) {
                            frappe.msgprint(__('Available quantity in {0} is {1}. Current pick quantity is {2}', 
                                [row.warehouse, available_qty, row.qty]));
                        }
                        
                        // Update a custom field if exists
                        frappe.model.set_value(cdt, cdn, 'available_qty', available_qty);
                    }
                }
            });
        }
    },
    
    qty: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.qty && row.required_quantity && row.qty > row.required_quantity) {
            frappe.msgprint(__('Pick quantity ({0}) cannot exceed required quantity ({1})', 
                [row.qty, row.required_quantity]));
        }
    }
});