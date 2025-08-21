let allowed_item_groups_map = {
    'Fabrics': ["Fabrics"],
    'Trims': ["Trims"],
    'Accessories': ["Accessories"],
    'Labels': ["Labels"],
    'Packing Materials': ["Packing Materials"]
};

frappe.ui.form.on('BOM', {
    calculate_total_cost(frm) {
        const formula = frm.doc.custom_costing_formula;
        let raw_material_cost = 0;

        if (formula === "Sum of all Items") {
            raw_material_cost = frm.doc.raw_material_cost || 0;
        } else if (formula === "Average by Sizes") {
            raw_material_cost = frm.doc.custom_raw_material_cost_avg || 0;
        } else if (formula === "Highest by Sizes") {
            raw_material_cost = frm.doc.custom_raw_material_cost_highest || 0;
        } else if (formula === "By Size") {
            const selected_size = frm.doc.custom_costing_size;
            if (!selected_size) {
                frappe.msgprint(__('Please select a size for By Size costing.'));
                return;
            }

            let size_total = 0;
            (frm.doc.items || []).forEach(row => {
                if (row.custom_size === selected_size) {
                    size_total += flt(row.amount || 0);
                }
            });
            raw_material_cost = size_total;
        }

        const operational_cost = flt(frm.doc.operating_cost || 0);
        const scrap_cost = flt(frm.doc.scrap_material_cost || 0);
        const total_cost = raw_material_cost + operational_cost + scrap_cost;

        frm.set_value('total_cost', total_cost);
        frm.set_value('raw_material_cost', raw_material_cost);
        frm.refresh_fields(['total_cost', 'raw_material_cost']);
    },

    validate(frm) {
        merge_custom_items_into_items(frm);
    },

    onload(frm) {
        frm.set_df_property('items', 'hidden', 1);
        modifyTheBOMItemTableFields(frm);
        fetch_allowed_item_groups(frm);
        set_item_filter(frm);
    },

    custom_net_qty(frm, cdt, cdn) {
        calculate_qty_based_on_net_and_wastage(frm, cdt, cdn);
    },

    custom_wastage_percentage(frm, cdt, cdn) {
        calculate_qty_based_on_net_and_wastage(frm, cdt, cdn);
    },

    refresh(frm) {
        
        maybe_update_costing_size_options(frm);
        set_item_filter(frm);

        $('[data-fieldname="item"]').on('click', function() {
            if (!frm.doc.custom_bom_type) {
                frappe.throw("Please select BOM Type first");
            }
        });
    },

    custom_costing_formula(frm) {
        maybe_update_costing_size_options(frm);
        frm.trigger("calculate_total_cost");
    },

    custom_bom_type(frm) {
        set_item_filter(frm);
    },

    custom_costing_size(frm) {
        frm.trigger("calculate_total_cost");
    },

    item: function(frm) {
        if (frm.doc.item) {
            copy_bom_operations_from_item(frm);
        }
    }
});


function set_item_filter(frm) {
    // Get Style item group details first
   
   // Set filter for item_code field in BOM Item child table
   console.log("item filters");

   item_types = []
   if(frm.doc.custom_bom_type)
   {
        
        console.log(frappe.boot.item_constants);
        bom_type_filters = frappe.boot.item_constants.bom_type_to_item_type_filters;
        item_types = bom_type_filters[frm.doc.custom_bom_type] 
        console.log(item_types);
        
    }
    frm.set_query( 'item', function() {
            return {
                filters: {
                    'custom_select_master': ['in', item_types],
                    'disabled': 0
                }
            };
    });                         
}



function generate_uuid() {
  return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
    (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
  );
}

function merge_custom_items_into_items(frm)
{
    const source_tables = [
        { table: 'custom_fabrics_items', label: 'Fabrics' },
        { table: 'custom_trims_items', label: 'Trims' },
        { table: 'custom_accessories_items', label: 'Accessories' },
        { table: 'custom_labels_items', label: 'Labels' },
        { table: 'custom_packing_materials_items', label: 'Packing Materials' }
    ];

    const required_fields = [
        'custom_supplier',
        'item_code',
        'uom',
        'custom_net_qty',
        'qty'
    ];

    const desired_item_map = {};

    for (const { table, label } of source_tables) {
        const rows = frm.doc[table] || [];

        // if ( frm.doc.docstatus == 1 && rows.length < 1) {
        //     frappe.throw(`Please add at least 1 row in <b>${label}</b> table.`);
        // }

        rows.forEach((row, idx) => {
            for (const field of required_fields) {
                if (!row[field]) {
                    const label_text = frappe.meta.get_docfield(row.doctype, field, frm.docname).label;
                    frappe.throw(`Field <b>${label_text}</b> is mandatory in row ${idx + 1} of <b>${label}</b> table.`);
                }
            }

            if (label === 'Fabrics' && !row.custom_fg_link) {
                frappe.throw(`Field <b>Panel Type</b> is mandatory in row ${idx + 1} of <b>Fabrics</b> table.`);
            }

            // Generate UUID if missing
            if (!row.custom_item_uuid) {
                row.custom_item_uuid = generate_uuid();
            }
            row.custom_item_type = label;
            desired_item_map[row.custom_item_uuid] = row;
        });
    }

    const existing_items_map = {};
    (frm.doc.items || []).forEach(item => {
        if (item.custom_item_uuid) {
            existing_items_map[item.custom_item_uuid] = item;
            copy(item, desired_item_map[item.custom_item_uuid], item.custom_item_type);
        }
    });

    // Remove items no longer present
    frm.doc.items = frm.doc.items.filter(item => {
        return item.custom_item_uuid && desired_item_map[item.custom_item_uuid];
    });

    // Add missing items
    for (const uuid in desired_item_map) {
        if (!existing_items_map[uuid]) {
            const source = desired_item_map[uuid];
            const new_row = frm.add_child('items');
            copy(new_row, source, source.custom_item_type);
            new_row.custom_item_uuid = uuid;
        }
    }

    frm.refresh_field('items');

}

function maybe_update_costing_size_options(frm) {
    if (frm.doc.custom_costing_formula === 'By Size') {
        const sizes = new Set();

        (frm.doc.items || []).forEach(row => {
            if (row.custom_size) {
                sizes.add(row.custom_size.trim());
            }
        });

        const options = Array.from(sizes).join('\n');
        frm.set_df_property('custom_costing_size', 'options', options);
        frm.refresh_field('custom_costing_size');
    }
}

function copy(new_row, row, item_type) {
    new_row.item_code = row.item_code;
    new_row.item_name = row.item_name;
    new_row.uom = row.uom;
    new_row.qty = row.qty;
    new_row.rate = row.rate;
    new_row.amount = row.amount;
    new_row.description = row.description;
    new_row.stock_uom = row.stock_uom;
    new_row.custom_fg_link = row.custom_fg_link;
    new_row.custom_article_no = row.custom_article_no;
    new_row.custom_size = row.custom_size;
    new_row.custom_consremarks = row.custom_consremarks;
    new_row.custom_artwork_reference = row.custom_artwork_reference;
    new_row.custom_wastage_percentage = row.custom_wastage_percentage;
    new_row.custom_net_qty = row.custom_net_qty;
    new_row.custom_gms = row.custom_gms;
    new_row.custom_item_type = item_type;
    new_row.custom_supplier = row.custom_supplier;
    new_row.qty_consumed_per_unit = row.qty_consumed_per_unit;
    new_row.base_amount = row.base_amount;
    new_row.custom_item_uuid = row.custom_item_uuid;
}

function modifyTheBOMItemTableFields(frm) {
    const tables = [
        'items',
        'custom_fabrics_items',
        'custom_trims_items',
        'custom_accessories_items',
        'custom_labels_items',
        'custom_packing_materials_items'
    ];

    tables.forEach(tablefield => {
        const grid = frm.fields_dict[tablefield]?.grid;
        if (!grid) return;

        frappe.meta.get_docfield('BOM Item', 'qty', frm.doc.name).read_only = 1;
        frappe.meta.get_docfield('BOM Item', 'item_name', frm.doc.name).read_only = 1;
        frappe.meta.get_docfield('BOM Item', 'qty', frm.doc.name).label = 'Cons Qty';
    });
}

// BOM Item Events
frappe.ui.form.on('BOM Item', {
    custom_net_qty(frm, cdt, cdn) {
        calculate_qty(cdt, cdn);
    },
    custom_wastage_percentage(frm, cdt, cdn) {
        calculate_qty(cdt, cdn);
    },
    custom_supplier(frm, cdt, cdn) {
        frappe.model.set_value(cdt, cdn, 'item_code', '');
        set_item_code_filters(frm);
    },
    custom_size(frm, cdt, cdn) {
        maybe_update_costing_size_options(frm);
    },
    item_code(frm, cdt, cdn) {
        maybe_update_costing_size_options(frm);
    },
    qty(frm, cdt, cdn) {
        maybe_update_costing_size_options(frm);
    }
});

function calculate_qty(cdt, cdn) {
    const row = locals[cdt][cdn];
    const net = flt(row.custom_net_qty || 0);
    const waste = flt(row.custom_wastage_percentage || 0);
    const qty = net + (net * waste / 100);

    frappe.model.set_value(cdt, cdn, 'qty', qty);
    frappe.model.set_value(cdt, cdn, 'amount', qty * row.rate);
}

function set_item_code_filters(frm) {
    const table_field_map = {
        'custom_fabrics_items': 'Fabrics',
        'custom_trims_items': 'Trims',
        'custom_accessories_items': 'Accessories',
        'custom_labels_items': 'Labels',
        'custom_packing_materials_items': 'Packing Materials'
    };

    Object.entries(table_field_map).forEach(([table_fieldname, item_type]) => {
        const grid = frm.fields_dict[table_fieldname]?.grid;
        if (!grid) return;

        const allowed_item_groups = allowed_item_groups_map[item_type] || [];

        grid.get_field('item_code').get_query = function(doc, cdt, cdn) {
            const row = locals[cdt][cdn];
            const filters = {
                is_stock_item: 1,
                disabled: 0,
                item_group: ['in', allowed_item_groups]
            };

            if (row.custom_supplier && typeof row.custom_supplier === "string" && isNaN(row.custom_supplier)) {
                filters["custom_preferred_supplier"] = row.custom_supplier;
            }

            return {
                filters,
                add_fields: "custom_preferred_supplier"
            };
        };
    });
}

function fetch_allowed_item_groups(frm) {
    const item_types = Object.keys(allowed_item_groups_map);
    let completed = 0;

    item_types.forEach(type => {
        frappe.call({
            method: 'erpnext_trackerx_customization.api.item_groups_filter.get_items_under_group_and_children',
            args: { item_group: type },
            callback: function(r) {
                if (r.message) {
                    allowed_item_groups_map[type] = [type, ...r.message.filter(g => g !== type)];
                }
                completed += 1;
                if (completed === item_types.length) {
                    set_item_code_filters(frm);
                }
            }
        });
    });
}


function copy_bom_operations_from_item(frm) {
    // Clear existing BOM Operations in the BOM
    frm.clear_table("operations");
    
    // Fetch the Item document to get BOM Operations
    frappe.call({
        method: 'frappe.client.get',
        args: {
            doctype: 'Item',
            name: frm.doc.item
        },
        callback: function(r) {
            if(r.message && r.message.custom_with_operations) {
                frm.set_value("with_operations",r.message.custom_with_operations );
                frm.refresh_field("with_operations");
            }
            if (r.message && r.message.custom_bom_operations) {
                // Copy each BOM Operation row from Item to BOM
                r.message.custom_bom_operations.forEach(function(operation) {
                    let new_row = frm.add_child("operations");
                    
                    // Copy all fields from Item BOM Operation to BOM Operation
                    // Exclude system fields like name, owner, creation, etc.
                    Object.keys(operation).forEach(function(key) {
                        if (!['name', 'owner', 'creation', 'modified', 'modified_by', 'docstatus', 'idx', 'parent', 'parentfield', 'parenttype'].includes(key)) {
                            new_row[key] = operation[key];
                        }
                    });
                });
                
                // Refresh the operations table to show the copied data
                frm.refresh_field("operations");
                
                // Show success message
                frappe.show_alert({
                    message: __('BOM Operations copied from Item successfully'),
                    indicator: 'green'
                });
            } else {
                frappe.show_alert({
                    message: __('No BOM Operations found in the selected Item'),
                    indicator: 'orange'
                });
            }
        },
        error: function() {
            frappe.msgprint(__('Error fetching Item data'));
        }
    });
}