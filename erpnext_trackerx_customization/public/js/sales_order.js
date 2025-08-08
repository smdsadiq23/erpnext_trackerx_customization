frappe.ui.form.on('Sales Order', {

    refresh(frm) {
        // Wait for default buttons to load, then remove Work Order
        // frm.page.clear_primary_action();
        // frm.page.clear_actions();

        setTimeout(() => {
          frm.remove_custom_button('Work Order', 'Create');
        }, 1000); 
        
        // Now re-add your own custom button
        if (frm.doc.docstatus === 1 && frm.doc.status !== "Closed") {
        frm.add_custom_button(__('Work Order(s)'), () => {
            open_custom_work_order_dialog(frm);
        }, __('Create'));
        }
    }
  
});

function open_custom_work_order_dialog(frm) {
  const items = frm.doc.items.map(item => ({
    item_code: item.item_code,
    qty: item.qty,
    custom_size: item.custom_size,
    custom_lineitem: item.custom_lineitem,
    so_detail: item.name
  }));

  const dialog = new frappe.ui.Dialog({
    title: 'Custom Work Order Creation',
    fields: [
      {
        fieldtype: 'Link',
        label: 'Source Warehouse',
        fieldname: 'source_warehouse',
        options: 'Warehouse',
        reqd: 1,
        description: 'Warehouse to source raw materials from'
      },
      {
        fieldtype: 'Link',
        label: 'WIP Warehouse',
        fieldname: 'wip_warehouse',
        options: 'Warehouse',
        reqd: 1,
        description: 'Work in Progress warehouse for manufacturing'
      },
      {
        fieldtype: 'Link',
        label: 'Target Warehouse',
        fieldname: 'fg_warehouse',
        options: 'Warehouse',
        reqd: 1,
        description: 'Finished goods warehouse'
      },
      {
        fieldtype: 'Column Break'
      },
      {
        fieldtype: 'Select',
        label: 'Work Order Creation Mode',
        fieldname: 'creation_mode',
        options: [
          'Single Work Order for All',
          'Separate Work Order per Line Item',
          'Separate Work Order per Size'
        ],
        default: 'Single Work Order for All',
        reqd: 1
      },
      {
        fieldtype: 'Section Break'
      },
      {
        fieldtype: 'Table',
        label: 'Sales Order Items',
        fieldname: 'items_table',
        cannot_add_rows: true,
        in_place_edit: false,
        data: items,
        get_data: () => items,
        fields: [
          {
            fieldtype: 'Data',
            fieldname: 'item_code',
            label: 'Item Code',
            in_list_view: true,
            read_only: true
          },
          {
            fieldtype: 'Data',
            fieldname: 'custom_lineitem',
            label: 'Line Item',
            in_list_view: true,
            read_only: true
          },
          {
            fieldtype: 'Data',
            fieldname: 'custom_size',
            label: 'Size',
            in_list_view: true,
            read_only: true
          },
          {
            fieldtype: 'Float',
            fieldname: 'qty',
            label: 'Qty',
            in_list_view: true,
            read_only: true
          }
        ]
      }
    ],
    primary_action_label: 'Create Work Order(s)',
    primary_action(values) {
      const selected_items = dialog.fields_dict.items_table.grid.get_selected_children();
      if (selected_items.length === 0) {
        frappe.throw('Please select at least one line item to create a work order');
      }

      
      const mode = values.creation_mode;
      const source_warehouse = values.source_warehouse;
      const wip_warehouse = values.wip_warehouse;
      const fg_warehouse = values.fg_warehouse;
      
      if (mode === 'Single Work Order for All') {
        create_single_work_order(frm, selected_items, source_warehouse, wip_warehouse, fg_warehouse);
      } else if (mode === 'Separate Work Order per Line Item') {
        create_work_orders_by_line_item(frm, selected_items, source_warehouse, wip_warehouse, fg_warehouse);
      } else if (mode === 'Separate Work Order per Size') {
        create_work_orders_by_size(frm, selected_items, source_warehouse, wip_warehouse, fg_warehouse);
      }

      dialog.hide();
    }
  });

  dialog.show();
}

// Helper function to fetch BOM Items by getting the full BOM document
function get_bom_required_items(bom_no, production_qty, source_warehouse) {
    return new Promise((resolve, reject) => {
        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'BOM',
                name: bom_no
            },
            callback(response) {
                if (response.message && response.message.items) {
                    const required_items = response.message.items.map(bom_item => ({
                        item_code: bom_item.item_code,
                        required_qty: bom_item.qty * production_qty,
                        stock_qty: bom_item.stock_qty * production_qty,
                        uom: bom_item.uom,
                        rate: bom_item.rate || 0,
                        amount: (bom_item.rate || 0) * production_qty,
                        source_warehouse: source_warehouse
                    }));
                    resolve(required_items);
                } else {
                    resolve([]);
                }
            },
            error(error) {
                reject(error);
            }
        });
    });
}

function create_single_work_order(frm, items, source_warehouse, wip_warehouse, fg_warehouse) {
    // Calculate total quantity correctly
    let total_qty = 0;
    for (let item of items) {
        total_qty += item.qty;
    }

    const production_item = items[0].item_code;
    
    // First get BOM for the production item
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'BOM',
            filters: {
                item: production_item,
                is_active: 1,
                is_default: 1
            },
            fields: ['name']
        },
        callback: async function(bom_response) {
            let bom_no = null;
            let required_items = [];
            
            if (bom_response.message && bom_response.message.length > 0) {
                bom_no = bom_response.message[0].name;
                
                try {
                    // Get required items from BOM
                    required_items = await get_bom_required_items(bom_no, total_qty, source_warehouse);
                } catch (error) {
                    frappe.msgprint({
                        title: 'Error',
                        message: 'Failed to fetch BOM items: ' + error.message,
                        indicator: 'red'
                    });
                    return;
                }
            }
            
            // Create the Work Order
            frappe.call({
                method: 'frappe.client.insert',
                args: {
                    doc: {
                        doctype: 'Work Order',
                        production_item: production_item,
                        company: frm.doc.company,
                        qty: total_qty,
                        bom_no: bom_no,
                        source_warehouse: source_warehouse,
                        wip_warehouse: wip_warehouse,
                        fg_warehouse: fg_warehouse,
                        sales_order: frm.doc.name,
                        custom_sales_orders: [{
                            sales_order: frm.doc.name,
                        }],
                        required_items: required_items, // Now using BOM Items
                        custom_work_order_line_items: items.map(i => ({
                            work_order_allocated_qty: i.qty,
                            sales_order: frm.doc.name,
                            sales_order_item: i.so_detail,
                            size: i.custom_size,
                            line_item_no: i.custom_lineitem
                        })),
                    }
                },
                callback(r) {
                    if (r.message) {
                        frappe.set_route('Form', 'Work Order', r.message.name);
                        frappe.show_alert({
                            message: `Work Order ${r.message.name} created successfully`,
                            indicator: 'green'
                        });
                    }
                },
                error(r) {
                    frappe.msgprint({
                        title: 'Error',
                        message: r.message || 'An error occurred while creating the Work Order',
                        indicator: 'red'
                    });
                }
            });
        }
    });
}

function create_work_orders_by_line_item(frm, items, source_warehouse, wip_warehouse, fg_warehouse) {
  items.forEach(async item => {
    // Get BOM for each item
    frappe.call({
      method: 'frappe.client.get_list',
      args: {
        doctype: 'BOM',
        filters: {
          item: item.item_code,
          is_active: 1,
          is_default: 1
        },
        fields: ['name']
      },
      callback: async function(bom_response) {
        let bom_no = null;
        let required_items = [];
        
        if (bom_response.message && bom_response.message.length > 0) {
          bom_no = bom_response.message[0].name;
          
          try {
            // Get required items from BOM
            required_items = await get_bom_required_items(bom_no, item.qty, source_warehouse);
          } catch (error) {
            frappe.msgprint({
              title: 'Error',
              message: `Failed to fetch BOM items for ${item.item_code}: ${error.message}`,
              indicator: 'red'
            });
            return;
          }
        }

        frappe.call({
          method: 'frappe.client.insert',
          args: {
            doc: {
              doctype: 'Work Order',
              production_item: item.item_code,
              company: frm.doc.company,
              qty: item.qty,
              bom_no: bom_no,
              source_warehouse: source_warehouse,
              wip_warehouse: wip_warehouse,
              fg_warehouse: fg_warehouse,
              sales_order: frm.doc.name,
              custom_sales_orders: [{
                            sales_order: frm.doc.name,
                        }],
              sales_order_item: item.so_detail,
              custom_work_order_line_items: [{
                work_order_allocated_qty: item.qty,
                sales_order: frm.doc.name,
                sales_order_item: item.so_detail,
                size: item.custom_size,
                line_item_no: item.custom_lineitem
              }],
              required_items: required_items // Now using BOM Items
            }
          },
          callback(r) {
            if (r.message) {
              frappe.msgprint(`Created Work Order: ${r.message.name}`);
            }
          },
          error(r) {
            frappe.msgprint({
              title: 'Error',
              message: `Failed to create Work Order for ${item.item_code}: ${r.message}`,
              indicator: 'red'
            });
          }
        });
      }
    });
  });
}

function create_work_orders_by_size(frm, items, source_warehouse, wip_warehouse, fg_warehouse) {
  // Create separate work order for each individual item row
  items.forEach(item => {
    // Get BOM for each individual item
    frappe.call({
      method: 'frappe.client.get_list',
      args: {
        doctype: 'BOM',
        filters: {
          item: item.item_code,
          is_active: 1,
          is_default: 1
        },
        fields: ['name']
      },
      callback: async function(bom_response) {
        let bom_no = null;
        let required_items = [];
        
        if (bom_response.message && bom_response.message.length > 0) {
          bom_no = bom_response.message[0].name;
          
          try {
            // Get required items from BOM for this individual item
            required_items = await get_bom_required_items(bom_no, item.qty, source_warehouse);
          } catch (error) {
            frappe.msgprint({
              title: 'Error',
              message: `Failed to fetch BOM items for ${item.item_code} (${item.custom_size}): ${error.message}`,
              indicator: 'red'
            });
            return;
          }
        }

        frappe.call({
          method: 'frappe.client.insert',
          args: {
            doc: {
              doctype: 'Work Order',
              production_item: item.item_code,
              company: frm.doc.company,
              qty: item.qty,
              bom_no: bom_no,
              source_warehouse: source_warehouse,
              wip_warehouse: wip_warehouse,
              fg_warehouse: fg_warehouse,
              sales_order: frm.doc.name,
              custom_sales_orders: [{
                sales_order: frm.doc.name,
              }],
              required_items: required_items, // Now using BOM Items
              custom_work_order_line_items: [{
                work_order_allocated_qty: item.qty,
                sales_order: frm.doc.name,
                sales_order_item: item.so_detail,
                size: item.custom_size,
                line_item_no: item.custom_lineitem
              }]
            }
          },
          callback(r) {
            if (r.message) {
              frappe.msgprint(`Created Work Order for ${item.item_code} (Size: ${item.custom_size}, Line: ${item.custom_lineitem}): ${r.message.name}`);
            }
          },
          error(r) {
            frappe.msgprint({
              title: 'Error',
              message: `Failed to create Work Order for ${item.item_code} (${item.custom_size}): ${r.message}`,
              indicator: 'red'
            });
          }
        });
      }
    });
  });
}

frappe.ui.form.on('Sales Order Item', {
  custom_order_qty: function (frm, cdt, cdn) {
    update_qty_based_on_custom_fields(cdt, cdn);
  },

  custom_tolerance_percentage: function (frm, cdt, cdn) {
    update_qty_based_on_custom_fields(cdt, cdn);
  }
});

function update_qty_based_on_custom_fields(cdt, cdn) {
  const row = locals[cdt][cdn];

  const custom_qty = flt(row.custom_order_qty);
  const tolerance_pct = flt(row.custom_tolerance_percentage);

  if (custom_qty >= 0 && tolerance_pct >= 0) {
    const qty = custom_qty + (custom_qty * tolerance_pct / 100);
    frappe.model.set_value(cdt, cdn, 'qty', qty);
  }
}