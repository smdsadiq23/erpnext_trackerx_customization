// -*- coding: utf-8 -*-
/**
 * Cutting Bundle Inspection JavaScript Controller
 * 
 * Provides enhanced client-side functionality with AQL calculator,
 * progress tracking, and real-time defect analysis.
 */

frappe.ui.form.on('Cutting Bundle Inspection', {
    refresh: function(frm) {
        setup_custom_buttons(frm);
        setup_progress_indicators(frm);
        setup_enhanced_ui(frm);
        update_aql_display(frm);
        
        // Auto-calculate when AQL parameters change
        if (frm.doc.lot_size && frm.doc.inspection_level && frm.doc.inspection_regime) {
            calculate_aql_parameters(frm);
        }
    },

    onload: function(frm) {
        setup_field_filters(frm);
    },

    bundle_configuration_reference: function(frm) {
        if (frm.doc.bundle_configuration_reference && frm.is_new()) {
            populate_from_bundle_configuration(frm);
        }
    },

    lot_size: function(frm) {
        calculate_aql_parameters(frm);
    },

    inspection_level: function(frm) {
        calculate_aql_parameters(frm);
    },

    inspection_regime: function(frm) {
        calculate_aql_parameters(frm);
    },

    critical_aql: function(frm) {
        calculate_aql_parameters(frm);
    },

    major_aql: function(frm) {
        calculate_aql_parameters(frm);
    },

    minor_aql: function(frm) {
        calculate_aql_parameters(frm);
    }
});

function setup_custom_buttons(frm) {
    /**
     * Add custom buttons based on form state
     */
    
    // Add AQL Calculator button
    if (!frm.is_new()) {
        frm.add_custom_button(__('Calculate AQL'), function() {
            calculate_aql_parameters(frm);
        }, __('AQL Tools'));
        
        frm.add_custom_button(__('Update Progress'), function() {
            update_inspection_progress(frm);
        }, __('Actions'));
    }
    
    // Add Bundle Configuration button
    if (frm.doc.bundle_configuration_reference) {
        frm.add_custom_button(__('View Bundle Configuration'), function() {
            frappe.set_route('Form', 'Bundle Creation', frm.doc.bundle_configuration_reference);
        }, __('Navigation'));
    }
    
    // Add Start Inspection button
    if (frm.doc.docstatus === 0 && frm.doc.inspection_status === 'Draft' && frm.doc.sample_size) {
        frm.add_custom_button(__('Start Inspection'), function() {
            start_inspection(frm);
        }, __('Actions')).addClass('btn-primary');
    }
    
    // Add Submit for Approval button
    if (frm.doc.docstatus === 0 && frm.doc.inspection_status === 'Completed') {
        frm.add_custom_button(__('Submit for Approval'), function() {
            submit_for_approval(frm);
        }, __('Actions')).addClass('btn-success');
    }
}

function setup_progress_indicators(frm) {
    /**
     * Setup progress display with visual indicators
     */
    if (frm.doc.inspection_checklist && frm.doc.inspection_checklist.length > 0) {
        let completed_items = frm.doc.inspection_checklist.filter(item => item.status !== 'Pending').length;
        let total_items = frm.doc.inspection_checklist.length;
        let progress_percent = Math.round((completed_items / total_items) * 100);
        
        let progress_html = `
            <div class="progress-container" style="margin: 10px 0;">
                <div class="progress-info" style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span><strong>Inspection Progress</strong></span>
                    <span>${completed_items} / ${total_items} completed</span>
                </div>
                <div class="progress" style="height: 20px;">
                    <div class="progress-bar bg-info" role="progressbar" 
                         style="width: ${progress_percent}%;" 
                         aria-valuenow="${progress_percent}" 
                         aria-valuemin="0" aria-valuemax="100">
                        ${progress_percent}%
                    </div>
                </div>
            </div>
        `;
        
        frm.dashboard.add_section(progress_html, __('Progress'));
    }
    
    // Add AQL Status indicators
    if (frm.doc.inspection_result) {
        let result_color = frm.doc.inspection_result === 'Pass' ? 'green' : 'red';
        frm.dashboard.add_indicator(__('Result: ') + frm.doc.inspection_result, result_color);
    }
    
    if (frm.doc.sample_size) {
        frm.dashboard.add_indicator(__('Sample Size: ') + frm.doc.sample_size, 'blue');
    }
}

function setup_enhanced_ui(frm) {
    /**
     * Setup enhanced UI with improved usability
     */
    setTimeout(function() {
        add_custom_styles();
        setup_aql_calculator_ui(frm);
        setup_defect_counter_ui(frm);
        setup_photo_capture_enhancements(frm);
        setup_defect_grid_components(frm);
        setup_sampling_plan_display(frm);
    }, 1000);
}

function setup_aql_calculator_ui(frm) {
    /**
     * Setup enhanced AQL calculator with modern design inspired by HTML template
     */
    
    // Enhanced AQL Cards Section
    if (frm.fields_dict.section_break_aql && frm.fields_dict.section_break_aql.wrapper) {
        let aql_enhanced = `
            <div class="aql-enhanced-container" style="margin: 20px 0; width: -webkit-fill-available; width: -moz-available; width: stretch;">
                <!-- AQL Selection Cards -->
                <div class="aql-cards-grid" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px;">
                    <div class="aql-severity-card critical-card">
                        <div class="card-header">
                            <h4>🔴 Critical Defects</h4>
                            <div class="aql-selector">
                                <label>AQL: ${frm.doc.critical_aql || 'Not Set'}</label>
                            </div>
                        </div>
                        <div class="card-metrics">
                            <div class="defects-found">${frm.doc.critical_defects_found || 0}</div>
                            <div class="limits-display">
                                <span class="accept">Accept: ≤${frm.doc.critical_accept_limit || 0}</span>
                                <span class="reject">Reject: ≥${frm.doc.critical_reject_limit || 1}</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="aql-severity-card major-card">
                        <div class="card-header">
                            <h4>🟠 Major Defects</h4>
                            <div class="aql-selector">
                                <label>AQL: ${frm.doc.major_aql || 'Not Set'}</label>
                            </div>
                        </div>
                        <div class="card-metrics">
                            <div class="defects-found">${frm.doc.major_defects_found || 0}</div>
                            <div class="limits-display">
                                <span class="accept">Accept: ≤${frm.doc.major_accept_limit || 0}</span>
                                <span class="reject">Reject: ≥${frm.doc.major_reject_limit || 1}</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="aql-severity-card minor-card">
                        <div class="card-header">
                            <h4>🟡 Minor Defects</h4>
                            <div class="aql-selector">
                                <label>AQL: ${frm.doc.minor_aql || 'Not Set'}</label>
                            </div>
                        </div>
                        <div class="card-metrics">
                            <div class="defects-found">${frm.doc.minor_defects_found || 0}</div>
                            <div class="limits-display">
                                <span class="accept">Accept: ≤${frm.doc.minor_accept_limit || 0}</span>
                                <span class="reject">Reject: ≥${frm.doc.minor_reject_limit || 1}</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Sample Distribution Enhanced Display -->
                <div class="sample-distribution-enhanced" style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); padding: 25px; border-radius: 12px; margin: 20px 0;">
                    <h4 style="color: #495057; margin-bottom: 20px; font-weight: 600;">📊 Sample Distribution</h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px;">
                        <div class="metric-card blue-metric">
                            <div class="metric-icon">📦</div>
                            <div class="metric-value">${frm.doc.bundles_to_sample || 0}</div>
                            <div class="metric-label">Bundles to Sample</div>
                        </div>
                        <div class="metric-card green-metric">
                            <div class="metric-icon">🎯</div>
                            <div class="metric-value">${frm.doc.pieces_to_sample || 0}</div>
                            <div class="metric-label">Pieces to Sample</div>
                        </div>
                        <div class="metric-card purple-metric">
                            <div class="metric-icon">📏</div>
                            <div class="metric-value">${frm.doc.sample_size || 0}</div>
                            <div class="metric-label">Total Sample Size</div>
                        </div>
                        <div class="metric-card result-metric ${frm.doc.inspection_result ? frm.doc.inspection_result.toLowerCase() : 'pending'}">
                            <div class="metric-icon">${frm.doc.inspection_result === 'Pass' ? '✅' : frm.doc.inspection_result === 'Fail' ? '❌' : '⏳'}</div>
                            <div class="metric-value">${frm.doc.inspection_result || 'PENDING'}</div>
                            <div class="metric-label">Inspection Result</div>
                        </div>
                    </div>
                </div>
                
                <!-- Start Inspection Button -->
                <div class="text-center" style="margin-top: 25px;">
                    <button class="quick-action-btn start-inspection-btn" onclick="startInspectionFromUI()" 
                            style="font-size: 1.1em; padding: 12px 30px; background: linear-gradient(135deg, #28a745 0%, #20c997 100%);">
                        🚀 START INSPECTION
                    </button>
                </div>
            </div>
        `;
        
        // Remove existing display and add enhanced version
        frm.fields_dict.section_break_aql.wrapper.find('.aql-enhanced-container').remove();
        frm.fields_dict.section_break_aql.wrapper.append(aql_enhanced);
    }
}

function setup_defect_counter_ui(frm) {
    /**
     * Setup defect counter with quick add functionality
     */
    if (frm.fields_dict.defect_records && frm.fields_dict.defect_records.$wrapper) {
        // Get unique components from Bundle Details table
        let component_options = '<option value="">Component</option>';
        if (frm.doc.bundle_details && frm.doc.bundle_details.length > 0) {
            let unique_components = [...new Set(frm.doc.bundle_details.map(bundle => bundle.component))];
            unique_components.forEach(component => {
                if (component) {
                    component_options += `<option value="${component}">${component}</option>`;
                }
            });
        }
        // Always add "Other" as a fallback option
        component_options += '<option value="Other">Other</option>';
        
        let defect_quick_add = `
            <div class="defect-quick-add" style="background: #fff3cd; padding: 15px; border-radius: 8px; margin: 10px 0;">
                <h6 style="margin-bottom: 10px;">⚡ Quick Add Defect</h6>
                <div class="row">
                    <div class="col-md-2">
                        <input type="text" class="form-control" placeholder="Bundle #" id="quick-bundle-no">
                    </div>
                    <div class="col-md-2">
                        <select class="form-control" id="quick-component">
                            ${component_options}
                        </select>
                    </div>
                    <div class="col-md-2">
                        <input type="text" class="form-control" placeholder="Defect Name" id="quick-defect-name">
                    </div>
                    <div class="col-md-2">
                        <select class="form-control" id="quick-severity">
                            <option value="">Severity</option>
                            <option value="Critical">Critical</option>
                            <option value="Major">Major</option>
                            <option value="Minor">Minor</option>
                        </select>
                    </div>
                    <div class="col-md-1">
                        <input type="number" class="form-control" value="1" min="1" id="quick-count">
                    </div>
                    <div class="col-md-3">
                        <button class="btn btn-primary btn-sm" onclick="addQuickDefect()">➕ Add Defect</button>
                    </div>
                </div>
            </div>
        `;
        
        frm.fields_dict.defect_records.$wrapper.find('.defect-quick-add').remove();
        frm.fields_dict.defect_records.$wrapper.prepend(defect_quick_add);
    }
}

function setup_photo_capture_enhancements(frm) {
    /**
     * Setup enhanced photo capture for inspection points
     */
    if (frm.fields_dict.inspection_checklist && frm.fields_dict.inspection_checklist.grid) {
        // Add photo capture button to each grid row
        setTimeout(function() {
            frm.fields_dict.inspection_checklist.grid.wrapper.find('.grid-row').each(function(idx, row) {
                let $row = $(row);
                let data_idx = $row.attr('data-idx');
                
                // Photo capture button removed as it was looking ugly
            });
        }, 500);
    }
}

function calculate_aql_parameters(frm) {
    /**
     * Calculate AQL parameters automatically
     */
    if (!frm.doc.lot_size || !frm.doc.inspection_level || !frm.doc.inspection_regime) {
        return;
    }
    
    frappe.call({
        method: 'erpnext_trackerx_customization.erpnext_trackerx_customization.doctype.cutting_bundle_inspection.cutting_bundle_inspection.calculate_aql_parameters',
        args: {
            lot_size: frm.doc.lot_size,
            inspection_level: frm.doc.inspection_level,
            inspection_regime: frm.doc.inspection_regime,
            critical_aql: frm.doc.critical_aql,
            major_aql: frm.doc.major_aql,
            minor_aql: frm.doc.minor_aql
        },
        callback: function(r) {
            if (r.message) {
                // Update calculated fields
                frm.set_value('sample_size', r.message.sample_size);
                frm.set_value('bundles_to_sample', r.message.bundles_to_sample);
                frm.set_value('pieces_to_sample', r.message.pieces_to_sample);
                
                if (r.message.critical_limits) {
                    frm.set_value('critical_accept_limit', r.message.critical_limits.accept);
                    frm.set_value('critical_reject_limit', r.message.critical_limits.reject);
                }
                
                if (r.message.major_limits) {
                    frm.set_value('major_accept_limit', r.message.major_limits.accept);
                    frm.set_value('major_reject_limit', r.message.major_limits.reject);
                }
                
                if (r.message.minor_limits) {
                    frm.set_value('minor_accept_limit', r.message.minor_limits.accept);
                    frm.set_value('minor_reject_limit', r.message.minor_limits.reject);
                }
                
                // Update AQL UI
                setup_aql_calculator_ui(frm);
                
                // Update sampling plan display
                update_sampling_plan_display(frm);
                
                frappe.show_alert({
                    message: __('AQL parameters calculated successfully'),
                    indicator: 'green'
                });
            }
        }
    });
}

function populate_from_bundle_configuration(frm) {
    /**
     * Populate form fields from Bundle Configuration
     */
    if (!frm.doc.bundle_configuration_reference) return;
    
    frappe.call({
        method: 'erpnext_trackerx_customization.erpnext_trackerx_customization.doctype.cutting_bundle_inspection.cutting_bundle_inspection.populate_from_bundle_configuration',
        args: {
            bundle_config_name: frm.doc.bundle_configuration_reference
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                frm.reload_doc();
                frappe.show_alert({
                    message: __('Bundle configuration data populated successfully'),
                    indicator: 'green'
                });
            }
        }
    });
}

function start_inspection(frm) {
    /**
     * Start the inspection process
     */
    frappe.confirm(
        __('Are you ready to start the inspection? This will change the status to "In Progress".'),
        function() {
            frm.set_value('inspection_status', 'In Progress');
            frm.set_value('auditor_time', frappe.datetime.now_time());
            frm.save();
            
            frappe.show_alert({
                message: __('Inspection started successfully'),
                indicator: 'blue'
            });
        }
    );
}

function submit_for_approval(frm) {
    /**
     * Submit inspection for approval
     */
    // Check if all mandatory checklist items are completed
    let pending_mandatory = frm.doc.inspection_checklist.filter(item => 
        item.is_mandatory && item.status === 'Pending'
    );
    
    if (pending_mandatory.length > 0) {
        frappe.msgprint({
            title: __('Mandatory Items Pending'),
            message: __('Please complete all mandatory checklist items before submitting for approval.'),
            indicator: 'orange'
        });
        return;
    }
    
    frappe.confirm(
        __('Are you sure you want to submit this inspection for approval?'),
        function() {
            frm.set_value('inspection_status', 'Completed');
            frm.set_value('completion_datetime', frappe.datetime.now_datetime());
            frm.set_value('inspector_signature', frappe.session.user_fullname);
            
            frm.save().then(function() {
                frappe.show_alert({
                    message: __('Inspection submitted for approval'),
                    indicator: 'green'
                });
            });
        }
    );
}

function update_inspection_progress(frm) {
    /**
     * Update inspection progress manually
     */
    // Save the document to trigger generate_inspection_summary in before_save
    frm.save().then(function() {
        setup_progress_indicators(frm);
        update_aql_display(frm);
        frappe.show_alert({
            message: __('Progress updated successfully'),
            indicator: 'green'
        });
    });
}

function update_aql_display(frm) {
    /**
     * Update AQL display with smooth animations based on current defect counts
     */
    
    // Add updated animation to metric cards
    $('.metric-card').addClass('updated');
    setTimeout(() => $('.metric-card').removeClass('updated'), 600);
    
    // Refresh the AQL display with new data
    setTimeout(function() {
        setup_aql_calculator_ui(frm);
        
        // Add progress indicators for completion
        add_progress_indicators(frm);
        
        // Update any real-time counters
        update_real_time_counters(frm);
    }, 300);
}

function add_progress_indicators(frm) {
    /**
     * Add progress indicators to show inspection completion
     */
    
    if (!frm.doc.inspection_checklist) return;
    
    let completed_items = frm.doc.inspection_checklist.filter(item => item.status !== 'Pending').length;
    let total_items = frm.doc.inspection_checklist.length;
    let progress_percentage = total_items > 0 ? (completed_items / total_items) * 100 : 0;
    
    // Add progress bar if not exists
    let progress_html = `
        <div class="inspection-progress-container" style="margin: 15px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <strong>Inspection Progress</strong>
                <span>${completed_items}/${total_items} completed</span>
            </div>
            <div class="progress-indicator" style="--progress: ${progress_percentage}%"></div>
        </div>
    `;
    
    // Remove existing and add new progress indicator
    $('.inspection-progress-container').remove();
    if (frm.fields_dict.inspection_checklist && frm.fields_dict.inspection_checklist.$wrapper) {
        frm.fields_dict.inspection_checklist.$wrapper.find('.grid-heading-row').after(progress_html);
    }
}

function update_real_time_counters(frm) {
    /**
     * Update real-time counters with animation
     */
    
    // Animate numbers counting up
    function animateValue(element, start, end, duration) {
        if (start === end) return;
        const range = end - start;
        let current = start; // Changed const to let
        const increment = end > start ? 1 : -1;
        const stepTime = Math.abs(Math.floor(duration / range));
        const obj = $(element);
        
        const timer = setInterval(() => {
            obj.text(current);
            current += increment;
            if (current === end) {
                obj.text(end);
                clearInterval(timer);
            }
        }, stepTime);
    }
    
    // Find and animate metric values
    $('.metric-value').each(function() {
        const newValue = parseInt($(this).text()) || 0;
        const oldValue = parseInt($(this).data('old-value')) || 0;
        
        if (newValue !== oldValue) {
            animateValue(this, oldValue, newValue, 800);
            $(this).data('old-value', newValue);
        }
    });
}

// Global functions for UI interactions
window.addQuickDefect = function() {
    let frm = cur_frm;
    
    let bundle_no = $('#quick-bundle-no').val();
    let component = $('#quick-component').val();
    let defect_name = $('#quick-defect-name').val();
    let severity = $('#quick-severity').val();
    let count = parseInt($('#quick-count').val()) || 1;
    
    if (!bundle_no || !component || !defect_name || !severity) {
        frappe.msgprint(__('Please fill all required fields'));
        return;
    }
    
    let new_row = frm.add_child('defect_records');
    new_row.bundle_number = bundle_no;
    new_row.component = component;
    new_row.defect_name = defect_name;
    new_row.defect_severity = severity;
    new_row.defect_count = count;
    
    frm.refresh_field('defect_records');
    frm.save();
    
    // Clear quick add form
    $('#quick-bundle-no').val('');
    $('#quick-component').val('');
    $('#quick-defect-name').val('');
    $('#quick-severity').val('');
    $('#quick-count').val('1');
    
    frappe.show_alert({
        message: __('Defect added successfully'),
        indicator: 'green'
    });
};

window.startInspectionFromUI = function() {
    /**
     * Start inspection from the enhanced UI button
     */
    let frm = cur_frm;
    
    if (!frm) {
        frappe.msgprint('Form not available');
        return;
    }
    
    // Check if required fields are filled
    if (!frm.doc.lot_size || !frm.doc.inspection_level || !frm.doc.inspection_regime) {
        frappe.msgprint({
            title: 'Missing Information',
            message: 'Please fill in Lot Size, Inspection Level, and Inspection Regime before starting inspection.',
            indicator: 'orange'
        });
        return;
    }
    
    // Call the existing start_inspection function
    start_inspection(frm);
    
    // Add visual feedback
    $('.start-inspection-btn').html('⏳ STARTING...').prop('disabled', true);
    
    setTimeout(() => {
        $('.start-inspection-btn').html('🚀 INSPECTION STARTED').css('background', 'linear-gradient(135deg, #17a2b8 0%, #138496 100%)');
    }, 1000);
};

window.captureInspectionPhoto = function(row_idx) {
    let frm = cur_frm;
    let grid = frm.fields_dict.inspection_checklist.grid;
    let row = grid.grid_rows[row_idx];
    
    if (row) {
        // Trigger file upload for photo_evidence field
        row.toggle_editable('photo_evidence', true);
        row.get_field('photo_evidence').set_focus();
    }
};

function setup_field_filters(frm) {
    /**
     * Setup field filters and queries
     */
    
    // Filter Bundle Configuration to only show those with cut_bundle_inspection = 1
    frm.set_query('bundle_configuration_reference', function() {
        return {
            filters: [
                ['cut_bundle_inspection', '=', 1],
                ['docstatus', '=', 1]
            ]
        };
    });
}

function add_custom_styles() {
    /**
     * Add enhanced CSS styles inspired by the HTML template design
     */
    
    let styles = `
        <style>
        /* AQL Enhanced Container */
        .aql-enhanced-container {
            width: 100% !important;
            max-width: 100% !important;
        }
        
        .aql-cards-grid {
            width: 100% !important;
            display: grid !important;
            grid-template-columns: repeat(3, 1fr) !important;
            gap: 20px !important;
        }
        
        /* Enhanced AQL Severity Cards */
        .aql-severity-card {
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 20px;
            text-align: center;
            transition: transform 0.2s, box-shadow 0.2s;
            border: 1px solid rgba(0,0,0,0.1);
        }
        
        .aql-severity-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 15px rgba(0, 0, 0, 0.15);
        }
        
        .critical-card {
            background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
            color: white;
        }
        
        .major-card {
            background: linear-gradient(135deg, #fd7e14 0%, #e55a00 100%);
            color: white;
        }
        
        .minor-card {
            background: linear-gradient(135deg, #ffc107 0%, #e0a800 100%);
            color: white;
        }
        
        .aql-severity-card .card-header h4 {
            margin-bottom: 10px;
            font-size: 1.2em;
            font-weight: 700;
        }
        
        .aql-selector label {
            font-size: 0.9em;
            opacity: 0.9;
        }
        
        .defects-found {
            font-size: 3rem;
            font-weight: 900;
            margin: 15px 0;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
        
        .limits-display {
            display: flex;
            justify-content: space-between;
            margin-top: 15px;
        }
        
        .limits-display span {
            font-size: 0.85em;
            font-weight: 600;
            padding: 5px 10px;
            border-radius: 15px;
            background: rgba(255,255,255,0.2);
        }
        
        .limits-display .accept {
            background: rgba(40, 167, 69, 0.3);
        }
        
        .limits-display .reject {
            background: rgba(220, 53, 69, 0.3);
        }
        
        /* Enhanced Sample Distribution Metrics */
        .metric-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            border-left: 4px solid transparent;
        }
        
        .metric-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }
        
        .blue-metric {
            border-left-color: #007bff;
        }
        
        .green-metric {
            border-left-color: #28a745;
        }
        
        .purple-metric {
            border-left-color: #6f42c1;
        }
        
        .result-metric.pass {
            border-left-color: #28a745;
            background: linear-gradient(135deg, #d4edda 0%, #ffffff 100%);
        }
        
        .result-metric.fail {
            border-left-color: #dc3545;
            background: linear-gradient(135deg, #f8d7da 0%, #ffffff 100%);
        }
        
        .result-metric.pending {
            border-left-color: #ffc107;
            background: linear-gradient(135deg, #fff3cd 0%, #ffffff 100%);
        }
        
        .metric-icon {
            font-size: 2rem;
            margin-bottom: 10px;
        }
        
        .metric-value {
            font-size: 2.5rem;
            font-weight: 900;
            color: #495057;
            margin-bottom: 8px;
        }
        
        .metric-label {
            font-size: 0.9rem;
            font-weight: 600;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        /* Responsive Design */
        @media (max-width: 1024px) {
            .aql-cards-grid {
                grid-template-columns: 1fr !important;
                gap: 15px;
            }
        }
        
        @media (max-width: 768px) {
            .aql-cards-grid {
                grid-template-columns: 1fr !important;
            }
            
            .defects-found {
                font-size: 2rem !important;
            }
            
            .metric-value {
                font-size: 1.8rem !important;
            }
        }
        
        /* Progress Indicators */
        .progress-indicator {
            background: linear-gradient(90deg, #28a745 0%, #28a745 var(--progress, 0%), #e9ecef var(--progress, 0%), #e9ecef 100%);
            height: 6px;
            border-radius: 3px;
            margin-top: 10px;
        }
        
        /* Animation for new data */
        .metric-card.updated {
            animation: pulse-update 0.6s ease-in-out;
        }
        
        @keyframes pulse-update {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        /* Enhanced Section Headers */
        .form-section .section-head {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 8px 8px 0 0;
        }
        
        .result-status {
            font-size: 1.2em;
            font-weight: bold;
        }
        
        /* Quick Action Buttons */
        .quick-action-btn {
            background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: 600;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .quick-action-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 123, 255, 0.4);
        }
        
        /* Enhanced Form Sections */
        .frappe-control[data-fieldname="section_break_sampling"] .form-section-heading {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .defect-quick-add .form-control {
            font-size: 0.9em;
        }
        
        .photo-capture-btn {
            margin-top: 2px;
        }
        
        .progress-container {
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            background: #f8f9fa;
        }
        
        /* Sampling Plan Enhanced Styles */
        .sampling-plan-enhanced {
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box;
        }
        
        .sampling-summary-cards {
            width: 100% !important;
            display: grid !important;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)) !important;
            gap: 15px !important;
        }
        
        .sampling-plan-visual {
            width: 100% !important;
            max-width: 100% !important;
        }
        
        /* Force full width for section wrapper */
        .frappe-control[data-fieldname="section_break_sampling_plan"] {
            width: 100% !important;
            max-width: 100% !important;
            grid-column: 1 / -1 !important;
            flex: 1 1 100% !important;
        }
        
        .frappe-control[data-fieldname="section_break_sampling_plan"] .form-section {
            width: 100% !important;
            max-width: 100% !important;
        }
        
        .frappe-control[data-fieldname="section_break_sampling_plan"] .form-section .section-head {
            width: 100% !important;
            max-width: 100% !important;
        }
        
        /* Force full width for sampling plan section column */
        .form-column .frappe-control[data-fieldname="section_break_sampling_plan"] {
            width: 100% !important;
            max-width: 100% !important;
            flex-basis: 100% !important;
        }
        
        /* Make sure parent column takes full width when containing sampling plan */
        .form-column:has(.frappe-control[data-fieldname="section_break_sampling_plan"]) {
            width: 100% !important;
            max-width: 100% !important;
            flex: 1 1 100% !important;
        }
        </style>
    `;
    
    if (!$('#bundle-inspection-styles').length) {
        $('head').append(styles);
        $('head').append('<style id="bundle-inspection-styles"></style>');
    }
}

// Bundle Inspection Checklist Item specific handlers
frappe.ui.form.on('Bundle Inspection Checklist Item', {
    status: function(frm, cdt, cdn) {
        let item = locals[cdt][cdn];
        
        // Auto-set checked by and date when status changes from Pending
        if (item.status !== 'Pending' && !item.checked_by) {
            frappe.model.set_value(cdt, cdn, 'checked_by', frappe.session.user);
            frappe.model.set_value(cdt, cdn, 'checked_date', frappe.datetime.now_datetime());
        }
        
        // Update progress
        setTimeout(function() {
            setup_progress_indicators(frm);
            update_inspection_progress(frm);
        }, 500);
    }
});

// Bundle Inspection Defect Item specific handlers
frappe.ui.form.on('Bundle Inspection Defect Item', {
    defect_count: function(frm) {
        update_aql_display(frm);
    },
    
    defect_severity: function(frm) {
        update_aql_display(frm);
    },
    
    defect_records_remove: function(frm) {
        update_aql_display(frm);
    },
    
    component: function(frm, cdt, cdn) {
        // This handles the component field in the grid
        // If user types something not in the list, we allow it
    }
});

function setup_defect_grid_components(frm) {
    /**
     * Setup dynamic component dropdown in defect records grid
     */
    if (frm.fields_dict.defect_records && frm.fields_dict.defect_records.grid) {
        // Get unique components from Bundle Details
        let component_options = [];
        if (frm.doc.bundle_details && frm.doc.bundle_details.length > 0) {
            let unique_components = [...new Set(frm.doc.bundle_details.map(bundle => bundle.component))];
            component_options = unique_components.filter(component => component);
        }
        
        // Add "Other" as fallback
        if (!component_options.includes("Other")) {
            component_options.push("Other");
        }
        
        // Override the component field to have autocomplete behavior
        frm.fields_dict.defect_records.grid.get_field('component').get_query = function() {
            return {
                filters: [
                    ['name', 'in', component_options]
                ]
            };
        };
        
        // Set up autocomplete for component field
        setTimeout(function() {
            $(frm.fields_dict.defect_records.wrapper).off('focusin.defect_component');
            $(frm.fields_dict.defect_records.wrapper).on('focusin.defect_component', 'input[data-fieldname="component"]', function() {
                let input = $(this);
                if (!input.hasClass('awesomplete-input')) {
                    // Create dropdown options
                    let awesomplete = new frappe.ui.form.Awesomplete(input[0], {
                        list: component_options,
                        autoFirst: true,
                        minChars: 0
                    });
                    
                    // Show dropdown on focus
                    input.on('focus', function() {
                        awesomplete.evaluate();
                        awesomplete.open();
                    });
                }
            });
        }, 500);
    }
}

function setup_sampling_plan_display(frm) {
    /**
     * Setup enhanced sampling plan display with visual breakdown
     */
    if (frm.fields_dict.section_break_sampling_plan && frm.fields_dict.section_break_sampling_plan.wrapper) {
        let sampling_enhanced = `
            <div class="sampling-plan-enhanced" style="margin: 15px 0; background: #f8f9fa; padding: 20px; border-radius: 8px; width: 100% !important; max-width: 100% !important;">
                <!-- Sampling Summary Cards -->
                <div class="sampling-summary-cards" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px;">
                    <div class="summary-card" style="background: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <div style="font-size: 24px; font-weight: bold; color: #2d5aa0;" id="total-sample-size">-</div>
                        <div style="font-size: 12px; color: #666;">Total Sample Size</div>
                    </div>
                    <div class="summary-card" style="background: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <div style="font-size: 24px; font-weight: bold; color: #17a2b8;" id="bundles-to-sample">-</div>
                        <div style="font-size: 12px; color: #666;">Bundles to Inspect</div>
                    </div>
                    <div class="summary-card" style="background: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <div style="font-size: 24px; font-weight: bold; color: #28a745;" id="total-bundles">-</div>
                        <div style="font-size: 12px; color: #666;">Total Bundles Available</div>
                    </div>
                    <div class="summary-card" style="background: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <div style="font-size: 24px; font-weight: bold; color: #ffc107;" id="sampling-efficiency">-</div>
                        <div style="font-size: 12px; color: #666;">Sampling Efficiency</div>
                    </div>
                </div>
                
                <!-- Sampling Plan Visualization -->
                <div class="sampling-plan-visual" id="sampling-plan-breakdown" style="background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h6 style="margin-bottom: 15px; color: #333;">📋 Detailed Sampling Plan</h6>
                    <div id="sampling-plan-content">
                        <p style="color: #666; text-align: center; padding: 20px;">Generate sampling plan by updating AQL parameters</p>
                    </div>
                </div>
            </div>
        `;
        
        frm.fields_dict.section_break_sampling_plan.wrapper.find(".sampling-plan-enhanced").remove();
        frm.fields_dict.section_break_sampling_plan.wrapper.append(sampling_enhanced);
        
        // Force section wrapper and all parent elements to full width
        setTimeout(() => {
            const sectionElement = $(frm.fields_dict.section_break_sampling_plan.wrapper);
            
            // Apply full width to the section and all its parent containers
            sectionElement.css({
                'width': '100% !important',
                'max-width': '100% !important'
            });
            
            sectionElement.parent().css({
                'width': '100% !important',
                'max-width': '100% !important',
                'flex': '1 1 100% !important'
            });
            
            sectionElement.closest('.form-column').css({
                'width': '100% !important',
                'max-width': '100% !important',
                'flex': '1 1 100% !important',
                'flex-basis': '100% !important'
            });
            
            sectionElement.closest('.form-page').css({
                'width': '100% !important',
                'max-width': '100% !important'
            });
        }, 100);
        
        // Update display with current data
        update_sampling_plan_display(frm);
    }
}

function update_sampling_plan_display(frm) {
    /**
     * Update sampling plan display with current data
     */
    if (!frm.doc) return;
    
    // Update summary cards
    $("#total-sample-size").text(frm.doc.sample_size || "-");
    $("#bundles-to-sample").text(frm.doc.bundles_to_sample || "-");
    
    // Calculate total bundles from bundle details
    let total_bundles = 0;
    if (frm.doc.bundle_details) {
        let unique_bundles = [...new Set(frm.doc.bundle_details.map(b => b.bundle_id))];
        total_bundles = unique_bundles.length;
    }
    $("#total-bundles").text(total_bundles);
    
    // Calculate sampling efficiency
    let efficiency = "-";
    if (frm.doc.bundles_to_sample && total_bundles > 0) {
        efficiency = Math.round((frm.doc.bundles_to_sample / total_bundles) * 100) + "%";
    }
    $("#sampling-efficiency").text(efficiency);
    
    // Update detailed sampling plan
    if (frm.doc.sampling_plan && frm.doc.sampling_plan.length > 0) {
        let plan_html = "";
        let current_bundle = "";
        
        frm.doc.sampling_plan.forEach((plan, index) => {
            if (plan.bundle_id !== current_bundle) {
                if (current_bundle !== "") {
                    plan_html += "</div></div>";
                }
                current_bundle = plan.bundle_id;
                plan_html += `
                    <div class="bundle-plan-item" style="margin-bottom: 15px; border-left: 4px solid #007bff; padding-left: 15px;">
                        <div style="font-weight: bold; color: #007bff; margin-bottom: 8px;">
                            📦 ${plan.bundle_id} 
                            <span style="font-size: 12px; color: #666;">(${plan.size}, ${plan.shade}, Ply: ${plan.ply})</span>
                        </div>
                        <div class="bundle-components" style="margin-left: 20px;">
                `;
            }
            
            plan_html += `
                <div style="margin-bottom: 5px; color: #555;">
                    <span style="display: inline-block; width: 80px; font-weight: 500;">${plan.component}:</span>
                    <span style="color: #28a745; font-weight: bold;">${plan.pieces_to_inspect} pieces</span>
                    <span style="color: #666; font-size: 11px; margin-left: 10px;">
                        (${plan.selection_method})
                    </span>
                </div>
            `;
        });
        
        if (current_bundle !== "") {
            plan_html += "</div></div>";
        }
        
        $("#sampling-plan-content").html(plan_html);
    } else {
        $("#sampling-plan-content").html(`
            <p style="color: #666; text-align: center; padding: 20px;">
                🔄 No sampling plan generated yet. Update AQL parameters to generate the plan.
            </p>
        `);
    }
}
