// Purchase Order Client Script
// File: erpnext_trackerx_customization/public/js/purchase_order.js

frappe.ui.form.on("Purchase Order", {
  refresh: function (frm) {
    // Remove existing Material Request get_items button
    setInterval(function () {
      frm.remove_custom_button("Material Request", "Get Items From");
    }, 300);    
    frm.remove_custom_button("Material Request", "Get Items From");

    // Add "Sales Order" option
    frm.add_custom_button(
        "Sales Order",
        function () {
            let dialog = new frappe.ui.Dialog({
                title: "Select Sales Order",
                fields: [
                    {
                        fieldname: "sales_order",
                        fieldtype: "Link",
                        label: "Sales Order",
                        options: "Sales Order",
                        reqd: 1,
                        get_query: function () {
                            return {
                                filters: {
                                    docstatus: 1, // Only submitted documents
                                    status: ["!=", "Closed"]
                                }
                            };
                        }
                    }
                ],
                primary_action_label: "Get Items",
                primary_action: function () {
                    let values = dialog.get_values();
                    if (values) {
                        get_items_from_sales_order(frm, values);
                        dialog.hide();
                    }
                }
            });
            dialog.show();
        },
        "Get Items From"
    );

    // Add custom get items button for Material Requirement Plan
    frm.add_custom_button(
      "Material Requirement Plan",
      function () {
        // Open dialog to select Material Requirement Plan
        let dialog = new frappe.ui.Dialog({
          title: "Select Material Requirement Plan",
          fields: [
            {
              fieldname: "material_requirement_plan",
              fieldtype: "Link",
              label: "Material Requirement Plan",
              options: "Material Requirement Plan",
              reqd: 1,
              get_query: function () {
                return {
                  filters: {
                    docstatus: 1, // Only submitted documents
                    status: ["!=", "Stopped"],
                  },
                };
              },
            },
          ],
          primary_action_label: "Get Items",
          primary_action: function () {
            let values = dialog.get_values();
            if (values) {
              get_items_from_material_requirement_plan(frm, values);
              dialog.hide();
            }
          },
        });
        dialog.show();
      },
      "Get Items From"
    );

    // // Add custom button to create Goods Receipt Note
    // frm.add_custom_button(
    //   "Goods Receipt Note",
    //   function () {
    //     create_goods_receipt_note(frm);
    //   },
    //   "Create"
    // );    
    
    // Add button only if PO is submitted and not fully received
    if (frm.doc.docstatus === 1 && frm.doc.per_received < 100) {
      frm.add_custom_button(
        "Goods Receipt Note",
        function () {
          create_goods_receipt_note(frm);
        },
        "Create"
      );
    }
  },

  supplier: function (frm) {
    // // Clear filter if no supplier selected
    // if (!frm.doc.supplier) {
    //     frm.set_query('item_code', 'items', function() {
    //         return {};
    //     });
    //     return;
    // }

    // // Set filter on item_code in child table
    // frm.set_query('item_code', 'items', function() {
    //     return {
    //         filters: {
    //             custom_preferred_supplier: frm.doc.supplier
    //         }
    //     };
    // });

    frm.doc.items.forEach((row) => {
      cur_frm.script_manager.trigger(
        "update_rate_from_bom",
        "Purchase Order Item",
        row.name
      );
    });
  },

  custom_order_method: function (frm) {
    frm.doc.items.forEach((row) => {
      cur_frm.script_manager.trigger(
        "update_rate_from_bom",
        "Purchase Order Item",
        row.name
      );
    });
  },
});

frappe.ui.form.on("Purchase Order Item", {
  item_code: function (frm, cdt, cdn) {
    if (!cdn) {
      console.warn("Invalid row reference");
      return;
    }

    const row = locals[cdt][cdn];
    // If no item_code, clear global options on the child field and exit
    if (!row || !row.item_code) {
      frm.fields_dict["items"].grid.update_docfield_property(
        "custom_sfg_code",
        "options",
        ""
      );
      return;
    }

    // Show loading in the Select options (applies to all rows)
    frm.fields_dict["items"].grid.update_docfield_property(
      "custom_sfg_code",
      "options",
      "Loading..."
    );

    frappe.call({
      method:
        "erpnext_trackerx_customization.api.purchase_order.get_fg_components_by_item",
      args: { item_code: row.item_code },
      callback: function (r) {
        if (r.exc) {
          frappe.msgprint(__("Error loading components."));
          frm.fields_dict["items"].grid.update_docfield_property(
            "custom_sfg_code",
            "options",
            ""
          );
          return;
        }

        const list = r.message || [];
        const options = list.join("\n"); // Select expects newline-separated options

        frm.fields_dict["items"].grid.update_docfield_property(
          "custom_sfg_code",
          "options",
          options
        );

        // If current value no longer valid, clear it for THIS row
        if (row.custom_sfg_code && !list.includes(row.custom_sfg_code)) {
          frappe.model.set_value(cdt, cdn, "custom_sfg_code", "");
        }

        // Refresh the grid field so the new options show up in the UI
        frm.refresh_field("items");
      },
    });

    // Trigger rate update when item changes
    cur_frm.script_manager.trigger("update_rate_from_bom", cdt, cdn);
  },

  update_rate_from_bom: function (frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    if (!row) {
      console.error("❌ Row not found for cdn:", cdn);
      return;
    }

    if (!row.item_code || !frm.doc.supplier || !frm.doc.custom_order_method) {
      console.warn("⚠️ Missing required fields — skipping rate update");
      return;
    }

    frappe.call({
      method:
        "erpnext_trackerx_customization.api.purchase_order.get_rate_from_bom_by_order_method",
      args: {
        item_code: row.item_code,
        supplier: frm.doc.supplier,
        order_method: frm.doc.custom_order_method,
      },
      callback: function (r) {
        if (r.message && r.message.rate !== undefined) {
          // Delay to avoid Frappe's internal reset
          setTimeout(() => {
            // Update data model
            frappe.model.set_value(cdt, cdn, "rate", r.message.rate);
            console.log(
              "✅ Rate set in data model. New value:",
              locals[cdt][cdn].rate
            );

            // Force UI update
            const grid_row =
              frm.fields_dict.items.grid.grid_rows_by_docname[cdn];
            if (grid_row) {
              grid_row.refresh_field("rate");
              grid_row.refresh_field("amount");
            }

            // Direct DOM update
            // const $input = $(`[data-fieldname="rate"][data-name="${cdn}"]`);
            // if ($input.length) {
            //     const formatted = format_currency(r.message.rate, frm.doc.currency);
            //     $input.val(formatted);
            //     $input.trigger('change');
            //     console.log("✅ DOM input forced to:", formatted);
            // }

            frm.refresh_field("items");
            frm.dirty();

            frappe.show_alert({
              message: __("Rate updated from BOM: ₹" + r.message.rate),
              indicator: "green",
            });

            setTimeout(() => {
              console.log("🏁 Final rate value:", locals[cdt][cdn].rate);
            }, 300);
          }, 500);
        } else {
          console.log("📭 No rate returned from server");
        }
      },
    });
  },
});

function get_items_from_material_requirement_plan(frm, values) {
  frappe.call({
    method:
      "erpnext_trackerx_customization.api.purchase_order.get_items_from_material_requirement_plan",
    args: {
      material_requirement_plan: values.material_requirement_plan,
      source_table: values.source_table,
      purchase_order: frm.doc.name,
    },
    callback: function (r) {
      if (r.message) {
        // Clear existing items
        frm.clear_table("items");

        // Add new items
        r.message.forEach(function (item) {
          let row = frm.add_child("items");
          Object.assign(row, item);
        });

        // Refresh the items table
        frm.refresh_field("items");
        // frm.save();

        frappe.msgprint("Items added successfully");
      }
    },
  });
}

function create_goods_receipt_note(frm) {
  // Check if PO is submitted
  if (frm.doc.docstatus !== 1) {
    frappe.msgprint(__("Please submit the Purchase Order first"));
    return;
  }

  // Check if already fully received
  if (frm.doc.per_received >= 100) {
    frappe.msgprint(__("Purchase Order is already fully received"));
    return;
  }

  // Create new Goods Receipt Note
  frappe.model.open_mapped_doc({
    method:
      "erpnext_trackerx_customization.api.purchase_order.make_goods_receipt_note",
    frm: frm,
    run_link_triggers: true,
  });
}

// Alternative implementation if the mapped doc approach doesn't work
function create_goods_receipt_note_alternative(frm) {
  // Check if PO is submitted
  if (frm.doc.docstatus !== 1) {
    frappe.msgprint(__("Please submit the Purchase Order first"));
    return;
  }

  // Check if already fully received
  if (frm.doc.per_received >= 100) {
    frappe.msgprint(__("Purchase Order is already fully received"));
    return;
  }

  // Create new Goods Receipt Note
  frappe.call({
    method:
      "erpnext_trackerx_customization.api.purchase_order.make_goods_receipt_note",
    args: {
      source_name: frm.doc.name,
    },
    callback: function (r) {
      if (r.message) {
        frappe.set_route("Form", "Goods Receipt Note", r.message);
      }
    },
  });
}

function get_items_from_sales_order(frm, values) {
    frappe.call({
        method: 'erpnext_trackerx_customization.api.purchase_order.get_items_from_sales_order',
        args: {
            sales_order: values.sales_order
        },
        callback: function(r) {
            if (r.message) {
                frm.clear_table('items');
                                
                r.message.forEach(function(item) {
                    let row = frm.add_child('items');
                    Object.assign(row, item);
                    
                    // Trigger item_code handler to populate custom_sfg_code
                    setTimeout(() => {
                        cur_frm.script_manager.trigger(
                            'item_code', 
                            'Purchase Order Item', 
                            row.name
                        );
                        
                        // Also trigger rate update
                        cur_frm.script_manager.trigger(
                            'update_rate_from_bom', 
                            'Purchase Order Item', 
                            row.name
                        );
                    }, 100);
                });
                                
                frm.refresh_field('items');
                frappe.msgprint('Items added successfully from Sales Order');
            }
        }
    });
}