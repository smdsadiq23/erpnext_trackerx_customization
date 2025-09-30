// Copyright (c) 2025, CognitionX and contributors
// For license information, please see license.txt

frappe.ui.form.on("Supplier FG Items", {
    refresh: function(frm) {
        // Apply filter on the 'item' link field
        frm.set_query('item', function() {
            return {
                filters: {
                    'custom_select_master': 'Finished Goods'
                }
            };
        });        
        frm.set_query('supplier', function() {
            return {
                filters: {
                    'supplier_group': 'Sub Contractors'
                }
            };
        });
    }
});

// Watch changes in BOM Operation child table
frappe.ui.form.on('BOM Operation', {
    // Trigger on relevant field changes
    custom_order_method: function(frm, cdt, cdn) {
        // Recalculate operating cost (if needed) and rebuild summary
        recalculate_operating_cost(frm, cdt, cdn);
        rebuild_order_method_cost(frm);
    },
    time_in_mins: function(frm, cdt, cdn) {
        recalculate_operating_cost(frm, cdt, cdn);
        rebuild_order_method_cost(frm);
    },
    hour_rate: function(frm, cdt, cdn) {
        recalculate_operating_cost(frm, cdt, cdn);
        rebuild_order_method_cost(frm);
    },
    // Also trigger on row deletion
    table_sp_fg_bom_opration_remove: function(frm) {
        rebuild_order_method_cost(frm);
    }
});

// Helper: Recalculate operating_cost for a single row
function recalculate_operating_cost(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    if (row.hour_rate && row.time_in_mins) {
        let cost = flt((flt(row.hour_rate) * flt(row.time_in_mins)) / 60, 2);
        frappe.model.set_value(cdt, cdn, 'operating_cost', cost);
    } else {
        frappe.model.set_value(cdt, cdn, 'operating_cost', 0);
    }
}

// Helper: Rebuild the grouped summary table
function rebuild_order_method_cost(frm) {
    // 1. Clear existing summary
    frm.set_value('table_sp_fg_om_cost', []);

    // 2. Group BOM Operations by custom_order_method
    let group = {};
    (frm.doc.table_sp_fg_bom_opration || []).forEach(row => {
        let method = row.custom_order_method || 'None'; // fallback if empty
        let cost = flt(row.operating_cost);

        if (!group[method]) {
            group[method] = 0;
        }
        group[method] += cost;
    });

    // 3. Add grouped rows to summary table
    let summary_rows = [];
    for (let method in group) {
        summary_rows.push({
            omc_order_method: method,
            omc_operating_cost: flt(group[method], 2),
            omc_total_cost: flt(group[method], 2) // assuming total = operating for now
        });
    }

    // 4. Set the new summary
    frm.set_value('table_sp_fg_om_cost', summary_rows);
    frm.refresh_field('table_sp_fg_om_cost');
}