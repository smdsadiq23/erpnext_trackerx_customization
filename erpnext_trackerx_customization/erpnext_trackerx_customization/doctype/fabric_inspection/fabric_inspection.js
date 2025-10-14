frappe.ui.form.on('Fabric Inspection', {
    onload: function(frm) {
        // Initialize form settings
        try {
            frm.set_df_property('inspection_summary', 'reqd', 0);
        } catch (e) {
            console.error('Error in onload:', e);
        }
    },

    refresh: function(frm) {
        try {
            // No custom buttons - handled by mobile app
        } catch (e) {
            console.error('Error in refresh:', e);
        }
    },

    grn_reference: function(frm) {
        if (frm.doc.grn_reference) {
            // Auto-fetch item details from GRN
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Goods Receipt Note',
                    name: frm.doc.grn_reference
                },
                callback: function(r) {
                    if (r.message) {
                        var grn = r.message;
                        if (grn.items && grn.items.length > 0) {
                            var first_item = grn.items[0];
                            frm.set_value('item_code', first_item.item_code);
                            frm.set_value('item_name', first_item.item_name);
                            frm.set_value('total_quantity', grn.total_qty || 0);
                            frm.set_value('supplier', grn.supplier);
                        }
                        
                        // Calculate total rolls from GRN
                        calculate_total_rolls_from_grn(frm, grn);
                        
                        // Populate AQL configuration fields from GRN and Item master
                        populate_aql_fields_from_grn(frm);
                    }
                }
            });
        }
    },
    
    item_code: function(frm) {
        if (frm.doc.item_code && frm.doc.grn_reference) {
            // When item code changes, update AQL fields from Item master
            populate_aql_fields_from_grn(frm);
        }
    },

    inspection_type: function(frm) {
        if (frm.doc.inspection_type) {
            // Show/hide relevant fields based on inspection type
            if (frm.doc.inspection_type === '100% Inspection') {
                frm.set_value('required_sample_size', 100);
                frm.set_value('required_sample_rolls', frm.doc.total_rolls || 0);
                frm.set_df_property('required_sample_size', 'read_only', 1);
                frm.set_df_property('required_sample_rolls', 'read_only', 1);
            } else {
                frm.set_df_property('required_sample_size', 'read_only', 1);
                frm.set_df_property('required_sample_rolls', 'read_only', 1);
            }
        }
    }
});

// Child table events for Fabric Roll Inspection Item
frappe.ui.form.on('Fabric Roll Inspection Item', {
    roll_number: function(frm, cdt, cdn) {
        try {
            var row = locals[cdt][cdn];
            if (row.roll_number) {
                // Auto-fetch roll details if available
                fetch_roll_details(frm, row);
            }
        } catch (e) {
            console.error('Error in roll_number:', e);
        }
    },

    inspected: function(frm, cdt, cdn) {
        try {
            var row = locals[cdt][cdn];
            if (row.inspected) {
                calculate_roll_results(frm, row);
            }
            calculate_overall_inspection_results(frm);
        } catch (e) {
            console.error('Error in inspected:', e);
        }
    }
});

// Helper Functions - Simplified for Mobile App Integration

function calculate_total_meters(frm) {
    var total_meters = 0;
    if (frm.doc.fabric_rolls_tab) {
        frm.doc.fabric_rolls_tab.forEach(function(row) {
            if (row.roll_length) {
                total_meters += flt(row.roll_length);
            }
        });
    }
    return total_meters;
}

function calculate_total_rolls_from_grn(frm, grn) {
    // Count rolls for fabric items in GRN
    var total_rolls = 0;

    if (grn.items && grn.items.length > 0) {
        grn.items.forEach(function(item) {
            if (item.item_code === frm.doc.item_code && item.material_type === 'Fabrics') {
                total_rolls += 1; // Each item record represents one roll for fabrics
            }
        });
    }

    frm.set_value('total_rolls', total_rolls);
    console.log('Total rolls calculated from GRN:', total_rolls, 'for item:', frm.doc.item_code);
}

function populate_aql_fields_from_grn(frm) {
    if (!frm.doc.grn_reference || !frm.doc.item_code) {
        return;
    }

    // Call server-side method to populate AQL fields
    frappe.call({
        method: 'update_aql_fields_from_grn',
        doc: frm.doc,
        callback: function(r) {
            if (r.message) {
                // Update the form with the populated values
                frm.set_value('total_rolls_to_inspect', r.message.total_rolls_to_inspect);
                frm.set_value('aql_level', r.message.aql_level);
                frm.set_value('inspection_regime', r.message.inspection_regime);
                frm.set_value('aql_value', r.message.aql_value);
                frm.set_value('inspection_type', r.message.inspection_type);

                // Show success message
                frappe.msgprint({
                    title: __('AQL Configuration Updated'),
                    message: __('AQL configuration fields have been populated from Item Master and GRN'),
                    indicator: 'green'
                });
            }
        },
        error: function(err) {
            console.error('Error populating AQL fields:', err);
            frappe.msgprint({
                title: __('Error'),
                message: __('Error populating AQL configuration fields'),
                indicator: 'red'
            });
        }
    });
}

function calculate_roll_results(frm, roll_row) {
    try {
        if (!roll_row || !roll_row.roll_number) {
            return;
        }

        // Basic roll calculations
        var roll_area = (flt(roll_row.roll_length) * flt(roll_row.roll_width)) / 1550;
        var defect_points = flt(roll_row.total_defect_points) || 0;
        
        if (roll_area > 0) {
            roll_row.points_per_100_sqm = (defect_points * 100) / roll_area;
            
            // Set grade and result based on points per 100 sqm
            if (roll_row.points_per_100_sqm <= 25) {
                roll_row.roll_grade = 'A';
                roll_row.roll_result = 'Accepted';
            } else if (roll_row.points_per_100_sqm <= 50) {
                roll_row.roll_grade = 'B';
                roll_row.roll_result = 'Conditional Accept';
            } else {
                roll_row.roll_grade = 'C';
                roll_row.roll_result = 'Rejected';
            }
        }
        
        frm.refresh_field('fabric_rolls_tab');
    } catch (e) {
        console.error('Error in calculate_roll_results:', e);
    }
}

function calculate_overall_inspection_results(frm) {
    try {
        if (!frm.doc.fabric_rolls_tab || frm.doc.fabric_rolls_tab.length === 0) {
            return;
        }

        var total_points = 0;
        var inspected_rolls = 0;
        var accepted_rolls = 0;

        frm.doc.fabric_rolls_tab.forEach(function(roll) {
            if (roll.inspected) {
                inspected_rolls += 1;
                total_points += flt(roll.total_defect_points);
                
                if (roll.roll_result === 'Accepted') {
                    accepted_rolls += 1;
                }
            }
        });

        // Update overall results
        frm.set_value('total_defect_points', total_points);
        
        // Determine overall result
        var acceptance_rate = inspected_rolls > 0 ? (accepted_rolls / inspected_rolls) * 100 : 0;
        
        if (acceptance_rate >= 95) {
            frm.set_value('inspection_result', 'Accepted');
            frm.set_value('quality_grade', 'A');
        } else if (acceptance_rate >= 80) {
            frm.set_value('inspection_result', 'Conditional Accept');
            frm.set_value('quality_grade', 'B');
        } else {
            frm.set_value('inspection_result', 'Rejected');
            frm.set_value('quality_grade', 'C');
        }
        
        // Update inspection status
        if (inspected_rolls === frm.doc.fabric_rolls_tab.length) {
            frm.set_value('inspection_status', 'Completed');
        } else if (inspected_rolls > 0) {
            frm.set_value('inspection_status', 'In Progress');
        }
    } catch (e) {
        console.error('Error in calculate_overall_inspection_results:', e);
    }
}

function fetch_roll_details(frm, roll_row) {
    if (!roll_row.roll_number) return;

    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Fabric Roll',
            filters: {
                roll_id: roll_row.roll_number
            },
            fields: ['length', 'width', 'shade_code', 'lot_no', 'gsm']
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                var roll_data = r.message[0];
                roll_row.roll_length = roll_data.length;
                roll_row.roll_width = roll_data.width;
                roll_row.shade_code = roll_data.shade_code;
                roll_row.lot_number = roll_data.lot_no;
                frm.refresh_field('fabric_rolls_tab');
            }
        }
    });
}

