// Copyright (c) 2025, CognitionX and contributors
// For license information, please see license.txt

frappe.ui.form.on("Fabric Roll", {
    refresh(frm) {
        // Add Start Inspection button
        if (frm.doc.inspection_status === 'Pending') {
            frm.add_custom_button(__('Start Inspection'), function() {
                start_inspection(frm);
            }, __('Actions'));
        }
        
        // Add Complete Inspection button
        if (frm.doc.inspection_status === 'In Progress' || (frm.doc.defects && frm.doc.defects.length > 0)) {
            frm.add_custom_button(__('Complete Inspection'), function() {
                complete_inspection(frm);
            }, __('Actions'));
        }

        // Add Recalculate button
        if (frm.doc.defects && frm.doc.defects.length > 0) {
            frm.add_custom_button(__('Recalculate Points'), function() {
                calculate_defect_points(frm);
            }, __('Actions'));
        }

        // Set inspection date default
        if (!frm.doc.inspection_date) {
            frm.set_value('inspection_date', frappe.datetime.now_date());
        }
        
        // Set inspector name default
        if (!frm.doc.inspector_name) {
            frm.set_value('inspector_name', frappe.session.user_fullname);
        }
    },

    inspection_status(frm) {
        if (frm.doc.inspection_status === 'In Progress' && !frm.doc.inspection_date) {
            frm.set_value('inspection_date', frappe.datetime.now_date());
        }
    },

    length(frm) {
        // Auto-set inspected length when roll length changes
        if (frm.doc.length && !frm.doc.inspected_length) {
            frm.set_value('inspected_length', frm.doc.length);
        }
    },

    width(frm) {
        // Trigger recalculation when width changes
        if (frm.doc.defects && frm.doc.defects.length > 0) {
            calculate_defect_points(frm);
        }
    },

    inspected_length(frm) {
        // Trigger recalculation when inspected length changes
        if (frm.doc.defects && frm.doc.defects.length > 0) {
            calculate_defect_points(frm);
        }
    }
});

// Defect item events
frappe.ui.form.on("Fabric Defect Item", {
    defects_add(frm, cdt, cdn) {
        // Auto-populate some fields for new defect
        let row = locals[cdt][cdn];
        if (!row.location_position) {
            frappe.model.set_value(cdt, cdn, 'location_position', 'Center');
        }
    },

    defect_code(frm, cdt, cdn) {
        // Fetch defect details and calculate points
        let row = locals[cdt][cdn];
        if (row.defect_code) {
            // Refresh to get fetch_from fields
            frm.refresh_field('defects');
            // Recalculate after a short delay to allow fetch_from to complete
            setTimeout(() => {
                calculate_single_defect_points(frm, cdt, cdn);
            }, 500);
        }
    },

    defect_size(frm, cdt, cdn) {
        calculate_single_defect_points(frm, cdt, cdn);
    },

    defects_remove(frm) {
        // Recalculate total when defect is removed
        calculate_defect_points(frm);
    }
});

function start_inspection(frm) {
    frappe.confirm(
        __('This will start the fabric inspection process. Do you want to continue?'),
        function() {
            frm.set_value('inspection_status', 'In Progress');
            frm.set_value('inspection_date', frappe.datetime.now_date());
            frm.set_value('inspector_name', frappe.session.user_fullname);
            
            // Set default inspected length
            if (frm.doc.length && !frm.doc.inspected_length) {
                frm.set_value('inspected_length', frm.doc.length);
            }
            
            frm.save();
        }
    );
}

function complete_inspection(frm) {
    if (!frm.doc.defects || frm.doc.defects.length === 0) {
        frappe.msgprint(__('Please add defects found during inspection, or add a "No Defects" entry if no defects were found.'));
        return;
    }

    calculate_defect_points(frm);
    
    frappe.confirm(
        __('This will complete the inspection and calculate final results. Do you want to continue?'),
        function() {
            // Determine final result based on grade
            let final_result = 'First Quality';
            if (frm.doc.points_per_100_sqm > 40) {
                final_result = 'Rejected';
            } else if (frm.doc.points_per_100_sqm > 20) {
                final_result = 'Second Quality';
            }
            
            frm.set_value('final_result', final_result);
            
            // Update inspection status based on result
            if (final_result === 'Rejected') {
                frm.set_value('inspection_status', 'Rejected');
            } else {
                frm.set_value('inspection_status', 'Passed');
            }
            
            frm.save();
            
            frappe.show_alert({
                message: __('Inspection completed. Final Result: {0}', [final_result]),
                indicator: final_result === 'Rejected' ? 'red' : 'green'
            });
        }
    );
}

function calculate_single_defect_points(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    
    if (!row.defect_size) {
        return;
    }

    // Parse defect size (handle fractions and decimals)
    let size_inches = parse_measurement(row.defect_size);
    
    if (size_inches === null) {
        frappe.msgprint(__('Invalid defect size format. Use numbers, fractions (1/2) or decimals (2.5)'));
        return;
    }

    // Calculate points based on 4-point system
    let points = 0;
    if (size_inches <= 1) {
        points = 1;
    } else if (size_inches <= 3) {
        points = 2;
    } else if (size_inches <= 6) {
        points = 3;
    } else {
        points = 4;
    }

    // Set severity based on points
    let severity = 'Minor';
    if (points >= 3) {
        severity = 'Critical';
    } else if (points >= 2) {
        severity = 'Major';
    }

    frappe.model.set_value(cdt, cdn, 'defect_points', points);
    frappe.model.set_value(cdt, cdn, 'severity', severity);

    // Recalculate total after a short delay
    setTimeout(() => {
        calculate_defect_points(frm);
    }, 100);
}

function calculate_defect_points(frm) {
    if (!frm.doc.defects || frm.doc.defects.length === 0) {
        frm.set_value('total_defect_points', 0);
        frm.set_value('points_per_100_sqm', 0);
        frm.set_value('fabric_grade', 'A');
        return;
    }

    // Calculate total points
    let total_points = 0;
    frm.doc.defects.forEach(defect => {
        if (defect.defect_points) {
            total_points += defect.defect_points;
        }
    });

    frm.set_value('total_defect_points', total_points);

    // Calculate points per 100 square meters
    if (frm.doc.width && frm.doc.inspected_length) {
        let width_meters = frm.doc.width * 0.0254; // Convert inches to meters
        let area_sqm = width_meters * frm.doc.inspected_length;
        let points_per_100_sqm = (total_points * 100) / area_sqm;
        
        frm.set_value('points_per_100_sqm', points_per_100_sqm);

        // Determine fabric grade based on points per 100 sqm
        let grade = 'A';
        if (points_per_100_sqm > 40) {
            grade = 'D (Rejected)';
        } else if (points_per_100_sqm > 20) {
            grade = 'C';
        } else if (points_per_100_sqm > 10) {
            grade = 'B';
        }
        
        frm.set_value('fabric_grade', grade);
    }
}

function parse_measurement(size_str) {
    if (!size_str) return null;
    
    size_str = size_str.toString().trim();
    
    // Handle fractions (e.g., "1/2", "3/4")
    if (size_str.includes('/')) {
        let parts = size_str.split('/');
        if (parts.length === 2) {
            let numerator = parseFloat(parts[0]);
            let denominator = parseFloat(parts[1]);
            if (!isNaN(numerator) && !isNaN(denominator) && denominator !== 0) {
                return numerator / denominator;
            }
        }
    }
    
    // Handle mixed numbers (e.g., "1 1/2")
    if (size_str.includes(' ') && size_str.includes('/')) {
        let parts = size_str.split(' ');
        if (parts.length === 2) {
            let whole = parseFloat(parts[0]);
            let fraction = parse_measurement(parts[1]);
            if (!isNaN(whole) && fraction !== null) {
                return whole + fraction;
            }
        }
    }
    
    // Handle decimals
    let decimal = parseFloat(size_str);
    if (!isNaN(decimal)) {
        return decimal;
    }
    
    return null;
}