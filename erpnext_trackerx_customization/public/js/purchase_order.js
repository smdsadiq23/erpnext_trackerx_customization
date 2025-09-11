// Purchase Order Client Script
// File: erpnext_trackerx_customization/public/js/purchase_order.js

frappe.ui.form.on('Purchase Order', {
    onload: function(frm) {
        // Remove existing Material Request get_items button
        setInterval(function()  {
            frm.remove_custom_button(('Material Request'), ('Get Items From'));
        }, 300);
        frm.remove_custom_button(('Material Request'), ('Get Items From'));
                
        // Add custom get items button for Material Requirement Plan
        frm.add_custom_button(('Material Requirement Plan'), function() {
            // Open dialog to select Material Requirement Plan
            let dialog = new frappe.ui.Dialog({
                title: ('Select Material Requirement Plan'),
                fields: [
                    {
                        fieldname: 'material_requirement_plan',
                        fieldtype: 'Link',
                        label: ('Material Requirement Plan'),
                        options: 'Material Requirement Plan',
                        reqd: 1,
                        get_query: function() {
                            return {
                                filters: {
                                    'docstatus': 1,  // Only submitted documents
                                    'status': ['!=', 'Stopped']
                                }
                            };
                        }
                    }
                ],
                primary_action_label: ('Get Items'),
                primary_action: function() {
                    let values = dialog.get_values();
                    if (values) {
                        get_items_from_material_requirement_plan(frm, values);
                        dialog.hide();
                    }
                }
            });
            dialog.show();
        }, ('Get Items From'));
        
        // Add custom button to create Goods Receipt Note
        frm.add_custom_button(('Goods Receipt Note'), function() {
            create_goods_receipt_note(frm);
        }, ('Create'));
    },
    
    refresh: function(frm) {
        // Add button only if PO is submitted and not fully received
        if (frm.doc.docstatus === 1 && frm.doc.per_received < 100) {
            frm.add_custom_button(('Goods Receipt Note'), function() {
                create_goods_receipt_note(frm);
            }, ('Create'));
        }
    },

    custom_process_type: function(frm) {
        if (!frm.doc.custom_process_type) {
            // Clear filter if no process selected
            frm.set_query('supplier', function() {
                return {};
            });
            return;
        }

        // Show loading state
        frm.set_df_property('supplier', 'description', 'Loading suppliers...');
        frm.refresh_field('supplier');

        frappe.call({
            method: 'erpnext_trackerx_customization.api.purchase_order.get_suppliers_by_process_type',
            args: {
                process_type: frm.doc.custom_process_type
            },
            callback: function(r) {
                frm.set_df_property('supplier', 'description', '');
                if (r.exc) {
                    frappe.msgprint(__('Error loading suppliers.'));
                    frm.set_query('supplier', function() { return {}; });
                    return;
                }

                const suppliers = r.message || [];

                if (suppliers.length === 0) {
                    frappe.msgprint(__('No suppliers found for this process type.'));
                    frm.set_query('supplier', function() { return { filters: { name: ['in', []] } }; });
                    return;
                }

                // Set filter on supplier field
                frm.set_query('supplier', function() {
                    return {
                        filters: {
                            name: ['in', suppliers]
                        }
                    };
                });

                // If current supplier is not in list, clear it
                if (frm.doc.supplier && !suppliers.includes(frm.doc.supplier)) {
                    frm.set_value('supplier', '');
                }

                frm.refresh_field('supplier');
            }
        });
    },

    supplier: function(frm) {
        if (!frm.doc.supplier) {
            // Clear filter if no supplier selected
            frm.set_query('item_code', 'items', function() {
                return {};
            });
            return;
        }

        // Set filter on item_code in child table
        frm.set_query('item_code', 'items', function() {
            return {
                filters: {
                    custom_preferred_supplier: frm.doc.supplier
                }
            };
        });
    }    
});

frappe.ui.form.on('Purchase Order Item', {
  item_code: function (frm, cdt, cdn) {
    if (!cdn) {
      console.warn("Invalid row reference");
      return;
    }

    const row = locals[cdt][cdn];
    // If no item_code, clear global options on the child field and exit
    if (!row || !row.item_code) {
      frm.fields_dict['items'].grid.update_docfield_property(
        'custom_sfg_code',
        'options',
        ''
      );
      return;
    }

    // Show loading in the Select options (applies to all rows)
    frm.fields_dict['items'].grid.update_docfield_property(
      'custom_sfg_code',
      'options',
      'Loading...'
    );

    frappe.call({
      method: 'erpnext_trackerx_customization.api.purchase_order.get_fg_components_by_item',
      args: { item_code: row.item_code },
      callback: function (r) {
        if (r.exc) {
          frappe.msgprint(__('Error loading components.'));
          frm.fields_dict['items'].grid.update_docfield_property(
            'custom_sfg_code',
            'options',
            ''
          );
          return;
        }

        const list = r.message || [];
        const options = list.join('\n'); // Select expects newline-separated options

        frm.fields_dict['items'].grid.update_docfield_property(
          'custom_sfg_code',
          'options',
          options
        );

        // If current value no longer valid, clear it for THIS row
        if (row.custom_sfg_code && !list.includes(row.custom_sfg_code)) {
          frappe.model.set_value(cdt, cdn, 'custom_sfg_code', '');
        }

        // Refresh the grid field so the new options show up in the UI
        frm.refresh_field('items');
      }
    });
  }
});


function get_items_from_material_requirement_plan(frm, values) {
    frappe.call({
        method: 'erpnext_trackerx_customization.api.purchase_order.get_items_from_material_requirement_plan',
        args: {
            material_requirement_plan: values.material_requirement_plan,
            source_table: values.source_table,
            purchase_order: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                // Clear existing items
                frm.clear_table('items');
                                
                // Add new items
                r.message.forEach(function(item) {
                    let row = frm.add_child('items');
                    Object.assign(row, item);
                });
                                
                // Refresh the items table
                frm.refresh_field('items');
                // frm.save();
                                
                frappe.msgprint(('Items added successfully'));
            }
        }
    });
}

function create_goods_receipt_note(frm) {
    // Check if PO is submitted
    if (frm.doc.docstatus !== 1) {
        frappe.msgprint(__('Please submit the Purchase Order first'));
        return;
    }
    
    // Check if already fully received
    if (frm.doc.per_received >= 100) {
        frappe.msgprint(__('Purchase Order is already fully received'));
        return;
    }
    
    // Create new Goods Receipt Note
    frappe.model.open_mapped_doc({
        method: 'erpnext_trackerx_customization.api.purchase_order.make_goods_receipt_note',
        frm: frm,
        run_link_triggers: true
    });
}

// Alternative implementation if the mapped doc approach doesn't work
function create_goods_receipt_note_alternative(frm) {
    // Check if PO is submitted
    if (frm.doc.docstatus !== 1) {
        frappe.msgprint(__('Please submit the Purchase Order first'));
        return;
    }
    
    // Check if already fully received
    if (frm.doc.per_received >= 100) {
        frappe.msgprint(__('Purchase Order is already fully received'));
        return;
    }
    
    // Create new Goods Receipt Note
    frappe.call({
        method: 'erpnext_trackerx_customization.api.purchase_order.make_goods_receipt_note',
        args: {
            source_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                frappe.set_route('Form', 'Goods Receipt Note', r.message);
            }
        }
    });
}