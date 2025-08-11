// Enhanced Sales Order List View Client Script
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
    }
};

function show_work_order_creation_dialog(sales_order_names) {
    // Get available production items and line items from selected sales orders
    frappe.call({
        method: "erpnext_trackerx_customization.api.sales_order.get_production_items_from_sales_orders",
        args: {
            sales_orders: sales_order_names
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                let production_items = r.message;
                
                if (production_items.length > 1) {
                    frappe.throw("All sales orders must be for the same Item");
                }
                
                // Get detailed line items and summary
                frappe.call({
                    method: "erpnext_trackerx_customization.api.sales_order.get_sales_order_line_items_detailed",
                    args: {
                        sales_orders: sales_order_names,
                        production_item: production_items[0].item_code
                    },
                    callback: function(line_items_r) {
                        let line_items_data = line_items_r.message || {};
                        show_enhanced_dialog_with_line_items(production_items[0], line_items_data, sales_order_names);
                    }
                });
            } else {
                frappe.msgprint(__('No items with pending quantity found in selected Sales Orders'));
            }
        }
    });
}

function show_enhanced_dialog_with_line_items(production_item, line_items_data, sales_order_names) {
    let summary_html = `
        <div class="row">
            <div class="col-md-4">
                <p><strong>Selected Orders:</strong> ${sales_order_names.length}</p>
            </div>
            <div class="col-md-4">
                <p><strong>Total Line Items:</strong> ${line_items_data.line_items ? line_items_data.line_items.length : 0}</p>
            </div>
            <div class="col-md-4">
                <p><strong>Total Pending Qty:</strong> ${line_items_data.total_pending_qty || 0}</p>
            </div>
        </div>
        <div class="text-muted small">${sales_order_names.join(', ')}</div>
    `;
    
    // Get default BOM
    frappe.call({
        method: "frappe.client.get_value",
        args: {
            doctype: "BOM",
            filters: {
                item: production_item.item_code,
                is_active: 1,
                docstatus: 1
            },
            fieldname: ["name", "quantity"]
        },
        callback: function(bom_r) {
            let default_bom = bom_r.message ? bom_r.message.name : null;
            show_dialog_with_data(production_item, line_items_data, sales_order_names, summary_html, default_bom);
        }
    });
}

function show_dialog_with_data(production_item, line_items_data, sales_order_names, summary_html, default_bom) {
    let d = new frappe.ui.Dialog({
        title: __('Create Work Order'),
        size: 'extra-large',
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
                fieldtype: 'Link',
                options: 'Item',
                reqd: 1,
                read_only: 1,
                default: production_item.item_code
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
                reqd: 1,
                default: default_bom,
                get_query: function() {
                    return {
                        filters: {
                            'item': production_item.item_code,
                            'is_active': 1,
                            'docstatus': 1
                        }
                    }
                }
            },
            {
                label: __('Planned Start Date'),
                fieldname: 'planned_start_date',
                fieldtype: 'Datetime',
                default: frappe.datetime.now_datetime()
            },
            {
                fieldtype: 'Section Break',
                label: __('Select Line Items')
            },
            {
                label: __('Line Items'),
                fieldname: 'line_items',
                fieldtype: 'Table',
                cannot_add_rows: true,
                cannot_delete_rows: true,
                data: line_items_data.line_items || [],
                fields: [
                    {
                        label: __('Select'),
                        fieldname: 'select_item',
                        fieldtype: 'Check',
                        in_list_view: 1,
                        columns: 1
                    },
                    {
                        label: __('Sales Order'),
                        fieldname: 'sales_order',
                        fieldtype: 'Link',
                        options: 'Sales Order',
                        in_list_view: 1,
                        read_only: 1,
                        columns: 2
                    },
                    {
                        label: __('Line Item No'),
                        fieldname: 'line_item_no',
                        fieldtype: 'Data',
                        in_list_view: 1,
                        read_only: 1,
                        columns: 1
                    },
                    {
                        label: __('Size'),
                        fieldname: 'size',
                        fieldtype: 'Data',
                        in_list_view: 1,
                        read_only: 1,
                        columns: 1
                    },
                    {
                        label: __('Total Qty'),
                        fieldname: 'total_qty',
                        fieldtype: 'Float',
                        in_list_view: 1,
                        read_only: 1,
                        columns: 1
                    },
                    {
                        label: __('Pending Qty'),
                        fieldname: 'pending_qty',
                        fieldtype: 'Float',
                        in_list_view: 1,
                        read_only: 1,
                        columns: 1
                    },
                    {
                        label: __('Allocate Qty'),
                        fieldname: 'allocate_qty',
                        fieldtype: 'Float',
                        in_list_view: 1,
                        columns: 1,
                        default: 1.0
                    },
                    {
                        label: __('Sales Order Item ID'),
                        fieldname: 'sales_order_item',
                        fieldtype: 'Data',
                        hidden: 1
                    }
                ]
            },
            {
                fieldtype: 'Section Break',
                label: __('Work Order Creation Options')
            },
            {
                label: __('Creation Strategy'),
                fieldname: 'creation_strategy',
                fieldtype: 'Select',
                options: [
                    'Single Work Order for All Selected Items',
                    'Individual Work Order for Each Line Item',
                    'Individual Work Order for Each Row'
                ].join('\n'),
                default: 'Single Work Order for All Selected Items',
                reqd: 1,
                description: __('Choose how to create work orders from selected line items')
            }
        ],
        primary_action_label: __('Create Work Order(s)'),
        primary_action: function(values) {
            // Get selected line items
            let selected_items = values.line_items.filter(item => item.select_item);
            
            if (selected_items.length === 0) {
                frappe.msgprint(__('Please select at least one line item'));
                return;
            }

            // Validate allocate quantities
            let invalid_qty = selected_items.find(item => !item.allocate_qty || item.allocate_qty <= 0 || item.allocate_qty > item.pending_qty);
            if (invalid_qty) {
                frappe.msgprint(__('Please enter valid allocate quantities (must be > 0 and <= pending qty)'));
                return;
            }

            // Create work orders based on strategy
            create_work_orders_by_strategy(selected_items, values, sales_order_names);
            d.hide();
        }
    });

    // Add bulk select/deselect functionality
    d.$wrapper.find('.modal-body').prepend(`
        <div class="row" style="margin-bottom: 10px;">
            <div class="col-md-12">
                <button class="btn btn-xs btn-default" onclick="select_all_line_items()" type="button">Select All</button>
                <button class="btn btn-xs btn-default" onclick="deselect_all_line_items()" type="button">Deselect All</button>
            </div>
        </div>
    `);

    // Make select all/deselect all functions global
    window.select_all_line_items = function() {
        let line_items = d.get_value('line_items');
        line_items.forEach(item => item.select_item = 1);
        d.fields_dict.line_items.grid.refresh();
    };

    window.deselect_all_line_items = function() {
        let line_items = d.get_value('line_items');
        line_items.forEach(item => item.select_item = 0);
        d.fields_dict.line_items.grid.refresh();
    };

    d.show();
}

function create_work_orders_by_strategy(selected_items, values, sales_order_names) {
    const strategy = values.creation_strategy;
    
    if (strategy === 'Single Work Order for All Selected Items') {
        create_single_work_order(selected_items, values, sales_order_names);
    } else if (strategy === 'Individual Work Order for Each Line Item') {
        create_work_orders_by_line_item(selected_items, values, sales_order_names);
    } else if (strategy === 'Individual Work Order for Each Row') {
        create_work_orders_by_row(selected_items, values, sales_order_names);
    }
}

function create_single_work_order(selected_items, values, sales_order_names) {
    frappe.call({
        method: "erpnext_trackerx_customization.api.sales_order.create_work_order_from_line_items",
        args: {
            line_items: selected_items,
            production_item: values.production_item,
            company: values.company,
            bom_no: values.bom_no,
            planned_start_date: values.planned_start_date,
            creation_strategy: 'single'
        },
        freeze: true,
        freeze_message: __('Creating Work Order...'),
        callback: function(r) {
            if (r.message) {
                frappe.show_alert({
                    message: __('Work Order {0} created successfully', [r.message]),
                    indicator: 'green'
                });
                setTimeout(() => {
                    frappe.set_route("Form", "Work Order", r.message);
                }, 1500);
            }
        }
    });
}

function create_work_orders_by_line_item(selected_items, values, sales_order_names) {
    // Group by line_item_no
    let grouped_items = {};
    selected_items.forEach(item => {
        if (!grouped_items[item.line_item_no]) {
            grouped_items[item.line_item_no] = [];
        }
        grouped_items[item.line_item_no].push(item);
    });

    frappe.call({
        method: "erpnext_trackerx_customization.api.sales_order.create_work_orders_bulk",
        args: {
            grouped_items: grouped_items,
            production_item: values.production_item,
            company: values.company,
            bom_no: values.bom_no,
            planned_start_date: values.planned_start_date,
            creation_strategy: 'by_line_item'
        },
        freeze: true,
        freeze_message: __('Creating Work Orders...'),
        callback: function(r) {
            if (r.message) {
                let result = r.message;
                frappe.show_alert({
                    message: __('Created {0} Work Orders successfully', [result.success_count]),
                    indicator: 'green'
                });
                
                if (result.created_work_orders.length > 0) {
                    setTimeout(() => {
                        frappe.set_route("List", "Work Order", {
                            "name": ["in", result.created_work_orders]
                        });
                    }, 1500);
                }
            }
        }
    });
}

function create_work_orders_by_row(selected_items, values, sales_order_names) {
    frappe.call({
        method: "erpnext_trackerx_customization.api.sales_order.create_work_orders_bulk",
        args: {
            individual_items: selected_items,
            production_item: values.production_item,
            company: values.company,
            bom_no: values.bom_no,
            planned_start_date: values.planned_start_date,
            creation_strategy: 'by_row'
        },
        freeze: true,
        freeze_message: __('Creating Work Orders...'),
        callback: function(r) {
            if (r.message) {
                let result = r.message;
                frappe.show_alert({
                    message: __('Created {0} Work Orders successfully', [result.success_count]),
                    indicator: 'green'
                });
                
                if (result.created_work_orders.length > 0) {
                    setTimeout(() => {
                        frappe.set_route("List", "Work Order", {
                            "name": ["in", result.created_work_orders]
                        });
                    }, 1500);
                }
            }
        }
    });
}

function validate_selected_orders(selected_docs, callback) {
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