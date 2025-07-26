console.log("material_request.js loaded");

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
    }
});
