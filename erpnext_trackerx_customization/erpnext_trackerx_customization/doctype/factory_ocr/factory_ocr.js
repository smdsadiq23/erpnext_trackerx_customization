// Copyright (c) 2025, CognitionX and contributors
// For license information, please see license.txt

frappe.ui.form.on('Factory OCR', {
    buyer: function(frm) {
        // Clear OCN if Buyer changes (optional but recommended)
        if (frm.doc.ocn) {
            frappe.db.get_value('Sales Order', frm.doc.ocn, ['customer', 'docstatus'])
                .then(r => {
                    const so = r.message;
                    if (!so || so.customer !== frm.doc.buyer || so.docstatus != 1) {
                        frm.set_value('ocn', '');
                    }
                });
        }
        set_ocn_query(frm);
    }, 
    ocn: function(frm) {
        if (frm.doc.ocn) {
            frappe.call({
                method: 'erpnext_trackerx_customization.erpnext_trackerx_customization.doctype.factory_ocr.factory_ocr.fetch_sales_order_items_for_factory_ocr',
                args: { sales_order: frm.doc.ocn },
                callback: function(r) {
                    frm.clear_table('table_ocn_details');
                    if (r.message && r.message.length) {
                        r.message.forEach(row => {
                            let child = frm.add_child('table_ocn_details');
                            child.style = row.style || '';
                            child.colour = row.colour || '';
                            child.order_quantity = row.order_quantity;
                            child.cut_quantity = row.cut_quantity || 0;
                            child.ship_quantity = row.ship_quantity || 0; 
                            child.rejected_garments = row.rejected_garments || 0;
                            // child.rejected_panels = row.rejected_panels || 0;
                            child.cut_to_ship = row.cut_to_ship || 0;
                        });

                        // ✅ Calculate Totals from child table
                        calculate_totals(frm);
                        frm.refresh_field('table_ocn_details');
                    }
                }
            });
        } else {
            frm.clear_table('table_ocn_details');
            frm.refresh_field('table_ocn_details');
            clear_totals(frm); // Clear totals when OCN is cleared
        }
    }  
});

// Recalculate totals whenever child table changes
frappe.ui.form.on('Factory OCR Item', {
    // Trigger on change of any key field
    order_quantity: function(frm, cdt, cdn) {
        calculate_totals(frm);
    },
    cut_quantity: function(frm, cdt, cdn) {
        calculate_totals(frm);
    },
    ship_quantity: function(frm, cdt, cdn) {
        calculate_totals(frm);
    },
    good_garments: function(frm, cdt, cdn) {
        calculate_totals(frm); // ✅ This is your main requirement
    },
    rejected_garments: function(frm, cdt, cdn) {
        calculate_totals(frm);
    },
    rejected_panels: function(frm, cdt, cdn) {
        calculate_totals(frm);
    },
    // Also recalculate when a row is added or deleted
    table_ocn_details_add: function(frm) {
        calculate_totals(frm);
    },
    table_ocn_details_remove: function(frm) {
        calculate_totals(frm);
    }
});

function set_ocn_query(frm) {
    frm.set_query('ocn', function() {
        return {
            filters: {
                customer: frm.doc.buyer,
                docstatus: 1
            }
        };
    });
}

// Helper: Calculate totals from child table
function calculate_totals(frm) {
    let total_order_qty = 0;
    let total_cut_qty = 0;
    let total_ship_qty = 0;
    let total_good_garments = 0;
    let total_rejected_garments = 0;
    let total_rejected_panels = 0;

    frm.doc.table_ocn_details.forEach(row => {
        total_order_qty += row.order_quantity || 0;
        total_cut_qty += row.cut_quantity || 0;
        total_ship_qty += row.ship_quantity || 0;
        total_good_garments += row.good_garments || 0; // ❗ Wait — you didn't fetch this!
        total_rejected_garments += row.rejected_garments || 0;
        total_rejected_panels += row.rejected_panels || 0;
    });

    // ✅ Set parent fields
    frm.set_value('total_order_qty', total_order_qty);
    frm.set_value('total_cut_qty', total_cut_qty);
    frm.set_value('total_ship_qty', total_ship_qty);
    frm.set_value('total_good_garments', total_good_garments);
    frm.set_value('total_rejected_garments', total_rejected_garments);
    frm.set_value('total_rejected_panels', total_rejected_panels);

    // ✅ Cumulative Total = Ship + Good + Rejected Garments + Rejected Panels
    let cumulative_total = total_ship_qty + total_good_garments + total_rejected_garments + total_rejected_panels;
    frm.set_value('cumulative_total', cumulative_total);

    // ✅ Cut to Ship of Order = (Total Ship / Total Cut) * 100
    let cut_to_ship_of_order = total_cut_qty > 0 ? (total_ship_qty / total_cut_qty * 100) : 0;
    frm.set_value('cut_to_ship_of_order', cut_to_ship_of_order);

    // Refresh all fields
    frm.refresh_fields([
        'total_order_qty', 'total_cut_qty', 'total_ship_qty', 'total_good_garments',
        'total_rejected_garments', 'total_rejected_panels', 'cumulative_total', 'cut_to_ship_of_order'
    ]);
}

// Helper: Clear totals when OCN is cleared
function clear_totals(frm) {
    frm.set_value('total_order_qty', 0);
    frm.set_value('total_cut_qty', 0);
    frm.set_value('total_ship_qty', 0);
    frm.set_value('total_good_garments', 0);
    frm.set_value('total_rejected_garments', 0);
    frm.set_value('total_rejected_panels', 0);
    frm.set_value('cumulative_total', 0);
    frm.set_value('cut_to_ship_of_order', 0);
    frm.refresh_fields([
        'total_order_qty', 'total_cut_qty', 'total_ship_qty', 'total_good_garments',
        'total_rejected_garments', 'total_rejected_panels', 'cumulative_total', 'cut_to_ship_of_order'
    ]);
}