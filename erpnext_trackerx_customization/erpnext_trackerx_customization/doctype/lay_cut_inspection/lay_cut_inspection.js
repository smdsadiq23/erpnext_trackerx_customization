// Copyright (c) 2025, Your Company and contributors
// For license information, please see license.txt

frappe.ui.form.on('Lay Cut Inspection', {
    refresh: function(frm) {
        // Enhanced button layout with better organization
        if (!frm.doc.__islocal) {
            frm.add_custom_button(__('🔄 Recalculate All Scores'), function() {
                recalculate_all_scores(frm);
            }, __('Actions'))
            .addClass('btn-primary');
            
            frm.add_custom_button(__('📊 Generate Quality Report'), function() {
                generate_quality_summary(frm);
            }, __('Actions'))
            .addClass('btn-info');
        }
        
        // Setup buttons grouped together
        frm.add_custom_button(__('📋 Load Default Checklists'), function() {
            load_default_checklists(frm);
        }, __('Setup'))
        .addClass('btn-secondary');

        frm.add_custom_button(__('📏 Configure Layer Fields'), function() {
            generate_layer_fields(frm);
        }, __('Setup'))
        .addClass('btn-secondary');
        
        frm.add_custom_button(__('🎯 Load Test Data'), function() {
            load_test_data(frm);
        }, __('Setup'))
        .addClass('btn-warning');

        // Enhanced print options for completed inspections
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__('🖨️ Print Full Report'), function() {
                frappe.print_format.make(frm, 'Lay Cut Inspection');
            }, __('Print'))
            .addClass('btn-success');
            
            frm.add_custom_button(__('📋 Print Checklist Only'), function() {
                print_checklist_only(frm);
            }, __('Print'))
            .addClass('btn-success');
        }

        // Initialize form with enhanced features
        initialize_form_enhancements(frm);
        
        // Calculate scores on refresh with better timing
        setTimeout(() => {
            calculate_efficiency(frm);
            calculate_quality_scores(frm);
            hide_unused_layer_fields(frm);
            update_progress_indicators(frm);
            set_conditional_styling(frm);
        }, 500);
        
        // Set field colors and indicators
        set_field_indicators(frm);
        
        // Add keyboard shortcuts
        setup_keyboard_shortcuts(frm);
    },

    total_layers: function(frm) {
        hide_unused_layer_fields(frm);
        generate_layer_assessment_html(frm);
    },

    // Efficiency calculation triggers
    marker_area: function(frm) {
        calculate_efficiency(frm);
    },
    
    fabric_used: function(frm) {
        calculate_efficiency(frm);
    },

    // Quality scoring triggers
    spreading_quality_score: function(frm) {
        calculate_quality_scores(frm);
    },
    
    technical_accuracy_score: function(frm) {
        calculate_quality_scores(frm);
    },
    
    defect_deduction_score: function(frm) {
        calculate_quality_scores(frm);
    }
});

// Child table triggers for checklist items
frappe.ui.form.on('Lay Cut Checklist Item', {
    status: function(frm, cdt, cdn) {
        calculate_checklist_scores(frm);
    },
    
    fabric_quality_checks_remove: function(frm) {
        calculate_checklist_scores(frm);
    },
    
    marker_verification_checks_remove: function(frm) {
        calculate_checklist_scores(frm);
    },
    
    lay_setup_checks_remove: function(frm) {
        calculate_checklist_scores(frm);
    },
    
    pattern_placement_checks_remove: function(frm) {
        calculate_checklist_scores(frm);
    }
});

// Child table triggers for defect items
frappe.ui.form.on('Lay Cut Defect Item', {
    count: function(frm, cdt, cdn) {
        calculate_defect_scores(frm);
    },
    
    critical_defects_remove: function(frm) {
        calculate_defect_scores(frm);
    },
    
    major_defects_remove: function(frm) {
        calculate_defect_scores(frm);
    },
    
    minor_defects_remove: function(frm) {
        calculate_defect_scores(frm);
    }
});

// Child table triggers for layer quality assessments
frappe.ui.form.on('Layer Quality Assessment Item', {
    layer_number: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        validate_layer_number(frm, row);
        update_layer_quality_summary(frm);
    },
    
    quality_rating: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        auto_suggest_comments(row);
        update_layer_quality_summary(frm);
    },
    
    layer_quality_assessments_remove: function(frm) {
        update_layer_quality_summary(frm);
    }
});

// Function to calculate efficiency
function calculate_efficiency(frm) {
    if (frm.doc.marker_area && frm.doc.fabric_used) {
        const efficiency = (frm.doc.marker_area / frm.doc.fabric_used) * 100;
        frm.set_value('efficiency_percentage', efficiency);
        
        // Check if meets target
        if (frm.doc.target_efficiency) {
            const meets_target = efficiency >= frm.doc.target_efficiency;
            frm.set_df_property('efficiency_percentage', 'color', meets_target ? 'green' : 'red');
        }
    }
}

// Function to calculate quality scores
function calculate_quality_scores(frm) {
    const spreading_score = frm.doc.spreading_quality_score || 0;
    const technical_score = frm.doc.technical_accuracy_score || 0;
    const defect_score = frm.doc.defect_deduction_score || 0;
    
    // Calculate weighted total (40% + 35% + 25% = 100%)
    const total_score = (spreading_score * 0.4) + (technical_score * 0.35) + (defect_score * 0.25);
    frm.set_value('total_score', total_score);
    
    // Set quality grade
    let quality_grade = '';
    let acceptable = 0;
    
    if (total_score >= 95) {
        quality_grade = 'A+ (Excellent 95-100%)';
        acceptable = 1;
    } else if (total_score >= 85) {
        quality_grade = 'A (Good 85-94%)';
        acceptable = 1;
    } else if (total_score >= 75) {
        quality_grade = 'B (Fair 75-84%)';
        acceptable = 1;
    } else {
        quality_grade = 'C (Poor <75% - REJECT)';
        acceptable = 0;
    }
    
    frm.set_value('quality_grade', quality_grade);
    frm.set_value('acceptable', acceptable);
}

// Function to calculate checklist scores
function calculate_checklist_scores(frm) {
    let total_items = 0;
    let passed_items = 0;
    let failed_items = 0;
    
    // Count items in all checklist tables
    const checklist_tables = ['fabric_quality_checks', 'marker_verification_checks', 
                             'lay_setup_checks', 'pattern_placement_checks'];
    
    checklist_tables.forEach(table => {
        if (frm.doc[table]) {
            frm.doc[table].forEach(item => {
                total_items++;
                if (item.status === 'Pass') {
                    passed_items++;
                } else if (item.status === 'Fail') {
                    failed_items++;
                }
            });
        }
    });
    
    // Calculate spreading quality score based on checklist performance
    if (total_items > 0) {
        const pass_rate = (passed_items / total_items) * 100;
        frm.set_value('spreading_quality_score', pass_rate);
    }
}

// Function to calculate defect scores
function calculate_defect_scores(frm) {
    let total_critical = 0;
    let total_major = 0;
    let total_minor = 0;
    
    // Count defects
    if (frm.doc.critical_defects) {
        frm.doc.critical_defects.forEach(defect => {
            total_critical += defect.count || 0;
        });
    }
    
    if (frm.doc.major_defects) {
        frm.doc.major_defects.forEach(defect => {
            total_major += defect.count || 0;
        });
    }
    
    if (frm.doc.minor_defects) {
        frm.doc.minor_defects.forEach(defect => {
            total_minor += defect.count || 0;
        });
    }
    
    // Calculate defect deduction score (start with 100, deduct for defects)
    let deduction_score = 100;
    deduction_score -= (total_critical * 10); // 10 points per critical defect
    deduction_score -= (total_major * 5);     // 5 points per major defect  
    deduction_score -= (total_minor * 2);     // 2 points per minor defect
    
    // Ensure score doesn't go below 0
    deduction_score = Math.max(0, deduction_score);
    
    frm.set_value('defect_deduction_score', deduction_score);
}

// Function to hide unused layer fields
function hide_unused_layer_fields(frm) {
    const total_layers = frm.doc.total_layers || 0;
    
    // Layer fields to control
    const layer_fields = [
        'layer_10_status', 'layer_20_status', 'layer_30_status', 'layer_40_status', 'layer_50_status',
        'layer_60_status', 'layer_70_status', 'layer_80_status', 'layer_90_status', 'layer_100_status'
    ];
    
    layer_fields.forEach((field, index) => {
        const layer_number = (index + 1) * 10;
        const should_show = layer_number <= total_layers;
        frm.toggle_display(field, should_show);
    });
}

// Function to load default checklists
function load_default_checklists(frm) {
    const categories = [
        {table: 'fabric_quality_checks', category: 'Fabric Quality'},
        {table: 'marker_verification_checks', category: 'Marker Verification'},
        {table: 'lay_setup_checks', category: 'Lay Setup'},
        {table: 'pattern_placement_checks', category: 'Pattern Placement'}
    ];
    
    categories.forEach(cat => {
        frappe.call({
            method: 'erpnext_trackerx_customization.erpnext_trackerx_customization.doctype.lay_cut_inspection.lay_cut_inspection.get_default_checklists',
            args: {
                category: cat.category
            },
            callback: function(r) {
                if (r.message) {
                    // Clear existing items
                    frm.clear_table(cat.table);
                    
                    // Add default items
                    r.message.forEach(item_text => {
                        const row = frm.add_child(cat.table);
                        row.check_item = item_text;
                        row.status = 'Pending';
                        row.scoring_points = 1.0;
                    });
                    
                    frm.refresh_field(cat.table);
                }
            }
        });
    });
    
    frappe.show_alert({
        message: __('Default checklists loaded successfully'),
        indicator: 'green'
    });
}

// Function to generate layer assessment HTML
function generate_layer_assessment_html(frm) {
    const total_layers = frm.doc.total_layers || 0;
    
    if (total_layers > 0) {
        const max_layer = Math.ceil(total_layers / 10) * 10;
        let html = '<div class="alert alert-info">';
        html += '<strong>Layer Assessment Required:</strong> ';
        html += `Assess every 10th layer up to layer ${max_layer} (Total layers: ${total_layers})`;
        html += '</div>';
        
        frm.set_df_property('layer_assessment_html', 'options', html);
    }
}

// Function to generate layer fields dynamically
function generate_layer_fields(frm) {
    const total_layers = frm.doc.total_layers || 0;
    
    if (total_layers === 0) {
        frappe.msgprint(__('Please enter Total Layers first'));
        return;
    }
    
    hide_unused_layer_fields(frm);
    generate_layer_assessment_html(frm);
    
    frappe.show_alert({
        message: __('Layer assessment fields configured for {0} layers', [total_layers]),
        indicator: 'blue'
    });
}

// New enhanced functions for better UX

function recalculate_all_scores(frm) {
    calculate_efficiency(frm);
    calculate_checklist_scores(frm);
    calculate_defect_scores(frm);
    calculate_quality_scores(frm);
    
    frappe.show_alert({
        message: __('All scores recalculated successfully'),
        indicator: 'green'
    });
}

function set_field_indicators(frm) {
    // Set efficiency field color based on target
    if (frm.doc.efficiency_percentage && frm.doc.target_efficiency) {
        const meets_target = frm.doc.efficiency_percentage >= frm.doc.target_efficiency;
        frm.set_df_property('efficiency_percentage', 'description', 
            meets_target ? '✅ Meets target efficiency' : '⚠️ Below target efficiency'
        );
    }
    
    // Set quality grade color
    if (frm.doc.quality_grade) {
        let description = '';
        if (frm.doc.quality_grade.includes('A+')) {
            description = '🌟 Excellent Quality';
        } else if (frm.doc.quality_grade.includes('A')) {
            description = '✅ Good Quality';  
        } else if (frm.doc.quality_grade.includes('B')) {
            description = '⚠️ Fair Quality';
        } else if (frm.doc.quality_grade.includes('C')) {
            description = '❌ Poor Quality - Requires Action';
        }
        frm.set_df_property('quality_grade', 'description', description);
    }
}

function update_progress_indicators(frm) {
    // Count completed sections
    let completed_sections = 0;
    let total_sections = 5;
    
    // Check if header is complete
    if (frm.doc.lay_cut_number && frm.doc.order_number && frm.doc.style_number) {
        completed_sections++;
    }
    
    // Check if measurements are complete
    if (frm.doc.length_start && frm.doc.width_left && frm.doc.height_inches) {
        completed_sections++;
    }
    
    // Check if efficiency is calculated
    if (frm.doc.efficiency_percentage) {
        completed_sections++;
    }
    
    // Check if quality scores are set
    if (frm.doc.total_score) {
        completed_sections++;
    }
    
    // Check if final assessment is done
    if (frm.doc.lay_status) {
        completed_sections++;
    }
    
    const progress_percent = Math.round((completed_sections / total_sections) * 100);
    
    // Add progress indicator to form
    const progress_html = `
        <div class="progress mb-3">
            <div class="progress-bar ${progress_percent === 100 ? 'bg-success' : 'bg-primary'}" 
                 role="progressbar" style="width: ${progress_percent}%" 
                 aria-valuenow="${progress_percent}" aria-valuemin="0" aria-valuemax="100">
                ${progress_percent}% Complete
            </div>
        </div>
        <small class="text-muted">Completed sections: ${completed_sections} of ${total_sections}</small>
    `;
    
    // You can add this to a custom HTML field if needed
}

function load_test_data(frm) {
    frappe.confirm(
        __('Load comprehensive test data? This will populate the form with sample inspection data including dynamic layer assessments.'),
        function() {
            // Load enhanced sample measurements
            frm.set_value('marker_area', 32.5);
            frm.set_value('fabric_used', 38.2); 
            frm.set_value('target_efficiency', 85.0);
            frm.set_value('length_start', 320.0);
            frm.set_value('length_center', 320.3);
            frm.set_value('length_end', 319.8);
            frm.set_value('width_left', 150.0);
            frm.set_value('width_center', 150.2);
            frm.set_value('width_right', 149.9);
            frm.set_value('height_inches', 3.75);
            frm.set_value('actual_layers', 75);
            frm.set_value('end_waste_inches', 2.5);
            frm.set_value('side_waste_inches', 1.8);
            
            // Set standard layer statuses (every 10th layer)
            if (frm.doc.total_layers >= 10) frm.set_value('layer_10_status', 'Good');
            if (frm.doc.total_layers >= 20) frm.set_value('layer_20_status', 'Good');
            if (frm.doc.total_layers >= 30) frm.set_value('layer_30_status', 'Fair');
            if (frm.doc.total_layers >= 40) frm.set_value('layer_40_status', 'Good');
            if (frm.doc.total_layers >= 50) frm.set_value('layer_50_status', 'Good');
            if (frm.doc.total_layers >= 60) frm.set_value('layer_60_status', 'Good');
            if (frm.doc.total_layers >= 70) frm.set_value('layer_70_status', 'Fair');
            
            // Add dynamic layer quality assessments
            add_sample_layer_assessments(frm);
            
            frm.set_value('surface_quality_rating', 4);
            
            // Set enhanced scoring values  
            frm.set_value('spreading_quality_score', 88.5);
            frm.set_value('technical_accuracy_score', 92.0);
            frm.set_value('defect_deduction_score', 85.0);
            
            // Add comprehensive notes
            frm.set_value('inspector_comments', 'High quality lay with excellent fabric condition. Minor wrinkles detected in middle layers but within acceptable limits. Dynamic layer assessment completed for critical layers.');
            frm.set_value('quality_manager_review', 'Approved for cutting with commendation for quality standards. Monitor layer alignment for future improvements.');
            frm.set_value('corrective_actions', '1. Implement additional tension control for middle layers\n2. Review spreading technique for layers 40-50\n3. Document best practices for team training');
            frm.set_value('special_cutting_instructions', 'Use sharp blades for precision cutting. Pay attention to pattern matching on front panels. Mark notches clearly for assembly team.');
            
            frappe.show_alert({
                message: __('Enhanced test data loaded successfully! Includes dynamic layer assessments and comprehensive data.'),
                indicator: 'green'
            });
            
            // Auto-calculate scores
            setTimeout(() => {
                calculate_efficiency(frm);
                calculate_quality_scores(frm);
            }, 1000);
        }
    );
}

function add_sample_layer_assessments(frm) {
    // Clear existing layer assessments
    frm.clear_table('layer_quality_assessments');
    
    // Add sample dynamic layer assessments
    const sample_assessments = [
        {layer_number: 5, quality_rating: 'Good', comments: 'Excellent layer alignment', inspector_notes: 'Perfect tension and positioning'},
        {layer_number: 15, quality_rating: 'Good', comments: 'Clean layer with proper alignment', inspector_notes: 'No issues detected'},
        {layer_number: 23, quality_rating: 'Fair', comments: 'Minor wrinkle detected', inspector_notes: 'Small wrinkle on left edge, acceptable level'},
        {layer_number: 35, quality_rating: 'Good', comments: 'Good quality layer', inspector_notes: 'Proper fabric spreading'},
        {layer_number: 42, quality_rating: 'Poor', comments: 'Tension issue detected', inspector_notes: 'Required adjustment and re-spreading of this layer'},
        {layer_number: 58, quality_rating: 'Good', comments: 'Improved after adjustment', inspector_notes: 'Quality restored after tension correction'},
        {layer_number: 67, quality_rating: 'Good', comments: 'Consistent quality maintained', inspector_notes: 'Excellent layer condition'},
        {layer_number: 72, quality_rating: 'Fair', comments: 'Minor edge irregularity', inspector_notes: 'Edge slightly uneven but within tolerance'}
    ];
    
    sample_assessments.forEach(assessment => {
        const row = frm.add_child('layer_quality_assessments');
        row.layer_number = assessment.layer_number;
        row.quality_rating = assessment.quality_rating;
        row.comments = assessment.comments;
        row.inspector_notes = assessment.inspector_notes;
    });
    
    frm.refresh_field('layer_quality_assessments');
}

// Enhanced validation function
function validate_inspection_completeness(frm) {
    const required_fields = [
        'lay_cut_number', 'order_number', 'style_number', 'fabric_code', 
        'color', 'total_layers', 'inspector_name'
    ];
    
    const missing_fields = [];
    
    required_fields.forEach(field => {
        if (!frm.doc[field]) {
            missing_fields.push(frm.get_field(field).label);
        }
    });
    
    if (missing_fields.length > 0) {
        frappe.msgprint({
            title: __('Required Fields Missing'),
            message: __('Please fill the following required fields: {0}', [missing_fields.join(', ')]),
            indicator: 'red'
        });
        return false;
    }
    
    return true;
}

// Add validation before save
frappe.ui.form.on('Lay Cut Inspection', {
    before_save: function(frm) {
        // Auto-calculate scores before saving
        calculate_efficiency(frm);
        calculate_quality_scores(frm);
        
        // Validate completeness
        return validate_inspection_completeness(frm);
    }
});

// Enhanced UI Functions

function initialize_form_enhancements(frm) {
    // Add custom CSS for better styling
    if (!$('.lay-cut-custom-styles').length) {
        $('<style class="lay-cut-custom-styles">')
            .text(`
                .form-section .section-head { 
                    background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%);
                    padding: 8px 15px;
                    border-left: 4px solid #007bff;
                    font-weight: 600;
                }
                .quality-score-high { color: #28a745 !important; font-weight: bold; }
                .quality-score-medium { color: #ffc107 !important; font-weight: bold; }
                .quality-score-low { color: #dc3545 !important; font-weight: bold; }
                .efficiency-indicator { 
                    display: inline-block;
                    padding: 2px 8px;
                    border-radius: 12px;
                    font-size: 0.85em;
                    font-weight: bold;
                }
                .efficiency-good { background: #d4edda; color: #155724; }
                .efficiency-warning { background: #fff3cd; color: #856404; }
                .efficiency-danger { background: #f8d7da; color: #721c24; }
            `)
            .appendTo('head');
    }
    
    // Add tooltips for better UX
    add_field_tooltips(frm);
}

function add_field_tooltips(frm) {
    const tooltips = {
        'marker_area': 'Total area of the marker pattern in square meters',
        'fabric_used': 'Actual fabric consumed including waste in square meters',
        'efficiency_percentage': 'Calculated as (Marker Area / Fabric Used) × 100',
        'spreading_quality_score': 'Score based on checklist performance (0-100)',
        'technical_accuracy_score': 'Technical precision score (0-100)',
        'defect_deduction_score': 'Score after deducting for defects (0-100)',
        'total_score': 'Weighted average of all quality scores'
    };
    
    Object.keys(tooltips).forEach(field => {
        frm.set_df_property(field, 'description', tooltips[field]);
    });
}

function generate_quality_summary(frm) {
    if (!frm.doc.total_score) {
        frappe.msgprint(__('Please calculate scores first'));
        return;
    }
    
    const summary = `
        <div class="alert alert-info">
            <h5>Quality Summary for ${frm.doc.lay_cut_number}</h5>
            <hr>
            <div class="row">
                <div class="col-md-6">
                    <p><strong>Efficiency:</strong> ${frm.doc.efficiency_percentage?.toFixed(1) || 'N/A'}%</p>
                    <p><strong>Quality Grade:</strong> ${frm.doc.quality_grade || 'Not Set'}</p>
                    <p><strong>Total Score:</strong> ${frm.doc.total_score?.toFixed(1) || 'N/A'}/100</p>
                </div>
                <div class="col-md-6">
                    <p><strong>Status:</strong> ${frm.doc.lay_status || 'Pending'}</p>
                    <p><strong>Acceptable:</strong> ${frm.doc.acceptable ? 'Yes' : 'No'}</p>
                    <p><strong>Authorization:</strong> ${frm.doc.cutting_authorization || 'Pending'}</p>
                </div>
            </div>
        </div>
    `;
    
    frappe.msgprint({
        title: __('Quality Summary'),
        message: summary,
        wide: true
    });
}

function print_checklist_only(frm) {
    // Generate checklist-only print format
    let checklist_html = '<h3>Inspection Checklist - ' + frm.doc.lay_cut_number + '</h3>';
    
    const tables = [
        {name: 'fabric_quality_checks', title: 'Fabric Quality Checks'},
        {name: 'marker_verification_checks', title: 'Marker Verification'},
        {name: 'lay_setup_checks', title: 'Lay Setup Checks'},
        {name: 'pattern_placement_checks', title: 'Pattern Placement Checks'}
    ];
    
    tables.forEach(table => {
        if (frm.doc[table.name] && frm.doc[table.name].length > 0) {
            checklist_html += `<h4>${table.title}</h4><table class="table table-bordered">
                <thead><tr><th>Item</th><th>Status</th><th>Comments</th></tr></thead><tbody>`;
            
            frm.doc[table.name].forEach(item => {
                checklist_html += `<tr>
                    <td>${item.check_item}</td>
                    <td><span class="badge ${item.status === 'Pass' ? 'badge-success' : item.status === 'Fail' ? 'badge-danger' : 'badge-warning'}">${item.status}</span></td>
                    <td>${item.comments || ''}</td>
                </tr>`;
            });
            
            checklist_html += '</tbody></table>';
        }
    });
    
    frappe.print.print(checklist_html);
}

function setup_keyboard_shortcuts(frm) {
    // Add keyboard shortcuts for common actions
    $(document).on('keydown', function(e) {
        if (!frm.doc || frm.is_new()) return;
        
        // Ctrl+R: Recalculate scores
        if (e.ctrlKey && e.keyCode === 82) {
            e.preventDefault();
            recalculate_all_scores(frm);
            return false;
        }
        
        // Ctrl+L: Load default checklists
        if (e.ctrlKey && e.keyCode === 76) {
            e.preventDefault();
            load_default_checklists(frm);
            return false;
        }
    });
}

function set_conditional_styling(frm) {
    // Apply conditional styling based on values
    if (frm.doc.efficiency_percentage) {
        let efficiency_class = 'efficiency-good';
        if (frm.doc.efficiency_percentage < 70) {
            efficiency_class = 'efficiency-danger';
        } else if (frm.doc.efficiency_percentage < 80) {
            efficiency_class = 'efficiency-warning';
        }
        
        const $efficiency_field = frm.fields_dict.efficiency_percentage.$wrapper;
        $efficiency_field.find('.control-value').addClass(`efficiency-indicator ${efficiency_class}`);
    }
    
    // Style quality score fields
    if (frm.doc.total_score) {
        let score_class = 'quality-score-high';
        if (frm.doc.total_score < 75) {
            score_class = 'quality-score-low';
        } else if (frm.doc.total_score < 85) {
            score_class = 'quality-score-medium';
        }
        
        const $total_score = frm.fields_dict.total_score.$wrapper;
        $total_score.find('.control-value').addClass(score_class);
    }
}

// Enhanced progress tracking
function update_progress_indicators(frm) {
    // Count completed sections with more detail
    let completed_sections = 0;
    let total_sections = 7; // Increased sections to include layer assessments
    const progress_details = [];
    
    // Check header completion
    if (frm.doc.lay_cut_number && frm.doc.order_number && frm.doc.style_number) {
        completed_sections++;
        progress_details.push('✅ Header Information');
    } else {
        progress_details.push('❌ Header Information');
    }
    
    // Check measurements completion
    if (frm.doc.length_start && frm.doc.width_left && frm.doc.height_inches) {
        completed_sections++;
        progress_details.push('✅ Measurements');
    } else {
        progress_details.push('❌ Measurements');
    }
    
    // Check checklists completion
    const checklist_tables = ['fabric_quality_checks', 'marker_verification_checks', 'lay_setup_checks', 'pattern_placement_checks'];
    const has_checklists = checklist_tables.some(table => frm.doc[table] && frm.doc[table].length > 0);
    if (has_checklists) {
        completed_sections++;
        progress_details.push('✅ Quality Checklists');
    } else {
        progress_details.push('❌ Quality Checklists');
    }
    
    // Check layer assessments completion
    const has_layer_assessments = frm.doc.layer_quality_assessments && frm.doc.layer_quality_assessments.length > 0;
    if (has_layer_assessments) {
        completed_sections++;
        progress_details.push('✅ Layer Quality Assessments');
    } else {
        progress_details.push('❌ Layer Quality Assessments');
    }
    
    // Check efficiency calculation
    if (frm.doc.efficiency_percentage) {
        completed_sections++;
        progress_details.push('✅ Efficiency Calculation');
    } else {
        progress_details.push('❌ Efficiency Calculation');
    }
    
    // Check quality scores
    if (frm.doc.total_score) {
        completed_sections++;
        progress_details.push('✅ Quality Scoring');
    } else {
        progress_details.push('❌ Quality Scoring');
    }
    
    // Check final assessment
    if (frm.doc.lay_status) {
        completed_sections++;
        progress_details.push('✅ Final Assessment');
    } else {
        progress_details.push('❌ Final Assessment');
    }
    
    const progress_percent = Math.round((completed_sections / total_sections) * 100);
    
    // Show progress in a more detailed way
    if (frm.doc.__islocal || progress_percent < 100) {
        frappe.show_alert({
            message: `Inspection Progress: ${progress_percent}% (${completed_sections}/${total_sections} sections)`,
            indicator: progress_percent >= 80 ? 'green' : progress_percent >= 50 ? 'orange' : 'red'
        });
    }
}

// Layer Quality Assessment Functions

function validate_layer_number(frm, row) {
    if (!row.layer_number) return;
    
    // Check if layer number is within total layers
    if (frm.doc.total_layers && row.layer_number > frm.doc.total_layers) {
        frappe.msgprint({
            title: __('Invalid Layer Number'),
            message: __('Layer number {0} exceeds total layers ({1})', [row.layer_number, frm.doc.total_layers]),
            indicator: 'red'
        });
        return;
    }
    
    // Check for duplicate layer numbers
    const duplicate = frm.doc.layer_quality_assessments.find(item => 
        item.layer_number === row.layer_number && item.name !== row.name
    );
    
    if (duplicate) {
        frappe.msgprint({
            title: __('Duplicate Layer Number'),
            message: __('Layer {0} has already been assessed. Please choose a different layer number.', [row.layer_number]),
            indicator: 'orange'
        });
    }
}

function auto_suggest_comments(row) {
    if (!row.quality_rating || row.comments) return;
    
    const suggestions = {
        'Good': 'Layer quality is excellent with no issues detected',
        'Fair': 'Minor issues detected but within acceptable limits',
        'Poor': 'Significant issues requiring attention or corrective action'
    };
    
    frappe.model.set_value(row.doctype, row.name, 'comments', suggestions[row.quality_rating] || '');
}

function update_layer_quality_summary(frm) {
    if (!frm.doc.layer_quality_assessments || frm.doc.layer_quality_assessments.length === 0) {
        return;
    }
    
    let good_count = 0;
    let fair_count = 0; 
    let poor_count = 0;
    
    frm.doc.layer_quality_assessments.forEach(item => {
        switch(item.quality_rating) {
            case 'Good':
                good_count++;
                break;
            case 'Fair':
                fair_count++;
                break;
            case 'Poor':
                poor_count++;
                break;
        }
    });
    
    const total_assessed = good_count + fair_count + poor_count;
    
    if (total_assessed > 0) {
        const summary_html = `
            <div class="alert alert-info">
                <strong>Layer Quality Summary:</strong> ${total_assessed} layers assessed<br>
                <span class="text-success">Good: ${good_count}</span> | 
                <span class="text-warning">Fair: ${fair_count}</span> | 
                <span class="text-danger">Poor: ${poor_count}</span>
                ${poor_count > 0 ? '<br><small class="text-danger">⚠️ Poor quality layers require attention</small>' : ''}
            </div>
        `;
        
        // Update the assessment HTML if field exists
        if (frm.fields_dict.layer_assessment_html) {
            frm.set_df_property('layer_assessment_html', 'options', summary_html);
        }
    }
}