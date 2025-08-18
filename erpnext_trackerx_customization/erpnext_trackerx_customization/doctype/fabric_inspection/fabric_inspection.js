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
            // Add custom buttons for specific actions
            if (frm.doc.docstatus === 0) {
                frm.add_custom_button(__('Fetch Rolls from GRN'), function() {
                    fetch_rolls_from_grn(frm);
                });
                
                frm.add_custom_button(__('Calculate Sample Requirements'), function() {
                    calculate_sample_requirements(frm);
                });

                // Add Four-Point Inspection button
                frm.add_custom_button(__('🎯 Four-Point Inspection'), function() {
                    open_four_point_inspection(frm);
                }, __('Inspection'));
            }

            if (frm.doc.docstatus === 1 && frm.doc.inspection_status === 'Completed') {
                frm.add_custom_button(__('Generate Inspection Report'), function() {
                    generate_inspection_report(frm);
                });
            }
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
                    }
                }
            });
        }
    },

    inspection_type: function(frm) {
        if (frm.doc.inspection_type) {
            calculate_sample_requirements(frm);
            
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
    },

    aql_level: function(frm) {
        calculate_sample_requirements(frm);
    },

    aql_value: function(frm) {
        calculate_sample_requirements(frm);
    },

    inspection_regime: function(frm) {
        calculate_sample_requirements(frm);
    },

    total_rolls: function(frm) {
        calculate_sample_requirements(frm);
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

// Helper Functions

function fetch_rolls_from_grn(frm) {
    if (!frm.doc.grn_reference) {
        frappe.msgprint(__('Please select a GRN Reference first'));
        return;
    }

    frappe.call({
        method: 'erpnext_trackerx_customization.api.fabric_inspection.get_grn_rolls',
        args: {
            grn_reference: frm.doc.grn_reference
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                // Clear existing rolls
                frm.clear_table('fabric_rolls_tab');
                
                // Add rolls from GRN
                r.message.forEach(function(roll_data) {
                    var row = frm.add_child('fabric_rolls_tab');
                    row.roll_number = roll_data.roll_number;
                    row.shade_code = roll_data.shade_code;
                    row.lot_number = roll_data.lot_number;
                    row.roll_length = roll_data.length;
                    row.roll_width = roll_data.width;
                    row.sample_length = roll_data.length; // Default to full length for 100% inspection
                    
                    // Set inspection percentage based on inspection type
                    if (frm.doc.inspection_type === '100% Inspection') {
                        row.inspection_percentage = 100;
                        row.sample_length = roll_data.length;
                    } else {
                        // Calculate sample length based on AQL
                        row.inspection_percentage = get_sample_percentage(frm);
                        row.sample_length = (roll_data.length * row.inspection_percentage / 100).toFixed(2);
                    }
                });
                
                frm.refresh_field('fabric_rolls_tab');
                
                frappe.msgprint({
                    title: __('Success'),
                    message: __('Fetched {0} rolls from GRN', [r.message.length]),
                    indicator: 'green'
                });
            } else {
                frappe.msgprint(__('No rolls found in the selected GRN'));
            }
        }
    });
}

function calculate_sample_requirements(frm) {
    if (!frm.doc.total_rolls || !frm.doc.inspection_type) {
        return;
    }

    if (frm.doc.inspection_type === '100% Inspection') {
        frm.set_value('required_sample_size', 100);
        frm.set_value('required_sample_rolls', frm.doc.total_rolls);
        frm.set_value('required_sample_meters', calculate_total_meters(frm));
        return;
    }

    if (frm.doc.inspection_type === 'AQL Based' && frm.doc.aql_level && frm.doc.aql_value) {
        frappe.call({
            method: 'erpnext_trackerx_customization.api.fabric_inspection.calculate_aql_sample_size',
            args: {
                lot_size: frm.doc.total_rolls,
                aql_level: frm.doc.aql_level,
                aql_value: frm.doc.aql_value,
                inspection_regime: frm.doc.inspection_regime || 'Normal'
            },
            callback: function(r) {
                if (r.message) {
                    frm.set_value('required_sample_size', r.message.sample_size);
                    frm.set_value('required_sample_rolls', r.message.sample_rolls);
                    frm.set_value('required_sample_meters', r.message.sample_meters);
                }
            }
        });
    }
}

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
    // Count unique rolls in GRN items
    var unique_rolls = new Set();
    if (grn.items) {
        grn.items.forEach(function(item) {
            if (item.roll_number) {
                unique_rolls.add(item.roll_number);
            }
        });
    }
    
    var total_rolls = unique_rolls.size || grn.items.length;
    frm.set_value('total_rolls', total_rolls);
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

function get_sample_percentage(frm) {
    // Calculate sample percentage based on AQL configuration
    if (frm.doc.inspection_type === '100% Inspection') {
        return 100;
    }
    
    // Default sampling percentages based on AQL
    var sample_map = {
        'I': 10,    // AQL Level I
        'II': 20,   // AQL Level II  
        'III': 35,  // AQL Level III
        'S-1': 5,   // Special Level 1
        'S-2': 8,   // Special Level 2
        'S-3': 13,  // Special Level 3
        'S-4': 20   // Special Level 4
    };
    
    return sample_map[frm.doc.aql_level] || 25;
}

function generate_inspection_report(frm) {
    // Generate comprehensive inspection report
    frappe.call({
        method: 'erpnext_trackerx_customization.api.fabric_inspection.generate_inspection_report',
        args: {
            inspection_doc: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                window.open(r.message.report_url, '_blank');
            }
        }
    });
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

function open_four_point_inspection(frm) {
    /**
     * Open the dedicated four-point inspection page
     */
    try {
        // Check if document is saved
        if (frm.is_new()) {
            frappe.msgprint({
                title: __('Document Not Saved'),
                message: __('Please save the document first before opening Four-Point Inspection'),
                indicator: 'orange'
            });
            return;
        }

        // Check if fabric rolls exist
        if (!frm.doc.fabric_rolls_tab || frm.doc.fabric_rolls_tab.length === 0) {
            frappe.msgprint({
                title: __('No Fabric Rolls'),
                message: __('Please add fabric rolls to the inspection before opening Four-Point Inspection'),
                indicator: 'orange'
            });
            return;
        }

        // Show loading message
        frappe.show_progress(__('Opening Four-Point Inspection...'), 50, 100);

        // Save current changes before redirecting
        if (frm.is_dirty()) {
            frm.save().then(function() {
                // Open the four-point inspection page
                open_inspection_page(frm.doc.name);
            });
        } else {
            // Open directly
            open_inspection_page(frm.doc.name);
        }

    } catch (error) {
        console.error('Error opening four-point inspection:', error);
        frappe.msgprint({
            title: __('Error'),
            message: __('Error opening Four-Point Inspection: {0}', [error.message]),
            indicator: 'red'
        });
    }
}

function open_inspection_page(inspection_name) {
    /**
     * Open the four-point inspection page in a new tab
     */
    try {
        // Hide loading progress
        frappe.hide_progress();

        // Construct the URL for the traditional four-point inspection page
        const inspection_url = `/fabric_inspection_ui?name=${encodeURIComponent(inspection_name)}`;
        
        // Open in new tab
        window.open(inspection_url, '_blank');
        
        // Show success message
        frappe.msgprint({
            title: __('Four-Point Inspection Opened'),
            message: __('The Four-Point Inspection interface has been opened in a new tab'),
            indicator: 'green'
        });

    } catch (error) {
        console.error('Error opening inspection page:', error);
        frappe.hide_progress();
        frappe.msgprint({
            title: __('Error'),
            message: __('Error opening inspection page: {0}', [error.message]),
            indicator: 'red'
        });
    }
}