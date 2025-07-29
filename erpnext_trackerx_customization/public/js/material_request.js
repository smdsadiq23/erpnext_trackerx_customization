frappe.ui.form.on('Material Request', {
    refresh(frm) {
        if (frm.doc.docstatus === 0 && frm.has_perm("submit")) {
            frm.add_custom_button(
                __('Sales Order & BOM'),
                function () {
                    const dialog = new frappe.ui.Dialog({
                        title: 'Select Sales Order',
                        fields: [
                            {
                                label: 'Sales Order',
                                fieldname: 'sales_order',
                                fieldtype: 'Link',
                                options: 'Sales Order',
                                get_query: () => {
                                    return { filters: { docstatus: 1 } };
                                }
                            }
                        ],
                        primary_action_label: 'Load Items',
                        primary_action: function () {
                            const values = this.get_values();
                            if (!values) return;

                            const selected_so = values.sales_order;

                            // Just warn if this SO already exists
                            const existing_so_item = frm.doc.items.find(item => item.sales_order === selected_so);
                            if (existing_so_item) {
                                frappe.msgprint({
                                    title: __("Warning"),
                                    message: __("You have already selected items from Sales Order {0}", [selected_so]),
                                    indicator: "orange"
                                });
                            }

                            frappe.call({
                                method: 'erpnext_trackerx_customization.erpnext_doctype_hooks.material_request_hooks.get_mr_items_from_sales_order',
                                args: { sales_order: selected_so },
                                callback(r) {
                                    if (r.message) {
                                        let first_empty_row_used = false;

                                        r.message.forEach(item => {
                                            let row;

                                            if (!first_empty_row_used) {
                                                const empty_row = frm.doc.items.find(r =>
                                                    !r.item_code && !r.qty && !r.sales_order
                                                );
                                                if (empty_row) {
                                                    row = empty_row;
                                                    first_empty_row_used = true;
                                                } else {
                                                    row = frm.add_child('items');
                                                }
                                            } else {
                                                row = frm.add_child('items');
                                            }

                                            // Set fields
                                            Object.keys(item).forEach(key => {
                                                frappe.model.set_value(row.doctype, row.name, key, item[key]);
                                            });
                                        });

                                        frm.refresh_field('items');
                                        //frappe.msgprint(__('Items loaded from Sales Order with BOM expansion.'));
                                    }
                                }
                            });

                            dialog.hide();
                        }
                    });

                    dialog.show();
                },
                __('Get Items From')
            );                     
        }

        // Update summary
        frm.trigger('update_item_summary');
    }
});

// Extend to update summary whenever items change

frappe.ui.form.on('Material Request Item', {
    item_code(frm, cdt, cdn) {
        frm.trigger('update_item_summary');
    },
    qty(frm, cdt, cdn) {
        frm.trigger('update_item_summary');
    },    
    items_add: function(frm, cdt, cdn) { 
        frm.trigger('update_item_summary');
        // Your logic here
    },
    items_remove: function(frm, cdt, cdn) { 
        frm.trigger('update_item_summary');
        // Your logic here
    }
});


// Custom method to update summary
$.extend(cur_frm.cscript, {
    update_item_summary: function() {
        const frm = cur_frm;
        if (!frm.doc.items) return;

        // Group by Item Code
        const summary = {};
        let has_warning = false;

        frm.doc.items.forEach(item => {
            if (!item.item_code) return;

            if (!summary[item.item_code]) {
                summary[item.item_code] = {
                    item_code: item.item_code,
                    quantity: 0,
                    custom_size: item.custom_size || null,
                    custom_uom: item.uom || null,
                    uom_mismatch: false,
                    size_mismatch: false
                };
            } else {
                // Check for UOM mismatch
                if (item.uom && summary[item.item_code].custom_uom !== item.uom) {
                    summary[item.item_code].uom_mismatch = true;
                }
                // Check for Size mismatch
                if (item.custom_size && summary[item.item_code].custom_size !== item.custom_size) {
                    summary[item.item_code].size_mismatch = true;
                }
            }

            summary[item.item_code].quantity += flt(item.qty);
        });

        //// Clear and repopulate summary
        // frm.set_value('custom_items_summary', []);

        // Object.values(summary).forEach(row => {
        //     const child = frm.add_child('custom_items_summary');
        //     frappe.model.set_value(child.doctype, child.name, 'item_code', row.item_code);
        //     frappe.model.set_value(child.doctype, child.name, 'quantity', row.quantity);
        //     frappe.model.set_value(child.doctype, child.name, 'custom_uom', row.custom_uom);

        //     // Show size only if no conflict
        //     const size_value = row.size_mismatch ? 'Mixed Sizes' : (row.custom_size || '');
        //     frappe.model.set_value(child.doctype, child.name, 'custom_size', size_value);

        //     // Optional: Warn if UOM or Size is mixed
        //     if (row.uom_mismatch && !has_warning) {
        //         has_warning = true;
        //         frappe.msgprint({
        //             title: __('Warning'),
        //             indicator: 'orange',
        //             message: __('Some items with the same Item Code have different UOMs. Only the first UOM is shown in summary.')
        //         });
        //     }
        // });

        frm.refresh_field('custom_items_summary');
    }
});