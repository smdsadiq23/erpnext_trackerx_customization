frappe.ui.form.on('Work Order', {
  onload: function(frm) {
    
    frm.sales_order_before_production_item = null;
    frm.production_item_before = null;

    if (!frm.doc.sales_order) {
      frm.set_query('production_item', () => {
        return {
          filters: [['Item', 'name', '=', '__none__']]
        };
      });
    }

    frm.fields_dict.production_item.$wrapper
      .find('input[data-fieldname="production_item"]')
      .on('click', function () {
        frm.sales_order_before_production_item = frm.doc.sales_order;
        if (!frm.doc.sales_order) {
          frappe.msgprint(__('Please select a Sales Order first.'));
        }
      });

    frm.set_df_property('custom_work_order_line_items', 'cannot_add_rows', true);
    frm.set_df_property('custom_work_order_line_items', 'cannot_delete_rows', true);
  },

  refresh: function(frm) {
    if (!frm.doc.sales_order) {
      //frm.set_value('production_item', null);
    }
    frm.is_user_selecting_production_item = false;
  },

  sales_order: function(frm) {
    frm.prev_sales_order = frm.doc.sales_order;

    if (!frm.doc.sales_order) {
      //frm.set_value('production_item', null);
      frm.set_query('production_item', () => {
        return {
          filters: [['Item', 'name', '=', '__none__']]
        };
      });
      return;
    }

    frappe.call({
      method: 'frappe.client.get',
      args: {
        doctype: 'Sales Order',
        name: frm.doc.sales_order
      },
      callback: function(r) {
        if (r.message) {
          const item_codes = (r.message.items || []).map(row => row.item_code);

          frm.set_query('production_item', () => {
            return {
              filters: [['Item', 'item_code', 'in', item_codes]]
            };
          });

          //frm.set_value('production_item', null);
          frm.clear_table('custom_work_order_line_items');

          r.message.items.forEach(item => {
            const child = frm.add_child('custom_work_order_line_items');
            child.line_item_no = item.custom_lineitem;
            child.size = item.custom_size;
            child.qty = item.qty;
            child.pending_qty = item.custom_pending_qty_for_work_order;

            frappe.call({
              method: "frappe.client.get_list",
              args: {
                doctype: "Work Order",
                filters: {
                  sales_order: frm.doc.sales_order
                },
                fields: ["name", "custom_work_order_line_items"]
              },
              callback: function(res) {
                let total_allocated = 0;
                if (res.message) {
                  res.message.forEach(wo => {
                    (wo.custom_work_order_line_items || []).forEach(line => {
                      if (
                        line.line_item_no === item.custom_lineitem &&
                        line.size === item.custom_size
                      ) {
                        total_allocated += flt(line.work_order_allocated_qty);
                      }
                    });
                  });
                }
                child.already_allocated_qty = total_allocated;
                frm.refresh_field('custom_work_order_line_items');
              }
            });
          });

          frm.refresh_field('custom_work_order_line_items');
        }
      }
    });
  },

  production_item: function(frm) {
    if (!frm.doc.sales_order && frm.is_user_selecting_production_item) {
      frappe.msgprint(__('Please select a Sales Order first.'));
      //frm.set_value('production_item', null);
    }

    if(frm.doc.production_item)
    {
        frm.production_item_before = frm.doc.production_item;
    }

    //frm.is_user_selecting_production_item = false;
    

    setTimeout(() => {
      if (!frm.doc.sales_order && frm.sales_order_before_production_item) {
        
            frm.set_value('sales_order', frm.sales_order_before_production_item);
       
      }
      frm.sales_order_before_production_item = null;
    }, 300); //
  }
});

frappe.ui.form.on('Work Order', {
  production_item_on_form_rendered: function(frm) {
    frm.is_user_selecting_production_item = false;
  }
});

frappe.ui.form.on('Work Order', {
  production_item_focus: function(frm) {
    frm.is_user_selecting_production_item = true;
  }
});
