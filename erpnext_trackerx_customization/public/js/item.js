frappe.ui.form.on('Item', {

    onload: function(frm) {
        console.log("Item form loaded."); // Debugging log

        // --- Auto-add row to 'components' child table on new Item creation ---
        if (frm.is_new()) {
            console.log("New Item document created. Adding default row to 'components' child table.");
            let new_component_row = frm.add_child('custom_fg_components'); // 'components' is the fieldname of your child table
            new_component_row.component_name = frm.doc.item_name; // Set child field from parent's item_name
            new_component_row.tracking_required=true;
            frm.refresh_field('custom_fg_components'); // Refresh the child table grid to show the new row
        }

        
    },

    custom_fg_components: function(frm) {
        console.log("Changed child table")
    },

    item_name: function(frm) {
        
        // This will update the component_name in the first row if item_name changes
        // after the initial load, or if the user types in item_name first.
        if (frm.doc.custom_fg_components && frm.doc.custom_fg_components.length > 0) {
            frm.doc.custom_fg_components[0].component_name = frm.doc.item_name;
            frm.refresh_field('custom_fg_components');
            console.log("Component name updated in child table from Item Name.");
        }
    },

    refresh: function(frm) {


        
        
        

        // Always remove stray dropdowns first
        $('#custom-master-type-select').remove();

        // Hide in-form field always
        if (frm.fields_dict.custom_select_master) {
            frm.toggle_display('custom_select_master', false);
        }

        // Show dropdown only when creating new Item
        if (frm.is_new()) {
            insertDropdownInHeading(frm, getMasterOptions(frm));
            $('#custom-master-type-select').show().prop('disabled', false);
        } else {
            $('#custom-master-type-select').remove();
        }

        setTimeout(function() {
            updateItemLabels(frm);
        }, 300);

        filterCustomSelectMasterOptionsBasedOnRole(frm);
        
        // --- New Logic: Filter 'construction_type' Link field ---
        // This function will be called on refresh and when custom_select_master changes
        setConstructionTypeFilter(frm);

        setTimeout(() => {
            frm.fields_dict.custom_fg_components.grid.wrapper
                .on('click', '.grid-remove-rows', function (e) {
                    const grid = frm.fields_dict.custom_fg_components.grid;
                    const selected = grid.get_selected();

                    if (selected && selected.length > 0) {
                        const firstRowName = grid.grid_rows[0]?.doc.name;
                        if (selected.includes(firstRowName)) {
                            frappe.msgprint(__('FG cannot be deleted'));
                            // Stop bubbling
                            setTimeout(()=>{
                                let new_component_row = frm.add_child('custom_fg_components'); // 'components' is the fieldname of your child table
                                new_component_row.component_name = frm.doc.item_name; 
                                new_component_row.tracking_required=true;
                                // Set child field from parent's item_name
                                frm.refresh_field('custom_fg_components'); 
                            },100)
                                            // Explicit cancel
                        }
                    }
                });
        }, 100);

        

        setItemGroupFilter(frm);

        

    },
    custom_select_master: function(frm) {
        updateItemLabels(frm);
        $('#custom-master-type-select').val(frm.doc.custom_select_master);
        
        // --- New Logic: Filter 'construction_type' Link field ---
        // This function will be called on refresh and when custom_select_master changes
        setConstructionTypeFilter(frm);
        setItemGroupFilter(frm);
    },
    
    
    
});

// Helper function to set the filter for 'construction_type'
function setConstructionTypeFilter(frm) {
    frm.set_query('custom_construction_type_link', function() {
        const selectedMasterValue = frm.doc.custom_select_master;
        console.log("Filtering Construction Type by custom_select_master:", selectedMasterValue);

        if (selectedMasterValue) {
            return {
                filters: {
                    // Filter Construction Type documents where 'item_group' matches 'selectedMasterValue'
                    'item_type': selectedMasterValue
                }
            };
        } else {
            // If custom_select_master is empty, show no options to prevent incorrect selections
            return { filters: { 'name': '_NO_MATCH_' } };
            // Alternatively, to show all options if custom_select_master is empty:
            // return { filters: {} };
        }
    });
    console.log("Filter applied to construction_type field based on custom_select_master.");
}

// --- Utility: Get options directly from the DocField ---
function getMasterOptions(frm) {
    if (frm.fields_dict.custom_select_master) {
        return frm.fields_dict.custom_select_master.df.options
            .split('\n').map(opt => opt.trim()).filter(opt => opt);
    }
    return [];
}

// --- Utility: Inject dropdown in the page header with CSS for mobile ---
function insertDropdownInHeading(frm, options) {
    $('#custom-master-type-select').remove();
    if (!options || options.length === 0) return;
    const current = frm.doc.custom_select_master || options[0];

    // Add custom style (only once)
    if (!$('#custom-master-type-css').length) {
        $('head').append(`
            <style id="custom-master-type-css">
                #custom-master-type-select {
                    z-index: 1051 !important;
                }
                @media (max-width: 575px) {
                    #custom-master-type-select {
                        width: 110px !important;
                    }
                }
            </style>
        `);
    }

    let html = `<select id="custom-master-type-select" class="form-control"
        style="
            width: 150px; 
            min-width: 110px;
            max-width: 45vw;
            z-index: 1051; 
        ">`
        + options.map(opt => `<option value="${opt}"${opt === current ? ' selected' : ''}>${opt}</option>`).join('')
        + `</select>`;

    $('.page-title .title-area').append(html);

    $('#custom-master-type-select').on('change', function() {
        let val = $(this).val();
        if (val && val !== frm.doc.custom_select_master) {
            frm.set_value('custom_select_master', val);
        }
    });
}

// --- Label Update Logic (only change heading in new mode) ---
function updateItemLabels(frm) {
    let masterLabel = ( $('#custom-master-type-select').val() || frm.doc.custom_select_master || "Item").trim();
    let wordBoundaryRegex = /\bItem\b/gi;

    // 1. For normal fields (control-label)
    $('.frappe-control').each(function() {
        let fieldname = $(this).attr('data-fieldname');
        if (!fieldname || fieldname === 'custom_select_master') return;
        let $label = $(this).find('label.control-label');
        if ($label.length) {
            let orig = $label.attr('data-orig-label');
            if (!orig) {
                orig = $label.text();
                $label.attr('data-orig-label', orig);
            }
            let updated = orig;
            if (masterLabel !== "Item") {
                updated = orig.replace(wordBoundaryRegex, masterLabel);
            }
            $label.text(updated);
        }
    });

    // 2. For checkboxes (label-area span)
    $('.frappe-control .label-area').each(function() {
        let $span = $(this);
        let orig = $span.attr('data-orig-label');
        if (!orig) {
            orig = $span.text();
            $span.attr('data-orig-label', orig);
        }
        let updated = orig;
        if (masterLabel !== "Item") {
            updated = orig.replace(wordBoundaryRegex, masterLabel);
        }
        $span.text(updated);
    });

    // 3. Section headings (Section Breaks)
    $('.form-section .section-head').each(function() {
        let $sec = $(this);
        let orig = $sec.attr('data-orig-title');
        if (!orig) {
            orig = $sec.text();
            $sec.attr('data-orig-title', orig);
        }
        let updated = orig;
        if (masterLabel !== "Item") {
            updated = orig.replace(wordBoundaryRegex, masterLabel);
        }
        $sec.text(updated);
    });

    // 4. Main form title (only if new)
    if (frm.is_new()) {
        $('.title-text').each(function() {
            let $title = $(this);
            let orig = $title.attr('data-orig-title');
            if (!orig) {
                orig = $title.text();
                $title.attr('data-orig-title', orig);
            }
            let updated = orig;
            if (masterLabel !== "Item") {
                updated = orig.replace(wordBoundaryRegex, masterLabel);
            }
            $title.text(updated);
        });
    }
}

// --- SPA safety: Remove injected dropdown on route change ---
frappe.router.on('change', () => {
    $('#custom-master-type-select').remove();
});

function setItemGroupFilter(frm) {
    const master = frm.doc.custom_select_master;

    const root_mapping = {
        "Style": "Finished Goods",
        "Fabrics": "Fabrics",
        "Trims": "Trims",
        "Accessories": "Accessories",
        "Machine": "Machine"
    };

    const root_group = root_mapping[master];

    if (!root_group) {
        frm.set_query('item_group', () => ({ filters: {} }));
        return;
    }

    frm.set_query('item_group', () => {
        return {
            filters: {
                'name': ['descendants of (inclusive)', root_group]
            }
        };
    });

    console.log(`Applied item_group filter: descendants of (inclusive) '${root_group}'`);
}




function filterCustomSelectMasterOptionsBasedOnRole(frm) {
    const role_map = {
        "Style": [
            "Finished Goods Manager", "Finished Goods", "FG Manager", "Finished Goods User", "FG User",
            "FG Supervisor", "Finished Goods Supervisor", "Style Master", "Style User",
            "Style Manager", "Style Master Manager"
        ],
        "Fabrics": [
            "Fabrics Manager", "Fabrics", "Fabrics Supervisor", "Fabrics User",
            "Fabric Manager", "Fabric", "Fabric Supervisor", "Fabric User"
        ],
        "Trims": [
            "Trims Manager", "Trims", "Trims Supervisor", "Trims User"
        ],
        "Accessories": [
            "Accessories Manager", "Accessories", "Accessories Supervisor", "Accessories User"
        ],
        "Machine": [
            "Machine Manager", "Machine", "Machine User", "Machine Supervisor"
        ]
    };

    frappe.roles = frappe.roles || [];

    // Always show full list for privileged users
    if (frappe.user_roles.includes("Administrator") || frappe.user_roles.includes("System Manager")) {
      
        return;
    }

    // Find allowed options
    const allowed_options = [];
    for (let option in role_map) {
        const roles = role_map[option];
        if (roles.some(role => frappe.user_roles.includes(role))) {
            allowed_options.push(option);
        }
    }

    if (allowed_options.length > 0) {
        updateInjectedDropdown(allowed_options);
    } else {
        // No match: show all
     
    }

    updateItemLabels(frm);
    
    
}

function updateInjectedDropdown(options) {
    const $dropdown = $('#custom-master-type-select');
    const $dropdownOld = $('#custom_select_master');


    if (!$dropdown.length) return;

    const currentVal = $dropdown.val();

    let html = options.map(opt => {
        const selected = (opt === currentVal) ? ' selected' : '';
        return `<option value="${opt}"${selected}>${opt}</option>`;
    }).join('');

    $dropdown.html(html);
}