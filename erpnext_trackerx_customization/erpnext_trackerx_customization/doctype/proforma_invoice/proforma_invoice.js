// Copyright (c) 2026, CognitionX Logic India Private Limited and contributors
// For license information, please see license.txt


frappe.ui.form.on('Proforma Invoice', {
    onload: function(frm) {
        // Load available PO numbers when form loads
        load_available_po_numbers(frm);
    },
    
    refresh: function(frm) {
        setup_child_table(frm);
    },
    
    po_number: function(frm) {
        // Auto-fetch items when PO number is selected
        if (frm.doc.po_number && frm.doc.po_number.trim()) {
            // Clear all linked fields before fetching new data
            clear_linked_fields(frm);
            
            // Fetch items from Sales Orders
            frm.call({
                method: 'fetch_items_from_sales_orders',
                doc: frm.doc,
                freeze: true,
                freeze_message: __('Fetching items from Sales Orders...'),
                callback: function(r) {
                    if (r.message) {
                        frm.refresh_field('items');
                        frm.refresh_field('buyer');
                        frm.refresh_field('currency');
                        frm.refresh_field('delivery_date');
                        frm.refresh_field('quality');
                        frm.refresh_field('payment_terms');
                        frm.refresh_field('delivery_terms');
                        
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
        } else {
            // Clear all fields if PO number is cleared
            clear_linked_fields(frm);
        }
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

// Load available PO numbers into select field
function load_available_po_numbers(frm) {
    frm.call({
        method: 'erpnext_trackerx_customization.erpnext_trackerx_customization.doctype.proforma_invoice.proforma_invoice.get_available_po_numbers',
        freeze: false,
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                // Convert to newline-separated options for Select field
                const options = [""] // Empty option first
                    .concat(r.message.map(po => po))
                    .join("\n");
                frm.set_df_property('po_number', 'options', options);
                
                // If editing existing doc, preserve current value even if not in options
                if (frm.doc.po_number && !r.message.includes(frm.doc.po_number)) {
                    frm.set_df_property('po_number', 'options', 
                        options + "\n" + frm.doc.po_number);
                }
            } else {
                frm.set_df_property('po_number', 'options', "\n[No available PO numbers]");
                if (!frm.doc.po_number) {
                    frm.set_value('po_number', '[No available PO numbers]');
                }
            }
            frm.refresh_field('po_number');
        },
        error: function() {
            console.warn("Failed to load PO numbers. Using manual entry.");
            frm.set_df_property('po_number', 'fieldtype', 'Data');
            frm.refresh_field('po_number');
        }
    });
}

// Clear all linked fields when PO number changes
function clear_linked_fields(frm) {
    // Clear child table
    frm.clear_table('items');
    frm.refresh_field('items');
    
    // Clear linked fields
    frm.set_value('buyer', '');
    frm.set_value('currency', '');
    frm.set_value('delivery_date', '');
    frm.set_value('quality', '');
    frm.set_value('payment_terms', '');
    frm.set_value('delivery_terms', '');
    
    // Refresh fields
    frm.refresh_field('buyer');
    frm.refresh_field('currency');
    frm.refresh_field('delivery_date');
    frm.refresh_field('quality');
    frm.refresh_field('payment_terms');
    frm.refresh_field('delivery_terms');
}