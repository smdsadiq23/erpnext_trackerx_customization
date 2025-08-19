frappe.ui.form.on('Trims Order', {

    refresh(frm) {

        // Now re-add your own custom button
        if (frm.doc.docstatus === 1 && frm.doc.status !== "Closed") {
        frm.add_custom_button(__('Pick List'), () => {
            create_pick_list(frm);
        }, __('Create'));
        }
    }
  
});

function genereate_key(so, size)
{
    return so + "___" + size;
}

function create_pick_list(frm)
{


    
    const trims_order_qty_dict = {}

    frm.doc.table_trims_order_summary.forEach(element => {
       key = genereate_key(element.sales_order, element.size);
       trims_order_qty_dict[key] = element.trims_order_quantity;
    });

    frappe.call({
        method: 'frappe.client.insert',
        args: {
            doc: {
                doctype: 'Pick List',
                company: frm.doc.company,
                purpose: 'Material Transfer for Manufacture',
                custom_trims_order: frm.doc.name,
                locations: frm.doc.table_trims_order_details.filter(i => i.required_quantity > 0).map(i => ({
                    line_item_no: i.line_item_no,
                    custom_size: i.size,
                    sales_order: i.sales_order,
                    item_code: i.item_code,
                    uom: i.uom,
                    per_unit_quantity: i.per_unit_quantity,
                    line_item_no: i.wo_quantity,
                    wo_quantity: i.already_issued_quantity,
                    qty: i.required_quantity,
                    required_quantity: i.required_quantity,
                    custom_trims_order_qty: trims_order_qty_dict[genereate_key(i.sales_order, i.size)] //i.trims_order_quantity
                })),
            }
        },
        callback(r) {
            if (r.message) {
                frappe.set_route('Form', 'Pick List', r.message.name);
                frappe.show_alert({
                    message: `Pick List ${r.message.name} created successfully`,
                    indicator: 'green'
                });
            }
        },
        error(r) {
            frappe.msgprint({
                title: 'Error',
                message: r.message || 'An error occurred while creating the Pick List',
                indicator: 'red'
            });
        }
    });
}