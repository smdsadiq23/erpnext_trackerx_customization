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
    },

    company: function(frm) {
        // Actions when company changes
        if (frm.doc.company) {
            // You can add company-specific logic here
            console.log('Company changed to:', frm.doc.company);
        }
    },

    style_group_number: function(frm) {
        // Validate style group number format
        if (frm.doc.style_group_number) {
            validate_style_group_number(frm);
        }
    },

    name: function(frm) {
        // Auto-generate style group number based on name if not set
        if (frm.doc.name && !frm.doc.style_group_number) {
            auto_generate_style_group_number(frm);
        }
    }
});

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

    components_add: function(frm, cdt, cdn) {
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
     * Set filters for company field to show only active companies
     */
    frm.set_query('company', function() {
        return {
            filters: {
                'disabled': 0
            }
        };
    });
}

function validate_style_group_number(frm) {
    /**
     * Validate style group number format and uniqueness
     */
    if (!frm.doc.style_group_number) {
        return;
    }

    // Remove extra spaces
    frm.set_value('style_group_number', frm.doc.style_group_number.trim().toUpperCase());

    // Check for uniqueness
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Style Group',
            filters: {
                'style_group_number': frm.doc.style_group_number,
                'name': ['!=', frm.doc.name || 'new']
            },
            fields: ['name']
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                frappe.msgprint({
                    title: __('Duplicate Style Group Number'),
                    message: __('Style Group Number {0} already exists in {1}',
                        [frm.doc.style_group_number, r.message[0].name]),
                    indicator: 'red'
                });
                frm.set_focus('style_group_number');
            }
        }
    });
}

function auto_generate_style_group_number(frm) {
    /**
     * Auto-generate style group number based on name and company
     */
    if (!frm.doc.name || !frm.doc.company) {
        return;
    }

    // Get company abbreviation
    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Company',
            filters: {'name': frm.doc.company},
            fieldname: 'abbr'
        },
        callback: function(r) {
            if (r.message) {
                var company_abbr = r.message.abbr || frm.doc.company.substring(0, 3).toUpperCase();
                var name_prefix = frm.doc.name.substring(0, 5).toUpperCase().replace(/[^A-Z0-9]/g, '');
                var timestamp = new Date().getTime().toString().slice(-4);

                var suggested_number = company_abbr + '-' + name_prefix + '-' + timestamp;

                frappe.msgprint({
                    title: __('Suggested Style Group Number'),
                    message: __('Suggested Style Group Number: {0}', [suggested_number]),
                    indicator: 'blue'
                });

                frm.set_value('style_group_number', suggested_number);
            }
        }
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