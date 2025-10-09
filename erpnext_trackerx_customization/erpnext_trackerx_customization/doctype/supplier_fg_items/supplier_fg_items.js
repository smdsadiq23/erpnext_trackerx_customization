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

        // Add "Fetch from Item" button on the BOM Operation grid and place it before "Add Row"
        add_fetch_from_item_button(frm);
    }
});

// ---- BOM Operation child events (keep your existing logic) ----
frappe.ui.form.on('BOM Operation', {
    custom_order_method: function(frm, cdt, cdn) {
        recalculate_operating_cost(frm, cdt, cdn);
        // Only rebuild on Supplier FG Items (avoid hitting Item doctype)
        if (frm.doc.doctype === 'Supplier FG Items') rebuild_order_method_cost(frm);
    },
    time_in_mins: function(frm, cdt, cdn) {
        recalculate_operating_cost(frm, cdt, cdn);
        if (frm.doc.doctype === 'Supplier FG Items') rebuild_order_method_cost(frm);
    },
    hour_rate: function(frm, cdt, cdn) {
        recalculate_operating_cost(frm, cdt, cdn);
        if (frm.doc.doctype === 'Supplier FG Items') rebuild_order_method_cost(frm);
    },
    // Trigger on row deletion
    table_sp_fg_bom_operation_remove: function(frm) {
        if (frm.doc.doctype === 'Supplier FG Items') rebuild_order_method_cost(frm);
    }
});

// ---- Helper: Add & position the custom button on the grid ----
function add_fetch_from_item_button(frm) {
    const fieldname = 'table_sp_fg_bom_operation'; // child table fieldname on Supplier FG Items
    const grid = frm.get_field(fieldname)?.grid;
    if (!grid) return;

    // Avoid duplicates on refresh
    if (grid.__fetch_from_item_btn_added) return;

    const $btn = grid.add_custom_button('Fetch from Item', async () => {
        if (!frm.doc.item) {
            frappe.msgprint(__('Please select an Item first.'));
            return;
        }
        await fetch_operations_from_item_and_fill(frm, frm.doc.item, fieldname);
    });

    // Move our button before the default "Add Row"
    try {
        const $addRow = grid.wrapper.find('.grid-add-row');
        if ($btn && $addRow && $addRow.length) {
            $btn.insertBefore($addRow);
        }
    } catch (e) {
        // if DOM structure changes, it's ok—button will still be visible in the toolbar
        console.warn('Could not reposition Fetch button:', e);
    }

    grid.__fetch_from_item_btn_added = true;
}

// ---- Helper: Call server, fill rows, refresh summary ----
async function fetch_operations_from_item_and_fill(frm, item, fieldname) {
    try {
        frappe.dom.freeze(__('Fetching BOM Operations from Item…'));
        const r = await frappe.call({
            method: 'erpnext_trackerx_customization.erpnext_trackerx_customization.doctype.supplier_fg_items.supplier_fg_items.get_item_bom_operations',
            args: { item }
        });

        const ops = r.message || [];

        // Clear existing rows to avoid duplicates (change to append-only if you prefer)
        frm.clear_table(fieldname);

        // Only map the requested fields
        ops.forEach(op => {
            const row = frm.add_child(fieldname);
            row.custom_order_method    = op.custom_order_method || '';
            row.custom_operation_group = op.custom_operation_group || '';
            row.operation              = op.operation || '';
            // leave your costing/time fields untouched; user will fill or you can add auto-fill later
        });

        frm.refresh_field(fieldname);

        // Recompute your grouped summary after importing rows
        rebuild_order_method_cost(frm);

        frappe.show_alert({message: __('Imported {0} operation(s) from Item', [ops.length]), indicator: 'green'});
    } catch (err) {
        console.error(err);
        frappe.msgprint(__('Failed to fetch operations from Item.'));
    } finally {
        frappe.dom.unfreeze();
    }
}

// ---- Your existing helpers (unchanged) ----

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
    // Guard: only run when we're actually on Supplier FG Items and the summary field exists
    if (frm.doc.doctype !== 'Supplier FG Items') return;
    if (!frm.fields_dict || !frm.fields_dict.table_sp_fg_om_cost) return;

    // 1. Clear existing summary
    frm.set_value('table_sp_fg_om_cost', []);

    // 2. Group BOM Operations by custom_order_method
    let group = {};
    (frm.doc.table_sp_fg_bom_operation || []).forEach(row => {
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
