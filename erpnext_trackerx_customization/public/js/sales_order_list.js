// Sales Order List View Client Script
// Add this to your Sales Order doctype's List View Settings or as a custom script

frappe.listview_settings['Sales Order'] = {
    onload: function(listview) {
        // Add custom filter for work order eligible orders
        listview.page.add_menu_item(__("Show Work Order Eligible"), function() {
            listview.filter_area.clear();
            listview.filter_area.add([
                ["Sales Order", "docstatus", "=", 1],
                ["Sales Order", "status", "not in", ["Closed", "Cancelled", "Completed", "On Hold"]],
                ["Sales Order Item", "custom_pending_qty_for_work_order", ">", 0]
            ]);
        });

        // Add bulk work order creation button
        listview.page.add_action_item(__("Create Work Order"), function() {
            let selected_docs = listview.get_checked_items();
            
            if (selected_docs.length === 0) {
                frappe.msgprint(__("Please select at least one Sales Order"));
                return;
            }

            // Validate selection before proceeding
            validate_selected_orders(selected_docs, function() {
                let sales_order_names = selected_docs.map(doc => doc.name);
                show_work_order_creation_dialog(sales_order_names);
            });
        });

        // Add quick work order button for individual rows
        listview.page.add_menu_item(__("Quick Work Order from Selected"), function() {
            let selected_docs = listview.get_checked_items();
            if (selected_docs.length !== 1) {
                frappe.msgprint(__("Please select exactly one Sales Order for quick creation"));
                return;
            }
            create_quick_work_order(selected_docs[0].name);
        });
    },

    // Add custom indicator for work order status
    get_indicator: function(doc) {
        if (doc.docstatus === 1 && doc.per_delivered < 100) {
            // Check if has pending items for work order (you might need to add this to list view)
            return [__("Work Order Eligible"), "blue", "status,=,To Deliver"];
        }
    }
};

function show_work_order_creation_dialog(sales_order_names) {
    // First, get available production items and summary from selected sales orders
    frappe.call({
        method: "erpnext_trackerx_customization.api.sales_order.get_production_items_from_sales_orders",
        args: {
            sales_orders: sales_order_names
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                let production_items = r.message;
                
                // Get sales order summary
                frappe.call({
                    method: "erpnext_trackerx_customization.api.sales_order.get_sales_order_summary",
                    args: {
                        sales_orders: sales_order_names
                    },
                    callback: function(summary_r) {
                        let summary = summary_r.message || {};
                        if((production_items.length) > 1)
                        {
                            frappe.throw("All sales order must be for same Item");
                        }
            
                        show_dialog_with_data(production_items, summary, sales_order_names);
                    }
                });
            } else {
                frappe.msgprint(__('No items with pending quantity found in selected Sales Orders'));
            }
        }
    });
}

function show_dialog_with_data(production_items, summary, sales_order_names) {
    let summary_html = `
        <div class="row">
            <div class="col-md-6">
                <p><strong>Selected Orders:</strong> ${summary.total_orders || 0}</p>
                
            </div>
            <div class="col-md-6">
                <p><strong>Total Value:</strong> ${format_currency(summary.total_value || 0)}</p>
            </div>
        </div>
        <div class="text-muted small">${sales_order_names.join(', ')}</div>
    `;
    
    let d = new frappe.ui.Dialog({
        title: __('Create Work Order'),
        size: 'large',
        fields: [
            {
                label: __('Sales Order Summary'),
                fieldname: 'summary',
                fieldtype: 'HTML',
                options: summary_html
            },
            {
                fieldtype: 'Section Break'
            },
            {
                label: __('Production Item'),
                fieldname: 'production_item',
                fieldtype: 'Autocomplete',
                options: production_items.map(item => `${item.item_code} - ${item.item_name}`),
                reqd: 1,
                description: __('Select the item to produce in this work order')
            },
            {
                label: __('Company'),
                fieldname: 'company',
                fieldtype: 'Link',
                options: 'Company',
                reqd: 1,
                default: frappe.defaults.get_user_default('Company')
            },
            {
                fieldtype: 'Column Break'
            },
            {
                label: __('BOM'),
                fieldname: 'bom_no',
                fieldtype: 'Link',
                options: 'BOM',
                depends_on: 'production_item',
                get_query: function() {
                    let production_item = d.get_value('production_item');
                    if (production_item) {
                        // Extract item code from the selection
                        production_item = production_item.split(' - ')[0];
                    }
                    return {
                        filters: {
                            'item': production_item,
                            'is_active': 1,
                            'docstatus': 1
                        }
                    }
                }
            },
            {
                label: __('Work Order Name'),
                fieldname: 'work_order_name',
                fieldtype: 'Data',
                description: __('Leave blank for auto-generated name')
            },
            {
                fieldtype: 'Section Break'
            },
            {
                label: __('Planned Start Date'),
                fieldname: 'planned_start_date',
                fieldtype: 'Datetime',
                default: frappe.datetime.now_datetime()
            }
        ],
        primary_action_label: __('Create Work Order'),
        primary_action: function(values) {
            if (!values.production_item) {
                frappe.msgprint(__('Please select a Production Item'));
                return;
            }

            // Extract item code from the selection
            let production_item = values.production_item.split(' - ')[0];

            frappe.call({
                method: "erpnext_trackerx_customization.api.sales_order.create_work_order_from_sales_orders",
                args: {
                    sales_orders: sales_order_names,
                    production_item: production_item,
                    work_order_name: values.work_order_name,
                    company: values.company,
                    bom_no: values.bom_no,
                    planned_start_date: values.planned_start_date
                },
                freeze: true,
                freeze_message: __('Creating Work Order...'),
                callback: function(r) {
                    if (r.message) {
                        frappe.show_alert({
                            message: __('Work Order {0} created successfully', [r.message]),
                            indicator: 'green'
                        });
                        
                        // Redirect to the created work order
                        setTimeout(() => {
                            frappe.set_route("Form", "Work Order", r.message);
                        }, 1500);
                    }
                }
            });
            
            d.hide();
        }
    });

    // Update BOM field when production item changes
    d.fields_dict.production_item.df.change = function() {
        d.set_value('bom_no', '');
        d.fields_dict.bom_no.refresh();
    };

    d.show();
}


function validate_selected_orders(selected_docs, callback) {
    // Check if selected orders are valid for work order creation
    let order_names = selected_docs.map(doc => doc.name);
    
    frappe.call({
        method: "erpnext_trackerx_customization.api.sales_order.validate_orders_for_work_order",
        args: {
            sales_orders: order_names
        },
        callback: function(r) {
            if (r.message && r.message.valid) {
                callback();
            } else {
                let msg = r.message ? r.message.message : "Selected orders are not valid for work order creation";
                frappe.msgprint({
                    title: __("Validation Error"),
                    message: msg,
                    indicator: "red"
                });
            }
        }
    });
}

function create_quick_work_order(sales_order_name) {
    // Quick creation with minimal dialog
    frappe.call({
        method: "erpnext_trackerx_customization.api.sales_order.get_production_items_from_sales_orders",
        args: {
            sales_orders: [sales_order_name]
        },
        callback: function(r) {
            if (r.message && r.message.length === 1) {
                // Only one production item, create directly
                let item = r.message[0];
                frappe.confirm(
                    __("Create Work Order for {0} from Sales Order {1}?", [item.item_name, sales_order_name]),
                    function() {
                        frappe.call({
                            method: "erpnext_trackerx_customization.api.sales_order.create_work_order_from_sales_orders",
                            args: {
                                sales_orders: [sales_order_name],
                                production_item: item.item_code,
                                company: frappe.defaults.get_user_default('Company')
                            },
                            callback: function(r) {
                                if (r.message) {
                                    frappe.show_alert({
                                        message: __("Work Order {0} created", [r.message]),
                                        indicator: "green"
                                    });
                                    frappe.set_route("Form", "Work Order", r.message);
                                }
                            }
                        });
                    }
                );
            } else {
                // Multiple items, show dialog
                show_work_order_creation_dialog([sales_order_name]);
            }
        }
    });
}

// Add keyboard shortcut for work order creation
$(document).on('keydown', function(e) {
    if (e.ctrlKey && e.shiftKey && e.which === 87) { // Ctrl+Shift+W
        let listview = cur_list;
        if (listview && listview.doctype === 'Sales Order') {
            let selected_docs = listview.get_checked_items();
            if (selected_docs.length > 0) {
                let sales_order_names = selected_docs.map(doc => doc.name);
                show_work_order_creation_dialog(sales_order_names);
            } else {
                frappe.msgprint(__("Please select Sales Orders first"));
            }
        }
    }
});