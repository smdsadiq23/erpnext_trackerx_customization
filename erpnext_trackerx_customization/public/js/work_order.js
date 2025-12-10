// Client Script for Work Order
// Add this to your Work Order doctype's Client Script

frappe.ui.form.on('Work Order', {
    production_item: function(frm) {
        // Clear existing sales orders when production item changes
        frm.clear_table("custom_sales_orders");
        frm.refresh_field("custom_sales_orders");
        frm.clear_table("custom_work_order_line_items");
        frm.refresh_field("custom_work_order_line_items");        
        
        // Set filter for the child table
        set_sales_order_filter(frm);
    },
    
    onload: function(frm) {
        // Set filter when form loads
        set_sales_order_filter(frm);
        frm.set_df_property('custom_work_order_line_items', 'cannot_add_rows', true);
        frm.set_df_property('custom_work_order_line_items', 'cannot_delete_rows', true);
    },

    refresh: function(frm){
        // FIX: Disable timeline rendering to prevent version timeline errors
        if (frm.timeline && frm.timeline.$timeline_items) {
            try {
                frm.timeline.$timeline_items.empty();
            } catch (e) {
                console.warn('Timeline clearing failed:', e);
            }
        }

        frm.remove_custom_button('Create Pick List');
        if (frm.doc.docstatus === 1 && frm.doc.status !== "Closed") {
          frm.add_custom_button(__('Create Trims Order'), () => {
              show_create_trims_order_dialogue(frm);
          });
        }
    },

    custom_sales_orders(frm) {
        frm.trigger('sync_work_order_line_items');
    },

    custom_work_order_line_items: function(frm){
        recalculate_total_qty(frm);
    },
    sync_work_order_line_items(frm) {
        const selected_sales_orders = frm.doc.custom_sales_orders.map(row => row.sales_order);
        if (!selected_sales_orders.length || !frm.doc.production_item) {
            frm.clear_table("custom_work_order_line_items")
            frm.refresh_field("custom_work_order_line_items");
            recalculate_total_qty(frm);
            return;
        } 

        frappe.call({
            method: "erpnext_trackerx_customization.api.sales_order.get_sales_order_items",
            args: {
                work_order_name: frm.doc.name,
                sales_orders: frm.doc.custom_sales_orders.map(row => row.sales_order),
                item_code: frm.doc.production_item
            },
            callback: function(res) {
                const so_items = res.message || [];
                const existing_so_item_ids = frm.doc.custom_work_order_line_items.map(row => row.sales_order_item);

                console.log(so_items);
                console.log("existing so item ids")
                console.log(existing_so_item_ids);
                
                // Add new ones or update existing ones
                so_items.forEach(item => {
                    console.log("In loop");
                    console.log(item);
                    
                    const existing_row_index = frm.doc.custom_work_order_line_items.findIndex(
                        row => row.sales_order_item === item.name
                    );
                    
                    if (existing_row_index === -1) {
                        // Add new row
                        console.log("Doesn't exist and adding new row")
                        let child = frm.add_child("custom_work_order_line_items");
                        child.sales_order_item = item.name;
                        child.line_item_no = item.custom_lineitem;
                        child.size = item.custom_size;
                        child.qty = item.qty;
                        child.already_allocated_qty = item.custom_allocated_qty_for_work_order;                        
                        child.work_order_allocated_qty = item.custom_pending_qty_for_work_order;
                        //child.pending_qty = item.custom_pending_qty_for_work_order;
                        child.pending_qty = 0;
                        child.sales_order = item.parent;
                    } else {
                        // Update existing row with fresh data
                        let existing_row = frm.doc.custom_work_order_line_items[existing_row_index];
                        // Preserve the work_order_allocated_qty but update other fields
                        existing_row.line_item_no = item.custom_lineitem;
                        existing_row.size = item.custom_size;
                        existing_row.qty = item.qty;
                        existing_row.already_allocated_qty = item.custom_allocated_qty_for_work_order;
                        //existing_row.pending_qty = item.custom_pending_qty_for_work_order;
                        existing_row.pending_qty = i0;
                        existing_row.sales_order = item.parent;
                    }
                });

                // Remove items from deselected sales orders
                frm.doc.custom_work_order_line_items = frm.doc.custom_work_order_line_items.filter(item =>
                    selected_sales_orders.includes(item.sales_order)
                );

                frm.refresh_field("custom_work_order_line_items");

                // Make only work_order_allocated_qty editable
                const grid = frm.fields_dict.custom_work_order_line_items.grid;
                if (grid) {
                    ["line_item_no", "size", "qty", "already_allocated_qty", "pending_qty", "sales_order_item"]
                        .forEach(fieldname => {
                            grid.toggle_enable(fieldname, false);
                        });
                }

                recalculate_total_qty(frm);
            }
    });
}

});

function show_create_trims_order_dialogue(frm){

    const dialog = new frappe.ui.Dialog({
    title: 'Create Trims Order',
    fields: [
      {
        fieldtype: 'Data',
        label: 'Work Center',
        fieldname: 'work_center',
        options: '',
        reqd: 1,
        description: 'Choose Work Center'
      }
    ],
    primary_action_label: 'Create',
    primary_action(values) {
    
      
        create_trims_order(frm, values.work_center);
        dialog.hide();
    }
  });

  dialog.show();
}

function create_trims_order(frm, work_center){


    const production_item = frm.doc.production_item;

    frappe.throw("Feature is under development, Till then please create Pick List from pick list doctype");
    
    
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
                    required_items = await get_raw_materials_from_bom_except_fabrics(bom_no, frm.doc.custom_work_order_line_items);
                } catch (error) {
                    frappe.msgprint({
                        title: 'Error',
                        message: 'Failed to fetch BOM items: ' + error.message,
                        indicator: 'red'
                    });
                    return;
                }
            }
            
             // Create Trims Order
            frappe.call({
                method: 'frappe.client.insert',
                args: {
                    doc: {
                        doctype: 'Trims Order',
                        work_order: frm.doc.name,
                        item_code: frm.doc.production_item,
                        work_center: work_center,
                        table_trims_order_details: required_items
                    }
                },
                callback(r) {
                    if (r.message) {
                        frappe.set_route('Form', 'Trims Order', r.message.name);
                        frappe.show_alert({
                            message: `Trims Order ${r.message.name} created successfully`,
                            indicator: 'green'
                        });
                    }
                },
                error(r) {
                    frappe.msgprint({
                        title: 'Error',
                        message: r.message || 'An error occurred while creating the Trims Order',
                        indicator: 'red'
                    });
                }
            });
        }
    });
}


function get_raw_materials_from_bom_except_fabrics(bom_no, work_order_line_items) {

    work_order_line_items.forEach(work_order)


    return new Promise((resolve, reject) => {
        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'BOM',
                name: bom_no
            },
            callback(response) {
                if (response.message && response.message.items) {
                    const required_items = response.message.items.filter(bom_item => bom_item.custom_item_type!='Fabrics').map(bom_item => ({
                        item_type: bom_item.custom_item_type,
                        item_code: bom_item.item_code,
                        size: bom_item.custom_size,
                        uom: bom_item.uom,
                        qty: bom_item.qty || 0,
                        rate: bom_item.rate || 0,
                        amount: (bom_item.rate || 0) * (bom_item.qty||0)
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

function set_sales_order_filter(frm) {
    if (frm.doc.production_item) {
        frm.set_query( "custom_sales_orders", function() {
            return {
                "filters": {
                    "docstatus": 1, // Only submitted sales orders
                    "status": ["not in", ["Closed", "Cancelled" , "Completed", "On Hold" ]], // Exclude closed/cancelled
                    // Filter based on production item - you have several options:
                    
                    // Option 1: Direct item code match in sales order items
                    "item_code": frm.doc.production_item
                
                }
            };
        });
    } else {
        // Clear filter if no production item selected
        frm.set_query("custom_sales_orders", function() {
            return {
                "filters": {
                    "docstatus": 1,
                    "status": ["not in", ["Closed", "Cancelled"]],
                    "name": "__None__"
                }
            };
        });
    }
}

function recalculate_total_qty(frm) {
    let total_qty = 0;
    const wo_line_items = frm.doc.custom_work_order_line_items || [];

    wo_line_items.forEach(function(row) {
        total_qty += flt(row.work_order_allocated_qty);
    });

    frm.set_value("qty", total_qty);
    frm.refresh_field("qty");
}




frappe.ui.form.on('Work Order Line Item', {
    work_order_allocated_qty: function(frm, cdt, cdn) {
        recalculate_total_qty(frm);

        const row = locals[cdt][cdn];

        const pending_qty = flt(row.qty) - flt(row.already_allocated_qty) - flt(row.work_order_allocated_qty);
      
        frappe.model.set_value(cdt, cdn, 'pending_qty', pending_qty);
      
    }
});