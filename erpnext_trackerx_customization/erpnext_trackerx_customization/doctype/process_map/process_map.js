frappe.ui.form.on("Process Map", {
    onload: function(frm) {
        // Set form properties and filters
        setup_style_group_filters(frm);

        if (frm.is_new()) {
            // Redirect to process map builder for new documents
            frappe.set_route("process-map-builder");
        }
    },

    refresh: function(frm) {
        // Set up form actions and styling
        setup_process_map_form(frm);
    },

    style_group: function(frm) {
        // When style group changes, update related fields
        if (frm.doc.style_group) {
            update_style_group_info(frm);
        }
    },

    edit_map_button: function(frm) {
        const mapName = frm.doc.map_name;
        const mapNumber = frm.doc.process_map_number;
        const styleGroup = frm.doc.style_group;

        if (!mapName || !mapNumber || !styleGroup) {
            frappe.msgprint({
                title: __('Missing Information'),
                message: __('Map name, process map number, and style group are required!'),
                indicator: 'red'
            });
            return;
        }

        // Construct dynamic URL with style group context
        const baseUrl = window.location.origin + "/app/process-map-builder/";
        const encodedStyleGroup = encodeURIComponent(styleGroup);
        const encodedMapName = encodeURIComponent(mapName);
        const encodedMapNumber = encodeURIComponent(mapNumber);

        const url = `${baseUrl}?style_group=${encodedStyleGroup}&map_name=${encodedMapName}&map_number=${encodedMapNumber}`;

        // Open process map builder in new tab
        window.open(url, "_blank");
    }
});

// Helper Functions
function setup_style_group_filters(frm) {
    // Set filter for Style Group field to show only active style groups
    frm.set_query('style_group', function() {
        return {
            filters: {
                // Add any specific filters if needed
            }
        };
    });
}

function setup_process_map_form(frm) {
    try {
        // Add custom styling if form is loaded
        if (!frm.is_new()) {
            // Add custom buttons or styling here if needed
            add_process_map_actions(frm);
        }

        // Make certain fields read-only based on status
        if (frm.doc.docstatus === 1) {
            frm.set_df_property('style_group', 'read_only', 1);
            frm.set_df_property('map_name', 'read_only', 1);
            frm.set_df_property('process_map_number', 'read_only', 1);
        }
    } catch (e) {
        console.error('Error in setup_process_map_form:', e);
    }
}

function update_style_group_info(frm) {
    // Auto-populate style group related fields
    if (frm.doc.style_group) {
        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Style Group',
                name: frm.doc.style_group
            },
            callback: function(r) {
                if (r.message) {
                    // Fields will auto-populate via fetch_from, but we can add custom logic here
                    console.log('Style Group loaded:', r.message.name);
                }
            }
        });
    }
}

function add_process_map_actions(frm) {
    // Add custom actions for process map
    if (frm.doc.style_group && !frm.is_new()) {
        frm.add_custom_button(__('View Style Group'), function() {
            frappe.set_route('Form', 'Style Group', frm.doc.style_group);
        }, __('Style Group'));

        frm.add_custom_button(__('Other Process Maps'), function() {
            frappe.set_route('List', 'Process Map', {
                'style_group': frm.doc.style_group
            });
        }, __('Style Group'));
    }
}
