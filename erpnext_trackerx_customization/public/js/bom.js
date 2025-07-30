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
        frappe.model.clear_table(frm.doc, 'items');

        const required_fields = [
            'custom_supplier',
            'item_code',
            'uom',
            'custom_net_qty',
            'qty'
        ];

        const merge_items = (source_table, item_type) => {
            const rows = frm.doc[source_table] || [];

            if (rows.length < 1) {
                frappe.throw(`Please add at least 1 row in <b>${item_type}</b> table.`);
            }

            rows.forEach((row, idx) => {
                for (const field of required_fields) {
                    if (!row[field]) {
                        frappe.throw(
                            `Field <b>${frappe.meta.get_docfield(row.doctype, field, frm.doc.name).label}</b> is mandatory in row ${idx + 1} of <b>${item_type}</b> table.`
                        );
                    }
                }

                if (item_type === 'Fabrics' && !row.custom_fg_link) {
                    frappe.throw(`Field <b>FG Link</b> is mandatory in row ${idx + 1} of <b>Fabrics</b> table.`);
                }

                let new_row = frm.add_child('items');
                copy(new_row, row, item_type);
            });
        };

        merge_items('custom_fabrics_items', 'Fabrics');
        merge_items('custom_trims_items', 'Trims');
        merge_items('custom_accessories_items', 'Accessories');
        merge_items('custom_labels_items', 'Labels');
        merge_items('custom_packing_materials_items', 'Packing Materials');
    },

    onload(frm) {
        frm.set_df_property('items', 'hidden', 1);
        modifyTheBOMItemTableFields(frm);
        fetch_allowed_item_groups(frm);
    },

    custom_net_qty(frm, cdt, cdn) {
        calculate_qty_based_on_net_and_wastage(frm, cdt, cdn);
    },

    custom_wastage_percentage(frm, cdt, cdn) {
        calculate_qty_based_on_net_and_wastage(frm, cdt, cdn);
    },

    refresh(frm) {
        frm.events.sync_virtual_tables(frm);
        maybe_update_costing_size_options(frm);
    },

    custom_costing_formula(frm) {
        maybe_update_costing_size_options(frm);
        frm.trigger("calculate_total_cost");
    },

    custom_costing_size(frm) {
        frm.trigger("calculate_total_cost");
    },

    after_save(frm) {
        frm.reload_doc().then(() => {
            frm.events.sync_virtual_tables(frm);
        });
    },

    onload_post_render(frm) {
        frm.events.sync_virtual_tables(frm);
    },

    sync_virtual_tables(frm) {
        if (true) return;

        frappe.model.clear_table(frm.doc, 'custom_fabrics_items');
        frappe.model.clear_table(frm.doc, 'custom_trims_items');
        frappe.model.clear_table(frm.doc, 'custom_accessories_items');
        frappe.model.clear_table(frm.doc, 'custom_labels_items');
        frappe.model.clear_table(frm.doc, 'custom_packing_materials_items');

        (frm.doc.items || []).forEach(row => {
            let target_table = {
                'Fabrics': 'custom_fabrics_items',
                'Trims': 'custom_trims_items',
                'Accessories': 'custom_accessories_items',
                'Labels': 'custom_labels_items',
                'Packing Materials': 'custom_packing_materials_items'
            }[row.custom_item_type];

            if (target_table) {
                let new_row = frm.add_child(target_table);
                copy(new_row, row, row.custom_item_type);
            }
        });

        frm.refresh_fields([
            'custom_fabrics_items',
            'custom_trims_items',
            'custom_accessories_items',
            'custom_labels_items',
            'custom_packing_materials_items'
        ]);
    }
});

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
