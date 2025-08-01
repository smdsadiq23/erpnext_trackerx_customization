frappe.ui.form.on('Sales Order', {

  
});


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
