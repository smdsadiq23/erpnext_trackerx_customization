// -*- coding: utf-8 -*-
/**
 * Cutting Lay Inspection Enhanced JavaScript Controller
 * 
 * Provides enhanced client-side functionality with tabbed card interface for checklists
 * for improved user experience and reduced scrolling.
 */

frappe.ui.form.on('Cutting Lay Inspection', {
    refresh: function(frm) {
        set_inspection_status_indicators(frm);
        add_custom_buttons(frm);
        setup_progress_display(frm);
        setup_enhanced_ui(frm);
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

function setup_enhanced_ui(frm) {
    /**
     * Setup enhanced UI with improved usability
     */
    setTimeout(function() {
        console.log('Setting up enhanced UI...');
        add_custom_styles();
        setup_checklist_enhancements(frm);
        console.log('Enhanced UI setup completed');
    }, 1000);
}


function setup_checklist_enhancements(frm) {
    /**
     * Add enhancements to checklist tables
     */
    console.log('🎯 Setting up checklist enhancements...');
    
    let checklists_processed = 0;
    ['pre_laying_checklist', 'during_laying_checklist', 'after_laying_checklist'].forEach(function(table_name) {
        let field = frm.fields_dict[table_name];
        console.log(`📋 Checking checklist table: ${table_name}`, {
            field_exists: !!field,
            wrapper_exists: !!(field && field.$wrapper),
            wrapper_length: field && field.$wrapper ? field.$wrapper.length : 0,
            grid_exists: !!(field && field.grid),
            grid_wrapper_exists: !!(field && field.grid && field.grid.wrapper),
            data_length: frm.doc[table_name] ? frm.doc[table_name].length : 0
        });
        
        if (field && field.$wrapper) {
            // Add enhanced styling
            field.$wrapper.addClass('enhanced-checklist-table');
            console.log(`✅ Added styling to ${table_name}`);
            
            // Enhance the grid
            if (field.grid && field.grid.wrapper) {
                field.grid.wrapper.addClass('checklist-grid-enhanced');
                console.log(`✅ Enhanced grid for ${table_name}`);
                
                // Add custom buttons to grid
                add_checklist_quick_actions(field, table_name, frm);
                checklists_processed++;
            } else {
                console.warn(`❌ Grid not ready for ${table_name}`);
            }
        } else {
            console.warn(`❌ Field not found for ${table_name}`);
        }
    });
    
    console.log(`✅ Checklist enhancements processed: ${checklists_processed}/3`);
}




function add_checklist_quick_actions(field, table_name, frm) {
    /**
     * Add quick action buttons to checklist grids
     */
    console.log(`🎯 Adding quick actions for ${table_name}`);
    console.log(`Grid details:`, {
        grid_exists: !!field.grid,
        wrapper_exists: !!(field.grid && field.grid.wrapper),
        wrapper_length: field.grid && field.grid.wrapper ? field.grid.wrapper.length : 0
    });
    
    if (!field.grid || !field.grid.wrapper) {
        console.warn(`❌ No grid or wrapper found for ${table_name}`);
        return;
    }
    
    let grid_wrapper = field.grid.wrapper;
    let existing_actions = grid_wrapper.find('.checklist-quick-actions');
    if (existing_actions.length) {
        console.log(`⚠️ Quick actions already exist for ${table_name}, removing old ones`);
        existing_actions.remove();
    }
    
    let heading_row = grid_wrapper.find('.grid-heading-row');
    console.log(`📊 Grid heading row found: ${heading_row.length}`);
    
    let quick_actions_html = `
        <div class="checklist-quick-actions" style="padding: 10px; background: #f8f9fa; border-bottom: 1px solid #dee2e6;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <strong>Quick Actions for ${table_name.replace('_', ' ').toUpperCase()}:</strong>
                <div class="btn-group" role="group">
                    <button type="button" class="btn btn-sm btn-success quick-action-btn" data-action="mark-all-pass" data-table="${table_name}">
                        <i class="fa fa-check"></i> Mark All Pass
                    </button>
                    <button type="button" class="btn btn-sm btn-secondary quick-action-btn" data-action="mark-all-na" data-table="${table_name}">
                        <i class="fa fa-minus"></i> Mark All N/A
                    </button>
                    <button type="button" class="btn btn-sm btn-outline-primary quick-action-btn" data-action="add-remarks" data-table="${table_name}">
                        <i class="fa fa-comment"></i> Bulk Remarks
                    </button>
                </div>
            </div>
        </div>
    `;
    
    if (heading_row.length) {
        heading_row.after(quick_actions_html);
        console.log(`✅ Added quick actions HTML for ${table_name}`);
    } else {
        // Fallback: add at the top of grid body
        grid_wrapper.find('.grid-body').prepend(quick_actions_html);
        console.log(`✅ Added quick actions HTML to grid body for ${table_name}`);
    }
    
    // Add click handlers with debugging
    setTimeout(function() {
        let action_buttons = grid_wrapper.find('.quick-action-btn');
        console.log(`🔘 Found ${action_buttons.length} action buttons for ${table_name}`);
        
        action_buttons.off('click').on('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            let action = $(this).data('action');
            let table = $(this).data('table');
            
            console.log(`🔄 Quick action clicked: ${action} for table: ${table}`);
            handle_checklist_quick_action(action, table, frm);
        });
        
        console.log(`✅ Click handlers attached for ${table_name}`);
    }, 100);
}

function handle_checklist_quick_action(action, table_name, frm) {
    /**
     * Handle quick action button clicks
     */
    console.log(`🚀 Handling quick action: ${action} for table: ${table_name}`);
    console.log(`📊 Current form state:`, {
        form_exists: !!frm,
        doc_exists: !!frm.doc,
        table_exists: !!(frm.doc && frm.doc[table_name]),
        table_length: frm.doc && frm.doc[table_name] ? frm.doc[table_name].length : 0
    });
    
    switch(action) {
        case 'mark-all-pass':
            console.log('🎯 Executing mark-all-pass action');
            bulk_update_checklist(frm, table_name, 'Pass');
            break;
        case 'mark-all-na':
            console.log('🎯 Executing mark-all-na action');
            bulk_update_checklist(frm, table_name, 'N/A');
            break;
        case 'add-remarks':
            console.log('🎯 Executing add-remarks action');
            add_bulk_remarks(frm, table_name);
            break;
        default:
            console.error(`❌ Unknown action: ${action}`);
            frappe.msgprint({
                title: __('Error'),
                message: __('Unknown action: {0}', [action]),
                indicator: 'red'
            });
    }
}

function add_bulk_remarks(frm, table_name) {
    /**
     * Add remarks to all pending items in a checklist
     */
    frappe.prompt({
        fieldname: 'bulk_remarks',
        fieldtype: 'Long Text',
        label: __('Bulk Remarks'),
        description: __('Add remarks to all pending items in this checklist')
    }, function(values) {
        if (!values.bulk_remarks) return;
        
        let updated_count = 0;
        frm.doc[table_name].forEach(function(item) {
            if (item.status === 'Pending') {
                frappe.model.set_value(item.doctype, item.name, 'remarks', values.bulk_remarks);
                updated_count++;
            }
        });
        
        frm.refresh_field(table_name);
        
        frappe.show_alert({
            message: __('Added remarks to {0} items', [updated_count]),
            indicator: 'green'
        });
    }, __('Add Bulk Remarks'));
}

function create_tabbed_checklists(frm) {
    /**
     * Create tabbed card interface for checklists
     */
    
    // Hide original checklist sections
    hide_original_checklist_sections(frm);
    
    // Find the container to add our tabbed interface
    let container = null;
    if (frm.fields_dict.section_break_pre_laying && frm.fields_dict.section_break_pre_laying.$wrapper) {
        container = frm.fields_dict.section_break_pre_laying.$wrapper;
    } else {
        // Fallback: find by looking for the first checklist table
        let pre_laying_field = frm.fields_dict.pre_laying_checklist;
        if (pre_laying_field && pre_laying_field.$wrapper) {
            container = pre_laying_field.$wrapper.closest('.frappe-section');
        }
    }
    
    if (!container || !container.length) {
        console.log('Container not found for tabbed checklists');
        return;
    }
    
    // Create tabbed interface HTML
    let tabbed_html = `
        <div class="checklist-tabs-container" style="margin: 20px 0;">
            <div class="section-head">
                <h5 class="text-muted uppercase">Inspection Checklists</h5>
            </div>
            
            <!-- Tab Navigation -->
            <ul class="nav nav-tabs checklist-nav-tabs" role="tablist" style="margin-bottom: 0;">
                <li class="nav-item">
                    <a class="nav-link active" id="pre-laying-tab" data-toggle="tab" href="#pre-laying-panel" 
                       role="tab" aria-controls="pre-laying-panel" aria-selected="true">
                        <i class="fa fa-play-circle"></i> Pre-Laying
                        <span class="badge badge-pill badge-light ml-2" id="pre-laying-count">0</span>
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" id="during-laying-tab" data-toggle="tab" href="#during-laying-panel" 
                       role="tab" aria-controls="during-laying-panel" aria-selected="false">
                        <i class="fa fa-cogs"></i> During Laying
                        <span class="badge badge-pill badge-light ml-2" id="during-laying-count">0</span>
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" id="after-laying-tab" data-toggle="tab" href="#after-laying-panel" 
                       role="tab" aria-controls="after-laying-panel" aria-selected="false">
                        <i class="fa fa-check-circle"></i> After Laying
                        <span class="badge badge-pill badge-light ml-2" id="after-laying-count">0</span>
                    </a>
                </li>
            </ul>
            
            <!-- Tab Content -->
            <div class="tab-content checklist-tab-content">
                <div class="tab-pane fade show active" id="pre-laying-panel" role="tabpanel" 
                     aria-labelledby="pre-laying-tab">
                    <div class="checklist-panel-content" data-table="pre_laying_checklist">
                        <div class="loading-text">Loading Pre-Laying Checklist...</div>
                    </div>
                </div>
                
                <div class="tab-pane fade" id="during-laying-panel" role="tabpanel" 
                     aria-labelledby="during-laying-tab">
                    <div class="checklist-panel-content" data-table="during_laying_checklist">
                        <div class="loading-text">Loading During Laying Checklist...</div>
                    </div>
                </div>
                
                <div class="tab-pane fade" id="after-laying-panel" role="tabpanel" 
                     aria-labelledby="after-laying-tab">
                    <div class="checklist-panel-content" data-table="after_laying_checklist">
                        <div class="loading-text">Loading After Laying Checklist...</div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Insert tabbed interface
    container.before(tabbed_html);
    
    // Populate the tabs with checklist data
    setTimeout(function() {
        populate_checklist_tabs(frm);
    }, 500);
}


function hide_original_checklist_sections(frm) {
    /**
     * Hide the original checklist sections since we're replacing with tabs
     */
    const checklist_sections = [
        'section_break_pre_laying',
        'section_break_during_laying', 
        'section_break_after_laying'
    ];
    
    checklist_sections.forEach(function(section_name) {
        let section = frm.fields_dict[section_name];
        if (section && section.$wrapper) {
            section.$wrapper.hide();
            // Also hide all fields until next section
            section.$wrapper.nextUntil('.frappe-section').hide();
        }
    });
}

function populate_checklist_tabs(frm) {
    /**
     * Populate the tabbed interface with actual checklist data
     */
    
    const checklist_mappings = {
        'pre_laying_checklist': 'pre-laying-panel',
        'during_laying_checklist': 'during-laying-panel',
        'after_laying_checklist': 'after-laying-panel'
    };
    
    Object.keys(checklist_mappings).forEach(function(table_name) {
        let panel_id = checklist_mappings[table_name];
        let checklist_data = frm.doc[table_name] || [];
        
        render_checklist_cards(panel_id, table_name, checklist_data);
        update_tab_counter(table_name, checklist_data.length);
    });
}

function render_checklist_cards(panel_id, table_name, checklist_data) {
    /**
     * Render checklist items as interactive cards
     */
    
    let panel = $(`#${panel_id} .checklist-panel-content`);
    if (!panel.length) {
        console.log('Panel not found:', panel_id);
        return;
    }
    
    panel.empty();
    
    if (!checklist_data || checklist_data.length === 0) {
        panel.html(`
            <div class="empty-checklist">
                <p class="text-muted text-center" style="padding: 40px;">
                    <i class="fa fa-clipboard-list fa-3x" style="opacity: 0.3;"></i><br><br>
                    No checklist items available.<br>
                    <small>Items will populate automatically from master checklists.</small>
                </p>
            </div>
        `);
        return;
    }
    
    let cards_html = '<div class="checklist-cards-grid">';
    
    checklist_data.forEach(function(item, index) {
        let status_class = get_checklist_card_class(item.status);
        let status_icon = get_status_icon(item.status);
        
        cards_html += `
            <div class="checklist-card ${status_class}" data-item-idx="${index}" data-table="${table_name}">
                <div class="checklist-card-header">
                    <div class="checklist-title">
                        <strong>${item.checkpoint || 'Checkpoint'}</strong>
                        ${item.is_mandatory ? '<span class="badge badge-danger mandatory-badge">Mandatory</span>' : ''}
                    </div>
                    <div class="status-indicator ${item.status.toLowerCase()}">
                        <i class="fa ${status_icon}"></i> ${item.status}
                    </div>
                </div>
                
                <div class="checklist-card-body">
                    <p class="checklist-description">${item.description || 'No description available'}</p>
                    
                    <div class="checklist-actions">
                        <div class="status-buttons">
                            <button class="btn btn-sm btn-success status-btn ${item.status === 'Pass' ? 'active' : ''}" 
                                    onclick="updateChecklistStatus('${table_name}', ${index}, 'Pass')">
                                <i class="fa fa-check"></i> Pass
                            </button>
                            <button class="btn btn-sm btn-danger status-btn ${item.status === 'Fail' ? 'active' : ''}"
                                    onclick="updateChecklistStatus('${table_name}', ${index}, 'Fail')">
                                <i class="fa fa-times"></i> Fail
                            </button>
                            <button class="btn btn-sm btn-secondary status-btn ${item.status === 'N/A' ? 'active' : ''}"
                                    onclick="updateChecklistStatus('${table_name}', ${index}, 'N/A')">
                                <i class="fa fa-minus"></i> N/A
                            </button>
                        </div>
                        
                        <div class="action-buttons mt-2">
                            <button class="btn btn-sm btn-outline-primary" onclick="updateRemarks('${table_name}', ${index})">
                                <i class="fa fa-comment"></i> Remarks
                            </button>
                            <button class="btn btn-sm btn-outline-info" onclick="uploadPhoto('${table_name}', ${index})">
                                <i class="fa fa-camera"></i> Photo
                            </button>
                        </div>
                    </div>
                    
                    ${item.remarks ? `<div class="remarks-preview"><small><strong>Remarks:</strong> ${item.remarks}</small></div>` : ''}
                    ${item.photo_evidence ? `<div class="photo-preview"><small><i class="fa fa-image"></i> Photo attached</small></div>` : ''}
                    ${item.checked_by ? `<div class="checked-info"><small>Checked by ${item.checked_by} on ${item.checked_date ? frappe.datetime.str_to_user(item.checked_date) : ''}</small></div>` : ''}
                </div>
            </div>
        `;
    });
    
    cards_html += '</div>';
    panel.html(cards_html);
}

function get_checklist_card_class(status) {
    /**
     * Get CSS class for checklist card based on status
     */
    const classes = {
        'Pending': 'status-pending',
        'Pass': 'status-pass',
        'Fail': 'status-fail',
        'N/A': 'status-na'
    };
    return classes[status] || 'status-pending';
}

function get_status_icon(status) {
    /**
     * Get icon for checklist status
     */
    const icons = {
        'Pending': 'fa-clock',
        'Pass': 'fa-check-circle',
        'Fail': 'fa-times-circle',
        'N/A': 'fa-minus-circle'
    };
    return icons[status] || 'fa-question-circle';
}

function update_tab_counter(table_name, count) {
    /**
     * Update the counter badge on tabs
     */
    const counter_mappings = {
        'pre_laying_checklist': 'pre-laying-count',
        'during_laying_checklist': 'during-laying-count',
        'after_laying_checklist': 'after-laying-count'
    };
    
    let counter_id = counter_mappings[table_name];
    if (counter_id) {
        $(`#${counter_id}`).text(count);
    }
}

function add_custom_styles() {
    /**
     * Add custom CSS styles for enhanced UI
     */
    
    let styles = `
        <style>
        .checklist-tabs-container {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            overflow: hidden;
        }
        
        .checklist-nav-tabs {
            background: #fff;
            border-bottom: 1px solid #dee2e6;
        }
        
        .checklist-nav-tabs .nav-link {
            color: #495057;
            border: none;
            padding: 12px 20px;
        }
        
        .checklist-nav-tabs .nav-link:hover {
            background-color: #f8f9fa;
        }
        
        .checklist-nav-tabs .nav-link.active {
            background-color: #007bff;
            color: white;
            border: none;
        }
        
        .checklist-tab-content {
            padding: 20px;
        }
        
        .checklist-cards-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-top: 10px;
        }
        
        .checklist-card {
            border: 2px solid #dee2e6;
            border-radius: 8px;
            background: white;
            transition: all 0.3s ease;
        }
        
        .checklist-card:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }
        
        .checklist-card.status-pass {
            border-color: #28a745;
            background: linear-gradient(to right, #d4edda, #fff);
        }
        
        .checklist-card.status-fail {
            border-color: #dc3545;
            background: linear-gradient(to right, #f8d7da, #fff);
        }
        
        .checklist-card.status-na {
            border-color: #6c757d;
            background: linear-gradient(to right, #e2e3e5, #fff);
        }
        
        .checklist-card.status-pending {
            border-color: #ffc107;
            background: linear-gradient(to right, #fff3cd, #fff);
        }
        
        .checklist-card-header {
            padding: 15px;
            border-bottom: 1px solid #dee2e6;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .checklist-card-body {
            padding: 15px;
        }
        
        .status-indicator {
            font-weight: bold;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
        }
        
        .status-indicator.pass { background: #d4edda; color: #155724; }
        .status-indicator.fail { background: #f8d7da; color: #721c24; }
        .status-indicator.pending { background: #fff3cd; color: #856404; }
        .status-indicator.n\\/a { background: #e2e3e5; color: #383d41; }
        
        .status-buttons {
            display: flex;
            gap: 8px;
            margin-bottom: 10px;
        }
        
        .status-btn.active {
            transform: scale(1.05);
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }
        
        .action-buttons {
            display: flex;
            gap: 8px;
        }
        
        .mandatory-badge {
            font-size: 10px;
            margin-left: 8px;
        }
        
        
        .remarks-preview, .photo-preview, .checked-info {
            margin-top: 10px;
            padding: 8px;
            background: #f8f9fa;
            border-radius: 4px;
            border-left: 3px solid #007bff;
        }
        
        /* Enhanced UI styles */
        .enhanced-checklist-table {
            border: 1px solid #dee2e6;
            border-radius: 8px;
            overflow: hidden;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .enhanced-checklist-table .section-head {
            background: linear-gradient(to right, #f8f9fa, #e9ecef);
            padding: 12px 20px;
            border-bottom: 1px solid #dee2e6;
            font-weight: 600;
        }
        
        .checklist-grid-enhanced .grid-row {
            border-bottom: 1px solid #f0f0f0;
            transition: background-color 0.2s ease;
        }
        
        .checklist-grid-enhanced .grid-row:hover {
            background-color: #f8f9fa;
        }
        
        
        .checklist-quick-actions {
            background: #f8f9fa !important;
            border-bottom: 1px solid #dee2e6 !important;
        }
        
        .checklist-quick-actions .btn {
            margin-right: 8px;
        }
        
        
        /* Grid enhancements */
        .checklist-grid-enhanced .grid-body .rows {
            max-height: 400px;
            overflow-y: auto;
        }
        
        .checklist-grid-enhanced .grid-row[data-idx] {
            border-left: 4px solid transparent;
        }
        
        .checklist-grid-enhanced .grid-row[data-idx]:hover {
            border-left-color: #007bff;
        }
        
        /* Status indicators in grid */
        .grid-row .col[data-fieldname="status"] {
            font-weight: 600;
        }
        
        .grid-row .col[data-fieldname="status"][data-value="Pass"] {
            background: rgba(40, 167, 69, 0.1);
            color: #28a745;
        }
        
        .grid-row .col[data-fieldname="status"][data-value="Fail"] {
            background: rgba(220, 53, 69, 0.1);
            color: #dc3545;
        }
        
        .grid-row .col[data-fieldname="status"][data-value="Pending"] {
            background: rgba(255, 193, 7, 0.1);
            color: #856404;
        }
        
        .grid-row .col[data-fieldname="status"][data-value="N/A"] {
            background: rgba(108, 117, 125, 0.1);
            color: #6c757d;
        }
        </style>
    `;
    
    if (!$('#checklist-custom-styles').length) {
        $('head').append(styles);
        $('head').append('<style id="checklist-custom-styles"></style>');
    }
}

// Global functions for checklist interactions
window.updateChecklistStatus = function(table_name, item_index, new_status) {
    let frm = cur_frm;
    if (!frm || !frm.doc[table_name] || !frm.doc[table_name][item_index]) return;
    
    let item = frm.doc[table_name][item_index];
    
    // Update the status
    frappe.model.set_value(item.doctype, item.name, 'status', new_status);
    
    // Set checked by and date
    frappe.model.set_value(item.doctype, item.name, 'checked_by', frappe.session.user);
    frappe.model.set_value(item.doctype, item.name, 'checked_date', frappe.datetime.now_datetime());
    
    // Refresh the UI
    setTimeout(function() {
        populate_checklist_tabs(frm);
        calculate_progress(frm);
    }, 300);
    
    frappe.show_alert({
        message: __('Status updated to {0}', [new_status]),
        indicator: 'green'
    });
};

window.updateRemarks = function(table_name, item_index) {
    let frm = cur_frm;
    if (!frm || !frm.doc[table_name] || !frm.doc[table_name][item_index]) return;
    
    let item = frm.doc[table_name][item_index];
    
    frappe.prompt([{
        fieldname: 'remarks',
        fieldtype: 'Long Text',
        label: __('Remarks'),
        default: item.remarks || ''
    }], function(values) {
        frappe.model.set_value(item.doctype, item.name, 'remarks', values.remarks);
        
        setTimeout(function() {
            populate_checklist_tabs(frm);
        }, 300);
        
        frappe.show_alert({
            message: __('Remarks updated'),
            indicator: 'green'
        });
    }, __('Update Remarks'));
};

window.uploadPhoto = function(table_name, item_index) {
    let frm = cur_frm;
    if (!frm || !frm.doc[table_name] || !frm.doc[table_name][item_index]) return;
    
    let item = frm.doc[table_name][item_index];
    
    new frappe.ui.FileUploader({
        doctype: item.doctype,
        docname: item.name,
        fieldname: 'photo_evidence',
        callback: function(attachment) {
            frappe.model.set_value(item.doctype, item.name, 'photo_evidence', attachment.file_url);
            
            setTimeout(function() {
                populate_checklist_tabs(frm);
            }, 300);
            
            frappe.show_alert({
                message: __('Photo uploaded successfully'),
                indicator: 'green'
            });
        }
    });
};

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
        if (frm.fields_dict[table_field]) {
            frm.fields_dict[table_field].grid.get_field('status').get_query = function() {
                return {
                    filters: [
                        ['name', 'in', ['Pending', 'Pass', 'Fail', 'N/A']]
                    ]
                };
            };
        }
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
    console.log(`🔄 Starting bulk update for ${table_field} to status: ${status}`);
    console.log(`📊 Current data for ${table_field}:`, frm.doc[table_field]);
    
    if (!frm.doc[table_field] || frm.doc[table_field].length === 0) {
        frappe.msgprint({
            title: __('No Items'),
            message: __('No checklist items found to update.'),
            indicator: 'orange'
        });
        return;
    }
    
    let pending_items = frm.doc[table_field].filter(item => item.status === 'Pending');
    console.log(`📋 Found ${pending_items.length} pending items out of ${frm.doc[table_field].length} total`);
    
    if (pending_items.length === 0) {
        frappe.msgprint({
            title: __('No Pending Items'),
            message: __('No pending items found to update.'),
            indicator: 'orange'
        });
        return;
    }
    
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
            label: __('Confirm bulk update of {0} items', [pending_items.length]),
            reqd: 1
        }
    ], function(values) {
        console.log('📝 User confirmed bulk update with values:', values);
        
        if (values.confirm) {
            let updated_count = 0;
            
            // Update all pending items in the specified table
            frm.doc[table_field].forEach(function(item, index) {
                if (item.status === 'Pending') {
                    console.log(`🔄 Updating item ${index}: ${item.checkpoint} from ${item.status} to ${status}`);
                    
                    try {
                        frappe.model.set_value(item.doctype, item.name, 'status', status);
                        if (values.remarks) {
                            frappe.model.set_value(item.doctype, item.name, 'remarks', values.remarks);
                        }
                        frappe.model.set_value(item.doctype, item.name, 'checked_by', frappe.session.user);
                        frappe.model.set_value(item.doctype, item.name, 'checked_date', frappe.datetime.now_datetime());
                        updated_count++;
                        console.log(`✅ Updated item ${index} successfully`);
                    } catch (error) {
                        console.error(`❌ Error updating item ${index}:`, error);
                    }
                }
            });
            
            console.log(`🎯 Updated ${updated_count} items, refreshing form...`);
            
            // Refresh the form fields
            frm.refresh_field(table_field);
            frm.refresh_fields();
            
            // Also try to refresh the specific grid
            if (frm.fields_dict[table_field] && frm.fields_dict[table_field].grid) {
                frm.fields_dict[table_field].grid.refresh();
            }
            
            // Update progress
            setTimeout(function() {
                calculate_progress(frm);
            }, 1000);
            
            frappe.show_alert({
                message: __('Bulk update completed - {0} items updated to {1}', [updated_count, status]),
                indicator: 'green'
            });
            
            console.log(`✅ Bulk update completed for ${table_field}`);
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
            populate_checklist_tabs(frm);
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