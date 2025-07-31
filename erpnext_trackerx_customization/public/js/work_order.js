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

    update_line_item_allocations(frm);
  },

  work_order_allocated_qty: function(frm) {
    update_total_allocated_qty(frm);
  },

sales_order: function (frm) {
  frm.prev_sales_order = frm.doc.sales_order;

  if (!frm.doc.sales_order) {
    frm.set_query("production_item", () => ({
      filters: [["Item", "name", "=", "__none__"]],
    }));
    return;
  }

  // Step 1: Fetch Sales Order
  frappe.call({
    method: "frappe.client.get",
    args: {
      doctype: "Sales Order",
      name: frm.doc.sales_order,
    },
    callback: function (r) {
      if (!r.message) return;

      const sales_order_data = r.message;
      const item_codes = sales_order_data.items.map(row => row.item_code);

      // Step 2: Set allowed production items based on SO
      frm.set_query("production_item", () => ({
        filters: [["Item", "item_code", "in", item_codes]],
      }));

      // Step 3: Populate custom_work_order_line_items
      frm.clear_table("custom_work_order_line_items");

      (sales_order_data.items || []).forEach(item => {
        const child = frm.add_child("custom_work_order_line_items");
        child.line_item_no = item.custom_lineitem;
        child.size = item.custom_size;
        child.qty = item.qty;
        child.pending_qty = item.custom_pending_qty_for_work_order;
        child.already_allocated_qty = item.custom_allocated_qty_for_work_order;
      });

      frm.refresh_field("custom_work_order_line_items");
    },
  });
},


  custom_work_order_line_items_on_form_rendered: function(frm) {
    // Update again when child table is rendered
    update_line_item_allocations(frm);
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

function update_total_allocated_qty(frm) {
  let total = 0;
  (frm.doc.custom_work_order_line_items || []).forEach(row => {
    total += flt(row.work_order_allocated_qty || 0);
  });
  frm.set_value('qty', total);
}


function update_line_item_allocations(frm) {
  if (!frm.doc.sales_order) return;

  frappe.call({
    method: "frappe.client.get",
    args: {
      doctype: "Sales Order",
      name: frm.doc.sales_order
    },
    callback: function(r) {
      const sales_order_items = r.message.items || [];

      frm.doc.custom_work_order_line_items.forEach(child => {
        const matching_item = sales_order_items.find(item =>
          item.custom_lineitem === child.line_item_no &&
          item.custom_size === child.size
        );
        if (matching_item) {
          frappe.model.set_value(child.doctype, child.name, 'already_allocated_qty', matching_item.custom_allocated_qty_for_work_order);
          frappe.model.set_value(child.doctype, child.name, 'pending_qty', matching_item.custom_pending_qty_for_work_order);
        }
      });
    }
  });
}