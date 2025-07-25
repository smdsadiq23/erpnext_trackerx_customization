console.log("✅ material_request.js loaded");

frappe.ui.form.on('Material Request', {
    refresh(frm) {
        if (frm.doc.docstatus === 0 && frm.has_perm("submit")) {
            frm.add_custom_button(
                __('Get Items from Sales Order (Custom)'),
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

                            frm.clear_table('items');

                            frappe.call({
                                method: 'erpnext_trackerx_customization.erpnext_doctype_hooks.material_request_hooks.get_mr_items_from_sales_order',
                                args: { sales_order: values.sales_order },
                                callback(r) {
                                    if (r.message) {
                                        r.message.forEach(item => {
                                            const row = frm.add_child('items');
                                            Object.keys(item).forEach(key => {
                                                frappe.model.set_value(row.doctype, row.name, key, item[key]);
                                            });
                                        });
                                        frm.refresh_field('items');
                                        frappe.msgprint(__('Items loaded with BOM expansion'));
                                    }
                                }
                            });
                            dialog.hide();
                        }
                    });
                    dialog.show();
                },
                __('Get Items')
            );
        }
    }
});