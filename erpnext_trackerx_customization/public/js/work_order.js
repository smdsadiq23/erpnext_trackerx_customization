// Client Script for Work Order
// Add this to your Work Order doctype's Client Script

frappe.ui.form.on('Work Order', {
    production_item: function(frm) {
        // Clear existing sales orders when production item changes
        frm.clear_table("custom_sales_orders");
        frm.refresh_field("custom_sales_orders");
        
        // Set filter for the child table
        set_sales_order_filter(frm);
    },
    
    onload: function(frm) {
        // Set filter when form loads
        set_sales_order_filter(frm);
        frm.set_df_property('custom_work_order_line_items', 'cannot_add_rows', true);
        frm.set_df_property('custom_work_order_line_items', 'cannot_delete_rows', true);
    },

    custom_sales_orders(frm) {
        frm.trigger('sync_work_order_line_items');
    },

    custom_work_order_line_items: function(frm){
        recalculate_total_qty(frm);
    },
    sync_work_order_line_items(frm) {
        const selected_sales_orders = frm.doc.custom_sales_orders.map(row => row.sales_order);
        if (!selected_sales_orders.length || !frm.doc.production_item)
        {
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
                // Add new ones
                so_items.forEach(item => {
                    console.log("In loop");
                    console.log(item);
                    if (!existing_so_item_ids.includes(item.name)) {
                        console.log("Doenst exists and adding new row")
                        let child = frm.add_child("custom_work_order_line_items");
                        child.sales_order_item = item.name;
                        child.line_item_no = item.custom_lineitem;
                        child.size = item.custom_size;
                        child.qty = item.qty;
                        child.already_allocated_qty = item.custom_allocated_qty_for_work_order;
                        child.pending_qty = item.custom_pending_qty_for_work_order;
                        child.work_order_allocated_qty = 1.0;
                        child.sales_order =  item.parent;
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
    }
});