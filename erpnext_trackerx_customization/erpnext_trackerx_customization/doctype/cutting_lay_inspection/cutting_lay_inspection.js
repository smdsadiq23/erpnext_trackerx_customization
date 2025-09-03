// -*- coding: utf-8 -*-
/**
 * Cutting Lay Inspection JavaScript Controller
 * 
 * Provides client-side functionality for the Cutting Lay Inspection form
 * including progress tracking, status updates, and workflow management.
 */

frappe.ui.form.on('Cutting Lay Inspection', {
    refresh: function(frm) {
        set_inspection_status_indicators(frm);
        add_custom_buttons(frm);
        setup_progress_display(frm);
        setup_checklist_interactions(frm);
    },

    onload: function(frm) {
        setup_field_filters(frm);
    },

    cut_docket_reference: function(frm) {
        if (frm.doc.cut_docket_reference) {
            populate_from_cut_docket(frm);
        }
    },

    inspection_status: function(frm) {
        update_form_based_on_status(frm);
    },

    final_status: function(frm) {
        validate_final_status_selection(frm);
    }
});

function set_inspection_status_indicators(frm) {
    /**
     * Set visual indicators for inspection status
     */
    if (frm.doc.inspection_status) {
        let color = get_status_color(frm.doc.inspection_status);
        frm.dashboard.add_indicator(__('Status: ') + frm.doc.inspection_status, color);
    }

    if (frm.doc.progress_percentage !== undefined) {
        let progress_color = frm.doc.progress_percentage >= 100 ? 'green' : 
                           frm.doc.progress_percentage >= 50 ? 'orange' : 'red';
        frm.dashboard.add_indicator(__('Progress: ') + frm.doc.progress_percentage + '%', progress_color);
    }

    if (frm.doc.final_status) {
        let final_color = get_final_status_color(frm.doc.final_status);
        frm.dashboard.add_indicator(__('Final: ') + frm.doc.final_status, final_color);
    }
}

function add_custom_buttons(frm) {
    /**
     * Add custom buttons based on form state
     */
    
    // Add Progress Update button
    if (!frm.is_new() && frm.doc.docstatus === 0) {
        frm.add_custom_button(__('Update Progress'), function() {
            calculate_progress(frm);
        }, __('Actions'));
    }

    // Add View Cut Docket button
    if (frm.doc.cut_docket_reference) {
        frm.add_custom_button(__('View Cut Docket'), function() {
            frappe.set_route('Form', 'Cut Docket', frm.doc.cut_docket_reference);
        }, __('Navigation'));
    }

    // Add Bulk Update buttons for checklists
    if (!frm.is_new() && frm.doc.docstatus === 0) {
        add_checklist_bulk_actions(frm);
    }

    // Add Submit for Approval button
    if (frm.doc.docstatus === 0 && frm.doc.progress_percentage >= 100) {
        frm.add_custom_button(__('Submit for Approval'), function() {
            submit_for_approval(frm);
        }, __('Actions'));
    }
}

function add_checklist_bulk_actions(frm) {
    /**
     * Add bulk action buttons for checklist management
     */
    
    // Pre-Laying bulk actions
    frm.add_custom_button(__('Mark All Pre-Laying Pass'), function() {
        bulk_update_checklist(frm, 'pre_laying_checklist', 'Pass');
    }, __('Bulk Actions'));

    frm.add_custom_button(__('Mark All Pre-Laying N/A'), function() {
        bulk_update_checklist(frm, 'pre_laying_checklist', 'N/A');
    }, __('Bulk Actions'));

    // During Laying bulk actions
    frm.add_custom_button(__('Mark All During-Laying Pass'), function() {
        bulk_update_checklist(frm, 'during_laying_checklist', 'Pass');
    }, __('Bulk Actions'));

    // After Laying bulk actions
    frm.add_custom_button(__('Mark All After-Laying Pass'), function() {
        bulk_update_checklist(frm, 'after_laying_checklist', 'Pass');
    }, __('Bulk Actions'));
}

function setup_progress_display(frm) {
    /**
     * Setup progress display with visual indicators
     */
    if (frm.doc.progress_percentage !== undefined) {
        let progress_html = `
            <div class="progress-container" style="margin: 10px 0;">
                <div class="progress-info" style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span><strong>Inspection Progress</strong></span>
                    <span>${frm.doc.completed_checkpoints || 0} / ${frm.doc.total_checkpoints || 0} completed</span>
                </div>
                <div class="progress" style="height: 20px;">
                    <div class="progress-bar bg-info" role="progressbar" 
                         style="width: ${frm.doc.progress_percentage}%;" 
                         aria-valuenow="${frm.doc.progress_percentage}" 
                         aria-valuemin="0" aria-valuemax="100">
                        ${frm.doc.progress_percentage}%
                    </div>
                </div>
            </div>
        `;
        
        frm.dashboard.add_section(progress_html, __('Progress'));
    }
}

function setup_checklist_interactions(frm) {
    /**
     * Setup interactive features for checklist tables
     */
    
    // Add status change handlers for all checklist items
    ['pre_laying_checklist', 'during_laying_checklist', 'after_laying_checklist'].forEach(function(table_field) {
        frm.fields_dict[table_field].grid.get_field('status').get_query = function() {
            return {
                filters: [
                    ['name', 'in', ['Pending', 'Pass', 'Fail', 'N/A']]
                ]
            };
        };
    });
}

function setup_field_filters(frm) {
    /**
     * Setup field filters and queries
     */
    
    // Filter Cut Docket to only show those with lay_cut_inspection = 1
    frm.set_query('cut_docket_reference', function() {
        return {
            filters: [
                ['lay_cut_inspection', '=', 1],
                ['docstatus', '=', 1]
            ]
        };
    });

    // Filter inspector to show only users with Quality Inspector role
    frm.set_query('inspector', function() {
        return {
            query: 'frappe.core.doctype.user.user.user_query',
            filters: {
                'ignore_user_type': 1
            }
        };
    });
}

function populate_from_cut_docket(frm) {
    /**
     * Populate form fields from selected Cut Docket
     */
    if (frm.doc.cut_docket_reference && frm.is_new()) {
        frappe.call({
            method: 'erpnext_trackerx_customization.erpnext_trackerx_customization.doctype.cutting_lay_inspection.cutting_lay_inspection.create_from_cut_docket',
            args: {
                cut_docket_name: frm.doc.cut_docket_reference
            },
            callback: function(r) {
                if (r.message && r.message.success) {
                    frm.reload_doc();
                } else if (r.message && r.message.existing_doc) {
                    frappe.msgprint({
                        title: __('Inspection Exists'),
                        message: __('An inspection already exists for this Cut Docket. Opening existing record.'),
                        indicator: 'orange'
                    });
                    frappe.set_route('Form', 'Cutting Lay Inspection', r.message.existing_doc);
                }
            }
        });
    }
}

function calculate_progress(frm) {
    /**
     * Recalculate and update progress
     */
    frappe.call({
        method: 'erpnext_trackerx_customization.erpnext_trackerx_customization.doctype.cutting_lay_inspection.cutting_lay_inspection.get_inspection_progress',
        args: {
            inspection_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                frm.set_value('progress_percentage', r.message.progress.progress_percentage);
                frm.set_value('completed_checkpoints', r.message.progress.completed_checkpoints);
                frm.set_value('total_checkpoints', r.message.progress.total_checkpoints);
                frm.refresh_fields();
                frappe.show_alert({
                    message: __('Progress updated: {0}%', [r.message.progress.progress_percentage]),
                    indicator: 'green'
                });
            }
        }
    });
}

function bulk_update_checklist(frm, table_field, status) {
    /**
     * Bulk update checklist items status
     */
    frappe.prompt([
        {
            fieldname: 'remarks',
            fieldtype: 'Long Text',
            label: __('Remarks'),
            description: __('Optional remarks for bulk update')
        },
        {
            fieldname: 'confirm',
            fieldtype: 'Check',
            label: __('Confirm bulk update'),
            reqd: 1
        }
    ], function(values) {
        if (values.confirm) {
            // Update all items in the specified table
            frm.doc[table_field].forEach(function(item) {
                if (item.status === 'Pending') {
                    frappe.model.set_value(item.doctype, item.name, 'status', status);
                    if (values.remarks) {
                        frappe.model.set_value(item.doctype, item.name, 'remarks', values.remarks);
                    }
                    frappe.model.set_value(item.doctype, item.name, 'checked_by', frappe.session.user);
                    frappe.model.set_value(item.doctype, item.name, 'checked_date', frappe.datetime.now_datetime());
                }
            });
            
            frm.refresh_fields();
            calculate_progress(frm);
            
            frappe.show_alert({
                message: __('Bulk update completed'),
                indicator: 'green'
            });
        }
    }, __('Bulk Update Checklist'), __('Update'));
}

function submit_for_approval(frm) {
    /**
     * Submit inspection for approval
     */
    frappe.confirm(
        __('Are you sure you want to submit this inspection for approval?'),
        function() {
            frm.set_value('inspection_status', 'Completed');
            frm.save().then(function() {
                frappe.show_alert({
                    message: __('Inspection submitted for approval'),
                    indicator: 'blue'
                });
            });
        }
    );
}

function update_form_based_on_status(frm) {
    /**
     * Update form display based on inspection status
     */
    if (frm.doc.inspection_status === 'Completed') {
        // Make final summary fields mandatory
        frm.toggle_reqd('overall_audit_rating', true);
        frm.toggle_reqd('final_status', true);
        frm.toggle_reqd('auditor_signature', true);
    } else {
        frm.toggle_reqd('overall_audit_rating', false);
        frm.toggle_reqd('final_status', false);
        frm.toggle_reqd('auditor_signature', false);
    }
    
    // Disable editing if inspection is completed and submitted
    if (frm.doc.docstatus === 1) {
        frm.set_read_only();
    }
}

function validate_final_status_selection(frm) {
    /**
     * Validate final status selection and show warnings if needed
     */
    if (frm.doc.final_status === 'Rejected - Rework Required') {
        if (!frm.doc.critical_issues_identified) {
            frappe.msgprint({
                title: __('Critical Issues Required'),
                message: __('Please specify critical issues when rejecting the inspection.'),
                indicator: 'orange'
            });
            frm.scroll_to_field('critical_issues_identified');
        }
    }
    
    if (frm.doc.final_status === 'Conditional Approval') {
        if (!frm.doc.corrective_actions_required) {
            frappe.msgprint({
                title: __('Corrective Actions Required'), 
                message: __('Please specify corrective actions for conditional approval.'),
                indicator: 'orange'
            });
            frm.scroll_to_field('corrective_actions_required');
        }
    }
}

function get_status_color(status) {
    /**
     * Get color indicator for inspection status
     */
    const status_colors = {
        'Draft': 'grey',
        'In Progress': 'orange', 
        'Completed': 'blue',
        'Approved': 'green',
        'Rejected': 'red'
    };
    return status_colors[status] || 'grey';
}

function get_final_status_color(final_status) {
    /**
     * Get color indicator for final status
     */
    if (final_status.includes('Approved')) return 'green';
    if (final_status.includes('Rejected')) return 'red';
    if (final_status.includes('Conditional')) return 'orange';
    if (final_status.includes('Hold')) return 'yellow';
    return 'grey';
}

// Checklist Item specific handlers
frappe.ui.form.on('Cutting Lay Inspection Checklist Item', {
    status: function(frm, cdt, cdn) {
        /**
         * Handle status change in checklist items
         */
        let item = locals[cdt][cdn];
        
        // Auto-set checked by and date when status changes from Pending
        if (item.status !== 'Pending' && !item.checked_by) {
            frappe.model.set_value(cdt, cdn, 'checked_by', frappe.session.user);
            frappe.model.set_value(cdt, cdn, 'checked_date', frappe.datetime.now_datetime());
        }
        
        // Show warning for mandatory failed items
        if (item.is_mandatory && item.status === 'Fail') {
            frappe.msgprint({
                title: __('Mandatory Item Failed'),
                message: __('This is a mandatory checklist item. Please provide detailed remarks.'),
                indicator: 'red'
            });
            frm.scroll_to_field('remarks');
        }
        
        // Auto-calculate progress when status changes
        setTimeout(function() {
            calculate_progress(frm);
        }, 500);
    },

    checklist_master_reference: function(frm, cdt, cdn) {
        /**
         * Auto-populate fields when master reference is selected
         */
        let item = locals[cdt][cdn];
        if (item.checklist_master_reference) {
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Cut Lay Checklists',
                    name: item.checklist_master_reference
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.model.set_value(cdt, cdn, 'checkpoint', r.message.checkpoint);
                        frappe.model.set_value(cdt, cdn, 'description', r.message.description);
                        frappe.model.set_value(cdt, cdn, 'category', r.message.category);
                        frappe.model.set_value(cdt, cdn, 'is_mandatory', r.message.is_mandatory);
                    }
                }
            });
        }
    }
});

// Auto-refresh progress when checklist items are updated
$(document).on('grid-row-render', function(e, grid_row) {
    if (grid_row.doc && grid_row.doc.doctype === 'Cutting Lay Inspection Checklist Item') {
        // Add visual indicators for status
        let status_cell = grid_row.grid_form.fields_dict.status.$wrapper;
        if (status_cell && grid_row.doc.status) {
            let color = get_checklist_status_color(grid_row.doc.status);
            status_cell.find('.control-input').css('background-color', color);
        }
    }
});

function get_checklist_status_color(status) {
    /**
     * Get background color for checklist status
     */
    const colors = {
        'Pending': '#fff2cc',
        'Pass': '#d5f4e6', 
        'Fail': '#fce8e6',
        'N/A': '#e8e8e8'
    };
    return colors[status] || '#ffffff';
}