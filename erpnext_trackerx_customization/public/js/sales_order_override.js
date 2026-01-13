(function trackerx_patch_update_child_items() {
  function patch() {
    if (!window.erpnext?.utils?.update_child_items) {
      return setTimeout(patch, 300);
    }
    if (erpnext.utils.__trackerx_update_child_items_patched) return;

    const original = erpnext.utils.update_child_items;

    erpnext.utils.update_child_items = function (opts) {
      const frm = opts?.frm;

      // Patch ONLY Sales Order -> items popup
      if (frm?.doc?.doctype === "Sales Order" && (opts.child_docname || "items") === "items") {
        return trackerx_update_child_items_with_size(opts);
      }

      return original(opts);
    };

    erpnext.utils.__trackerx_update_child_items_patched = true;
  }

  patch();

  function trackerx_update_child_items_with_size(opts) {
    const frm = opts.frm;

    const cannot_add_row = typeof opts.cannot_add_row === "undefined" ? true : opts.cannot_add_row;

    const child_docname = typeof opts.child_docname === "undefined" ? "items" : opts.child_docname;

    const child_meta = frappe.get_meta(`${frm.doc.doctype} Item`);
    const has_reserved_stock = opts.has_reserved_stock ? true : false;

    const get_precision = (fieldname) => {
      const f = child_meta.fields.find((f) => f.fieldname == fieldname);
      return f?.precision;
    };

    // ✅ Function to calculate qty based on order_qty and tolerance_percentage
    function calculate_qty(field) {
      const docname = field.doc.docname;
      const grid = dialog.fields_dict.trans_items;
      const row = grid.df.data.find((doc) => doc.docname == docname);
      
      if (row && row.custom_order_qty) {
        const order_qty = flt(row.custom_order_qty);
        const tolerance = flt(row.custom_tolerance_percentage) || 0;
        
        // Calculate: qty = order_qty * (1 + tolerance/100)
        row.qty = order_qty * (1 + tolerance / 100);
        
        grid.grid.refresh();
      }
    }

    // include custom fields in row data
    this.data = frm.doc[child_docname].map((d) => {
      return {
        docname: d.name,
        name: d.name,
        item_code: d.item_code,
        custom_size: d.custom_size,
        delivery_date: d.delivery_date,
        schedule_date: d.schedule_date,
        conversion_factor: d.conversion_factor,
        
        // ✅ Add new custom fields
        custom_order_qty: d.custom_order_qty || 0,
        custom_tolerance_percentage: d.custom_tolerance_percentage || 0,
        
        qty: d.qty,
        rate: d.rate,
        uom: d.uom,
        fg_item: d.fg_item,
        fg_item_qty: d.fg_item_qty,
      };
    });

    const fields = [
      { 
        fieldtype: "Data", 
        fieldname: "docname", 
        read_only: 1, 
        hidden: 1 
      },

      {
        fieldtype: "Link",
        fieldname: "item_code",
        options: "Item",
        in_list_view: 1,
        read_only: 0,
        disabled: 0,
        label: __("Item Code"),
        columns: 2, // ✅ Control column width
        get_query: function () {
          let filters;
          if (frm.doc.doctype == "Sales Order") {
            filters = { is_sales_item: 1 };
          } else if (frm.doc.doctype == "Purchase Order") {
            if (frm.doc.is_subcontracted) {
              if (frm.doc.is_old_subcontracting_flow) {
                filters = { is_sub_contracted_item: 1 };
              } else {
                filters = { is_stock_item: 0 };
              }
            } else {
              filters = { is_purchase_item: 1 };
            }
          }
          return { query: "erpnext.controllers.queries.item_query", filters };
        },
        onchange: function () {
          const me = this;

          frm.call({
            method: "erpnext.stock.get_item_details.get_item_details",
            args: {
              doc: frm.doc,
              args: {
                item_code: this.value,
                set_warehouse: frm.doc.set_warehouse,
                customer: frm.doc.customer || frm.doc.party_name,
                quotation_to: frm.doc.quotation_to,
                supplier: frm.doc.supplier,
                currency: frm.doc.currency,
                is_internal_supplier: frm.doc.is_internal_supplier,
                is_internal_customer: frm.doc.is_internal_customer,
                conversion_rate: frm.doc.conversion_rate,
                price_list: frm.doc.selling_price_list || frm.doc.buying_price_list,
                price_list_currency: frm.doc.price_list_currency,
                plc_conversion_rate: frm.doc.plc_conversion_rate,
                company: frm.doc.company,
                order_type: frm.doc.order_type,
                is_pos: cint(frm.doc.is_pos),
                is_return: cint(frm.doc.is_return),
                is_subcontracted: frm.doc.is_subcontracted,
                ignore_pricing_rule: frm.doc.ignore_pricing_rule,
                doctype: frm.doc.doctype,
                name: frm.doc.name,
                qty: me.doc.qty || 1,
                uom: me.doc.uom,
                pos_profile: cint(frm.doc.is_pos) ? frm.doc.pos_profile : "",
                tax_category: frm.doc.tax_category,
                child_doctype: frm.doc.doctype + " Item",
                is_old_subcontracting_flow: frm.doc.is_old_subcontracting_flow,
              },
            },
            callback: function (r) {
              if (r.message) {
                const { qty, price_list_rate: rate, uom, conversion_factor, bom_no } = r.message;

                const row = dialog.fields_dict.trans_items.df.data.find(
                  (doc) => doc.idx == me.doc.idx
                );
                if (row) {
                  Object.assign(row, {
                    conversion_factor: me.doc.conversion_factor || conversion_factor,
                    uom: me.doc.uom || uom,
                    qty: me.doc.qty || qty,
                    rate: me.doc.rate || rate,
                    bom_no: bom_no,
                  });
                  dialog.fields_dict.trans_items.grid.refresh();
                }
              }
            },
          });
        },
      },

      // Read-only Size column
      {
        fieldtype: "Data",
        fieldname: "custom_size",
        label: __("Size"),
        in_list_view: 1,
        read_only: 1,
        columns: 1, // ✅ Smaller column
      },

      {
        fieldtype: "Link",
        fieldname: "uom",
        options: "UOM",
        read_only: 0,
        in_list_view: 1,
        label: __("UOM"),
        reqd: 1,
        columns: 1, // ✅ Smaller column
        onchange: function () {
          frappe.call({
            method: "erpnext.stock.get_item_details.get_conversion_factor",
            args: { item_code: this.doc.item_code, uom: this.value },
            callback: (r) => {
              if (!r.exc) {
                if (this.doc.conversion_factor == r.message.conversion_factor) return;

                const docname = this.doc.docname;
                dialog.fields_dict.trans_items.df.data.some((doc) => {
                  if (doc.docname == docname) {
                    doc.conversion_factor = r.message.conversion_factor;
                    dialog.fields_dict.trans_items.grid.refresh();
                    return true;
                  }
                });
              }
            },
          });
        },
      },
      
      // ✅ Add custom_order_qty field (editable, visible in grid)
      {
        fieldtype: "Float",
        fieldname: "custom_order_qty",
        default: 0,
        read_only: 0,
        in_list_view: 1,
        label: __("Order Qty"),
        columns: 1, // ✅ Control width
        precision: get_precision("custom_order_qty") || 2,
        onchange: function () {
          calculate_qty(this);
        },
      },
      
      // ✅ Add custom_tolerance_percentage field (editable, visible in grid)
      {
        fieldtype: "Percent",
        fieldname: "custom_tolerance_percentage",
        default: 0,
        read_only: 0,
        in_list_view: 1,
        label: __("Tolerance %"),
        columns: 1, // ✅ Control width
        precision: get_precision("custom_tolerance_percentage") || 2,
        onchange: function () {
          calculate_qty(this);
        },
      },
      
      {
        fieldtype: "Float",
        fieldname: "qty",
        default: 0,
        read_only: 0,
        in_list_view: 1,
        label: __("Qty"),
        columns: 1, // ✅ Control width
        precision: get_precision("qty"),
      },
      
      {
        fieldtype: "Currency",
        fieldname: "rate",
        options: "currency",
        default: 0,
        read_only: 0,
        in_list_view: 1,
        label: __("Rate"),
        columns: 1, // ✅ Control width
        precision: get_precision("rate"),
      },
    ];

    // Insert Sales Order specific fields at the right position
    if (frm.doc.doctype == "Sales Order" || frm.doc.doctype == "Purchase Order") {
      // Insert delivery_date/schedule_date after item_code (position 2)
      fields.splice(2, 0, {
        fieldtype: "Date",
        fieldname: frm.doc.doctype == "Sales Order" ? "delivery_date" : "schedule_date",
        in_list_view: 1,
        columns: 1, // ✅ Control width
        label: frm.doc.doctype == "Sales Order" ? __("Delivery Date") : __("Reqd by date"),
        reqd: 1,
      });
      
      // Insert conversion_factor after delivery_date (position 3) - HIDE from grid
      fields.splice(3, 0, {
        fieldtype: "Float",
        fieldname: "conversion_factor",
        label: __("Conversion Factor"),
        in_list_view: 0, // ✅ Hide from grid to save space
        columns: 1,
        precision: get_precision("conversion_factor"),
      });
    }

    let dialog = new frappe.ui.Dialog({
      title: __("Update Items"),
      size: "extra-large",
      fields: [
        {
          fieldname: "trans_items",
          fieldtype: "Table",
          label: "Items",
          cannot_add_rows: cannot_add_row,
          in_place_edit: true, // ✅ Enable in-place editing
          reqd: 1,
          data: this.data,
          get_data: () => this.data,
          fields: fields,
        },
      ],
      primary_action: function () {
        if (frm.doctype == "Sales Order" && has_reserved_stock) {
          this.hide();
          frappe.confirm(
            __(
              "The reserved stock will be released when you update items. Are you certain you wish to proceed?"
            ),
            () => this.update_items()
          );
        } else {
          this.update_items();
        }
      },
      update_items: function () {
        const trans_items = this.get_values()["trans_items"].filter((item) => !!item.item_code);
        
        frappe.call({
          method: "erpnext.controllers.accounts_controller.update_child_qty_rate",
          freeze: true,
          args: {
            parent_doctype: frm.doc.doctype,
            trans_items: trans_items,
            parent_doctype_name: frm.doc.name,
            child_docname: child_docname,
          },
          callback: function (r) {
            if (!r.exc) {
              // ✅ Update custom fields in a single batch operation
              frappe.call({
                method: "frappe.client.get",
                args: {
                  doctype: frm.doc.doctype,
                  name: frm.doc.name
                },
                callback: function(doc_response) {
                  if (doc_response.message) {
                    let doc = doc_response.message;
                    
                    // Update custom fields in the fetched document
                    trans_items.forEach(item => {
                      let child_row = doc[child_docname].find(row => row.name === item.docname);
                      if (child_row) {
                        child_row.custom_order_qty = item.custom_order_qty || 0;
                        child_row.custom_tolerance_percentage = item.custom_tolerance_percentage || 0;
                      }
                    });
                    
                    // Save the document with updated custom fields
                    frappe.call({
                      method: "frappe.client.save",
                      args: {
                        doc: doc
                      },
                      callback: function() {
                        frm.reload_doc();
                      }
                    });
                  } else {
                    frm.reload_doc();
                  }
                }
              });
            } else {
              frm.reload_doc();
            }
          },
        });
        this.hide();
        refresh_field("items");
      },
      primary_action_label: __("Update"),
    });

    dialog.show();
  }
})();