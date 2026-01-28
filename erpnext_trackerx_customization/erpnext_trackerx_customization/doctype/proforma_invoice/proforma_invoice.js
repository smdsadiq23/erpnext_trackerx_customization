// Copyright (c) 2026, CognitionX Logic India Private Limited and contributors
// For license information, please see license.txt


frappe.ui.form.on('Proforma Invoice', {
    refresh: function(frm) {
        setup_child_table(frm);
    },
    
    // Client-side validation for immediate feedback
    validate: function(frm) {
        if (!frm.doc.items || frm.doc.items.length === 0) {
            frappe.throw(__('Proforma Invoice Item table cannot be empty. Please add at least one item before saving.'));
            return false;
        }
        
        // Quick client-side check for critical fields
        const invalid_rows = frm.doc.items.filter(row => 
            !row.item_code || !row.qty || row.qty <= 0 || !row.rate || row.rate <= 0
        );
        
        if (invalid_rows.length > 0) {
            frappe.throw(__('Please ensure all items have valid Item Code, Quantity (>0), and Rate (>0).'));
            return false;
        }
        
        return true;
    }
});

// Child table field change handlers
frappe.ui.form.on('Proforma Invoice Item', {
    rate: function(frm, cdt, cdn) {
        calculate_amount(frm, cdt, cdn);
    },
    
    qty: function(frm, cdt, cdn) {
        calculate_amount(frm, cdt, cdn);
    }
});

function calculate_amount(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    const qty = flt(row.qty) || 0;
    const rate = flt(row.rate) || 0;
    
    // Calculate amount
    const amount = qty * rate;
    
    // Update the amount field
    frappe.model.set_value(cdt, cdn, 'amount', amount);
}

function setup_child_table(frm) {
    const fieldname = "items";
    const grid = frm.fields_dict[fieldname]?.grid;
    
    if (!grid) return;

    // Hide the default "Add Row" button
    hide_add_row_button(grid);

    // Add custom fetch button if not already added
    if (!grid.fetch_button_added) {
        grid.add_custom_button(
            __("Fetch from Sales Orders"),
            function() {
                if (!frm.doc.po_number?.trim()) {
                    frappe.msgprint({
                        title: __('Missing PO Number'),
                        indicator: 'orange',
                        message: __('Please enter PO Number first before fetching items.')
                    });
                    return;
                }
                
                // Clear existing items before fetching new ones
                frm.clear_table('items');
                frm.refresh_field('items');
                
                frm.call({
                    method: 'fetch_items_from_sales_orders',
                    doc: frm.doc,
                    freeze: true,
                    freeze_message: __('Fetching items from Sales Orders...'),
                    callback: function(r) {
                        if (r.message) {
                            frm.refresh_field('items');
                            
                            // Refresh delivery_date field if populated
                            if (r.message.delivery_date) {
                                frm.refresh_field('delivery_date');
                            }
                            
                            frappe.show_alert({
                                message: __('✅ Loaded {0} items from {1} Sales Order(s)', 
                                    [r.message.item_count, r.message.sales_order_count]),
                                indicator: 'green'
                            });
                        } else {
                            frappe.msgprint({
                                title: __('No Items Found'),
                                indicator: 'orange',
                                message: __('No items found for this PO Number. Please verify Sales Orders.')
                            });
                        }
                    },
                    error: function(r) {
                        frappe.msgprint({
                            title: __('Fetch Failed'),
                            indicator: 'red',
                            message: r.message || __('No matching Sales Orders found for this PO Number')
                        });
                    }
                });
            },
            __("Actions")
        );
        
        grid.fetch_button_added = true;
    }
}

function hide_add_row_button(grid) {
    // Initial hide
    setTimeout(() => {
        if (grid.grid_buttons) {
            grid.grid_buttons.find(".grid-add-row").hide();
        }
    }, 50);

    // Patch grid refresh to keep button hidden
    if (!grid.refresh_patched) {
        const original_refresh = grid.refresh;
        grid.refresh = function() {
            original_refresh.apply(this, arguments);
            setTimeout(() => {
                if (this.grid_buttons) {
                    this.grid_buttons.find(".grid-add-row").hide();
                }
            }, 50);
        };
        grid.refresh_patched = true;
    }
}