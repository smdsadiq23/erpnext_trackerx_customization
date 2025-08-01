// frappe.ui.form.on('Work Order', {
//     onload(frm) {
//         console.log('onload');
//         frm.sales_order_item_map = {};
//         frm.set_df_property('custom_work_order_line_items', 'cannot_add_rows', true);
//         frm.set_df_property('custom_work_order_line_items', 'cannot_delete_rows', true);
//     },

//     production_item(frm) {
//         // Set filter on sales orders
//         console.log('production_item');
//         if (frm.doc.production_item) {
//             frappe.after_ajax(() => {
//                 console.log('after_ajax');
//                 console.log(frm.fields_dict.custom_sales_orders);
//                 console.log(frm.fields_dict.custom_sales_orders.grid);
//                 console.log(frm.fields_dict.custom_sales_orders.grid.get_field("sales_order"));
//                 if (frm.fields_dict.custom_sales_orders && frm.fields_dict.custom_sales_orders.grid) {
//                     frm.fields_dict.custom_sales_orders.grid.get_field("sales_order").get_query = () => ({
//                         query: "frappe.desk.search.search_link",
//                         filters: {
//                             doctype: "Sales Order",
//                             item_code: frm.doc.production_item
//                         }
//                     });
//                 }
//             });
//         }
//     },


//     custom_sales_orders_on_form_rendered(frm) {
//         console.log('custom_sales_orders_on_form_rendered');
//         setup_sales_order_sync(frm);
//     }
// });

// frappe.ui.form.on('Work Order Sales Orders', {
//     sales_order: function (frm) {
//         console.log('sales_order');
//         setup_sales_order_sync(frm);
//     }
// });

// function setup_sales_order_sync(frm) {
//     console.log('setup_sales_order_sync');
//     const selected_sos = (frm.doc.custom_sales_orders || []).map(row => row.sales_order);

//     // Load all Sales Orders' item data
//     frappe.call({
//         method: "frappe.client.get_list",
//         args: {
//             doctype: "Sales Order",
//             filters: {
//                 name: ["in", selected_sos]
//             },
//             fields: ["name"],
//             limit_page_length: 1000
//         },
//         callback: function (res) {
//             if (!res.message) return;

//             // Get all SO Items
//             frappe.call({
//                 method: "frappe.client.get_list",
//                 args: {
//                     doctype: "Sales Order Item",
//                     filters: {
//                         parent: ["in", selected_sos],
//                         item_code: frm.doc.production_item
//                     },
//                     fields: [
//                         "name", "parent", "item_code", "custom_lineitem", "custom_size",
//                         "qty", "custom_allocated_qty_for_work_order",
//                         "custom_pending_qty_for_work_order"
//                     ],
//                     limit_page_length: 1000
//                 },
//                 callback: function (res2) {
//                     const so_items = res2.message || [];
//                     const existing_so_item_names = frm.doc.custom_work_order_line_items.map(i => i.sales_order_item);

//                     const new_items = [];

//                     for (const item of so_items) {
//                         if (existing_so_item_names.includes(item.name)) continue;

//                         const child = frm.add_child("custom_work_order_line_items");
//                         child.sales_order_item = item.name;
//                         child.line_item_no = item.custom_lineitem;
//                         child.size = item.custom_size;
//                         child.qty = item.qty;
//                         child.already_allocated_qty = item.custom_allocated_qty_for_work_order;
//                         child.pending_qty = item.custom_pending_qty_for_work_order;
//                         child.work_order_allocated_qty = 1.0;

//                         new_items.push(child);
//                     }

//                     frm.refresh_field("custom_work_order_line_items");
//                 }
//             });
//         }
//     });
// }

// // Remove Work Order Line Items if Sales Order deselected
// frappe.ui.form.on('Work Order Sales Orders', {
//     custom_sales_orders_remove: function (frm) {
//         console.log('custom_sales_orders_remove');
//         const selected_so_names = (frm.doc.custom_sales_orders || []).map(row => row.sales_order);

//         const to_remove = frm.doc.custom_work_order_line_items.filter(row =>
//             !selected_so_names.includes(get_sales_order_from_item(row.sales_order_item))
//         );

//         to_remove.forEach(row => {
//             const idx = frm.doc.custom_work_order_line_items.findIndex(r => r.name === row.name);
//             if (idx !== -1) frm.doc.custom_work_order_line_items.splice(idx, 1);
//         });

//         frm.refresh_field("custom_work_order_line_items");
//     }
// });

// function get_sales_order_from_item(sales_order_item) {
//     console.log('get_sales_order_from_item');
//     // sales_order_item is in format SO-0001-1, so parent is SO-0001
//     return sales_order_item?.split("-").slice(0, -1).join("-");
// }
