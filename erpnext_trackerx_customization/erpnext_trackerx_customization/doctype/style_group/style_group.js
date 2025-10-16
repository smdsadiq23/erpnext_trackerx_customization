// Copyright (c) 2025, CognitionX and contributors
// For license information, please see license.txt

frappe.ui.form.on('Style Group', {
    onload: function(frm) {
        // Set auto-company selection on form load
        set_default_company(frm);

        // Set form properties
        frm.set_df_property('description', 'reqd', 0);
    },

    refresh: function(frm) {
        // Set custom buttons and form properties
        setup_form_layout(frm);

        // Auto-set company if not already set
        if (!frm.doc.company) {
            set_default_company(frm);
        }

        // Set filters for company field
        set_company_filter(frm);

        // Setup process map integration
        setup_process_map_integration(frm);
    },

    company: function(frm) {
        // Actions when company changes
        if (frm.doc.company) {
            // You can add company-specific logic here
            console.log('Company changed to:', frm.doc.company);
        }
    },

});

// Process Map Integration Helper Functions

function setup_process_map_integration(frm) {
    /**
     * Setup Process Map integration buttons and functionality
     */
    if (!frm.is_new() && frm.doc.name) {
        // Add Process Map button group
        frm.add_custom_button(__('Create Process Map'), function() {
            create_style_group_process_map(frm);
        }, __('Process Map'));

        frm.add_custom_button(__('View Process Maps'), function() {
            view_style_group_process_maps(frm);
        }, __('Process Map'));

        // Load and display process map count
        load_process_map_count(frm);
    }
}

function create_style_group_process_map(frm) {
    /**
     * Redirect to Process Map Builder with style group pre-selected
     */
    if (!frm.doc.name) {
        frappe.msgprint({
            title: __('Style Group Required'),
            message: __('Please save the Style Group first before creating a process map'),
            indicator: 'yellow'
        });
        return;
    }

    // Redirect directly to Process Map Builder with style group in URL
    const baseUrl = window.location.origin + "/app/process-map-builder/";
    const url = `${baseUrl}?style_group=${encodeURIComponent(frm.doc.name)}`;

    // Show a brief message and redirect
    frappe.show_alert({
        message: __('Opening Process Map Builder for {0}', [frm.doc.name]),
        indicator: 'blue'
    });

    // Open in new tab
    window.open(url, '_blank');
}

function view_style_group_process_maps(frm) {
    /**
     * View all process maps for this style group
     */
    if (!frm.doc.name) {
        frappe.msgprint(__('Style Group not found'));
        return;
    }

    // Navigate to Process Map list filtered by style group
    frappe.set_route('List', 'Process Map', {
        'style_group': frm.doc.name
    });
}

function load_process_map_count(frm) {
    /**
     * Load and display process map count for this style group
     */
    if (!frm.doc.name) return;

    frappe.call({
        method: 'erpnext_trackerx_customization.api.process_map.get_style_group_process_maps',
        args: {
            style_group_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                const count = r.message.total || 0;

                // Update button label with count
                if (count > 0) {
                    // Check if button structure exists before updating
                    if (frm.custom_buttons &&
                        frm.custom_buttons[__('Process Map')] &&
                        frm.custom_buttons[__('Process Map')][__('View Process Maps')]) {
                        frm.custom_buttons[__('Process Map')][__('View Process Maps')].html(
                            __('View Process Maps ({0})', [count])
                        );
                    }

                    // Add info to form
                    if (!frm.process_map_info_added && frm.dashboard) {
                        frm.dashboard.add_indicator(__('Process Maps: {0}', [count]), 'blue');
                        frm.process_map_info_added = true;
                    }
                }
            }
        }
    });
}

// Child table events for Style Group Component
frappe.ui.form.on('Style Group Component', {
    component_name: function(frm, cdt, cdn) {
        try {
            var row = locals[cdt][cdn];
            if (row.component_name) {
                // Format component name to title case
                row.component_name = row.component_name.toUpperCase();
                frm.refresh_field('components');
            }
        } catch (e) {
            console.error('Error in component_name:', e);
        }
    },

    components_add: function(frm) {
        // Set focus to component name when new row is added
        try {
            setTimeout(() => {
                var grid = frm.get_field('components').grid;
                if (grid.grid_rows.length > 0) {
                    var last_row = grid.grid_rows[grid.grid_rows.length - 1];
                    last_row.columns.component_name.df.focus = true;
                }
            }, 100);
        } catch (e) {
            console.error('Error in components_add:', e);
        }
    }
});

// Helper Functions

function set_default_company(frm) {
    /**
     * Set default company for the user
     */
    if (!frm.doc.company && !frm.is_new()) {
        return; // Don't auto-set on existing documents
    }

    if (!frm.doc.company) {
        // Get user's default company
        frappe.call({
            method: 'frappe.defaults.get_user_default',
            args: {
                key: 'Company'
            },
            callback: function(r) {
                if (r.message) {
                    frm.set_value('company', r.message);
                } else {
                    // Get global default company if user default not set
                    frappe.call({
                        method: 'frappe.client.get_single',
                        args: {
                            doctype: 'Global Defaults'
                        },
                        callback: function(r) {
                            if (r.message && r.message.default_company) {
                                frm.set_value('company', r.message.default_company);
                            }
                        }
                    });
                }
            }
        });
    }
}

function set_company_filter(frm) {
    /**
     * Set filters for company field to show only non-group companies
     */
    frm.set_query('company', function() {
        return {
            filters: {
                'is_group': 0  // Show only leaf companies, not group companies
            }
        };
    });
}


function setup_form_layout(frm) {
    /**
     * Setup form layout and custom styling
     */
    try {
        // Add custom CSS for better form appearance
        if (!document.getElementById('style-group-custom-css')) {
            var style = document.createElement('style');
            style.id = 'style-group-custom-css';
            style.textContent = `
                .form-section .section-head {
                    background: #f8f9fa;
                    padding: 8px 15px;
                    border-left: 3px solid #007bff;
                    margin: 0 -15px 15px -15px;
                    font-weight: 600;
                    color: #495057;
                }

                .style-group-image img {
                    max-width: 200px;
                    max-height: 200px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }

                .components-table .grid-row {
                    border-left: 3px solid #28a745;
                }
            `;
            document.head.appendChild(style);
        }

        // Show/hide fields based on permissions and form state
        if (frm.is_new()) {
            frm.set_df_property('company', 'read_only', 0);
        }

    } catch (e) {
        console.error('Error in setup_form_layout:', e);
    }
}