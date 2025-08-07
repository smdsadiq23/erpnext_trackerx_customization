frappe.ui.form.on('Sales Order', {

    refresh(frm) {
        // Wait for default buttons to load, then remove Work Order
        // frm.page.clear_primary_action();
        // frm.page.clear_actions();

        // setTimeout(() => {
        //   frm.remove_custom_button('Work Order', 'Create');
        // }, 1000); 
        
        // Now re-add your own custom button
        if (frm.doc.docstatus === 1 && frm.doc.status !== "Closed") {
        frm.add_custom_button(__('Create Work Order'), () => {
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
      }
    ],
    primary_action_label: 'Create Work Order(s)',
    primary_action(values) {
      const selected_items = dialog.fields_dict.items_table.grid.get_selected_children();
      if (selected_items.length === 0) {
        frappe.throw('Please select at least one line item to create a work order');
      }

      frappe.throw('This enhancement is under development, Till then please go to work order doctype and create it manually.');
      const mode = values.creation_mode;
      if (mode === 'Single Work Order for All') {
        create_single_work_order(frm, selected_items);
      } else if (mode === 'Separate Work Order per Line Item') {
        create_work_orders_by_line_item(frm, selected_items);
      } else if (mode === 'Separate Work Order per Size') {
        create_work_orders_by_size(frm, selected_items);
      }

      dialog.hide();
    }
  });

  dialog.show();
}

function create_single_work_order(frm, items) {

    total_qty = 1;
  for (let item of items) {
    total_qty = total_qty += item.qty;
  }
  frappe.call({
    method: 'frappe.client.insert',
    args: {
      doc: {
        doctype: 'Work Order',
        production_item: items[0],
        company: frm.doc.company,
        sales_order: frm.doc.name,
        sales_orders: [{
            sales_order: frm.doc.name,
        }],
        required_items: items.map(i => ({
          item_code: i.item_code,
          required_qty: i.qty,
          sales_order: frm.doc.name,
          sales_order_item: i.so_detail,
          custom_size: i.custom_size,
          custom_lineitem: i.custom_lineitem
        })),
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
      }
    }
  });
}

function create_work_orders_by_line_item(frm, items) {
  items.forEach(item => {
    frappe.call({
      method: 'frappe.client.insert',
      args: {
        doc: {
          doctype: 'Work Order',
          production_item: item.item_code,
          company: frm.doc.company,
          qty: item.qty,
          sales_order: frm.doc.name,
          sales_order_item: item.so_detail,
          custom_size: item.custom_size,
          custom_lineitem: item.custom_lineitem
        }
      },
      callback(r) {
        if (r.message) {
          frappe.msgprint(`Created Work Order: ${r.message.name}`);
        }
      }
    });
  });
}


function create_work_orders_by_size(frm, items) {
  const grouped_by_size = {};

  for (let item of items) {
    const key = `${item.item_code}||${item.custom_size}`;
    if (!grouped_by_size[key]) grouped_by_size[key] = [];
    grouped_by_size[key].push(item);
  }

  Object.values(grouped_by_size).forEach(group => {
    const first = group[0];

    frappe.call({
      method: 'frappe.client.insert',
      args: {
        doc: {
          doctype: 'Work Order',
          production_item: first.item_code,
          company: frm.doc.company,
          qty: group.reduce((sum, i) => sum + i.qty, 0),
          sales_order: frm.doc.name,
          items: group.map(i => ({
            item_code: i.item_code,
            qty: i.qty,
            sales_order: frm.doc.name,
            sales_order_item: i.so_detail,
            custom_size: i.custom_size,
            custom_lineitem: i.custom_lineitem
          }))
        }
      },
      callback(r) {
        if (r.message) {
          frappe.msgprint(`Created Work Order for Size ${first.custom_size}: ${r.message.name}`);
        }
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
