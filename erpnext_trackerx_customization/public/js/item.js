frappe.ui.form.on('Item', {

    onload: function(frm) {

        console.log("Item form loaded."); // Debugging log

        setItemMasterOptions(frm);
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

        // Add "Copy from Style Master" button to custom_bom_operations grid
        if (frm.fields_dict.custom_bom_operations) {
            if (!frm.custom_bom_operations_button_added) {
                const grid = frm.fields_dict.custom_bom_operations.grid;
                if (grid) {
                    grid.add_custom_button(
                        __('Copy from Style Master'),
                        function () {
                            if (!frm.doc.custom_style_master) {
                                frappe.msgprint(__('Please select a Style Master first'));
                                return;
                            }

                            frappe.confirm(
                                __('This will clear all existing operations and copy from selected Style Master. Continue?'),
                                () => {
                                    // Clear operations
                                    frm.clear_table('custom_bom_operations');
                                    frm.refresh_field('custom_bom_operations');

                                    // Copy from Style Master
                                    copy_operations_from_style_master(frm);
                                }
                            );
                        },
                        __('Actions')
                    );

                    frm.custom_bom_operations_button_added = true;
                }
            }
        }     
           
        setTimeout(function() {
            updateItemLabels(frm);
        }, 300);

        filterCustomSelectMasterOptionsBasedOnRole(frm);
        
        setConstructionTypeFilter(frm);        

        setItemGroupFilter(frm);

        setFieldsToReadyOnly(frm);

        setMeasurementUploadAttachExtensionRestriction(frm);


        setTimeout(function() {
            setItemNameAndItemNumberProps(frm);
        }, 500);

    },
    custom_select_master: function(frm) {
        setTimeout(function() {
            updateItemLabels(frm);
            setDefaultUOM(frm);        
        }, 300);
        $('#custom-master-type-select').val(frm.doc.custom_select_master);
        
        // --- New Logic: Filter 'construction_type' Link field ---
        // This function will be called on refresh and when custom_select_master changes
        setConstructionTypeFilter(frm);
        setItemGroupFilter(frm);
        setItemNameAndItemNumberProps(frm);
        
    },

    custom_style_master: function(frm) {
        if(frm.doc.custom_style_master)
        {
            copy_operations_from_style_master(frm);
        }
    },

    custom_manual_item_code: function(frm) {
        toggle_item_code_behavior(frm);
    }       
});

function toggle_item_code_behavior(frm) {
    const is_manual = cint(frm.doc.custom_manual_item_code);

    if (is_manual) {
        frm.toggle_display('item_code', true);
        frm.set_df_property('item_code', 'read_only', 0);
        // frm.toggle_reqd('item_code', true);
        // Optional: change label
        frm.set_value('item_code', '');
    } else {
        frm.toggle_display('item_code', false);
        frm.set_df_property('item_code', 'read_only', 1);
        // Reset label to default
        frm.set_value('item_code', 'Item Code');        
    }

    frm.refresh_field('item_code');
}

function populate_measurement_table_sample_data(frm) {
    // Only proceed if both fields are selected
    if (frm.doc.custom_size_filter && frm.doc.custom_size_standard) {
        
        // Clear existing rows in the child table
        frm.clear_table('item_measurement_chart');

        frappe.call({
            method: "erpnext_trackerx_customization.utils.measurement_data_importer.get_measurement_data",
            args: {
                custom_size_filter: frm.doc.custom_size_filter,
                custom_size_standard: frm.doc.custom_size_standard
            },
            callback: function(r) {
                if (r.message && r.message.length) {
                    r.message.forEach(row => {
                        // Add each row to the child table
                        let new_row = frm.add_child('item_measurement_chart');
                        new_row.type = row.type;
                        new_row.measurement_point = row.measurement_point;
                        new_row.size = row.size;
                        new_row.value = row.value;
                        new_row.tolerance = row.tolerance;
                    });
                    frm.refresh_field('item_measurement_chart');
                } else {
                    frappe.msgprint("No measurement data found for the selected combination.");
                }
            }
        });
    }
}

function setMeasurementUploadAttachExtensionRestriction(frm) {
    const attach_field = frm.fields_dict['custom_attach_measurement_chart'];
        attach_field.on_attach_click = function() {
            attach_field.set_upload_options();
            attach_field.upload_options.restrictions.allowed_file_types = [
                "application/pdf",
                "image/jpeg",
                "image/png",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "application/vnd.ms-excel"
            ];
            attach_field.file_uploader = new frappe.ui.FileUploader(attach_field.upload_options);
        };
}

function setItemNameAndItemNumberProps(frm){
    let read_only_value = 1;
    const reqd_value = 1;
        if(frm.doc.custom_select_master != 'Finished Goods'){
            read_only_value = 0;
        }
        else{
            read_only_value = 1;
        }
        frm.set_df_property("item_name", "read_only", read_only_value);
        frm.set_df_property("custom_item_number", "read_only", read_only_value);
        frm.refresh_field("item_name");
        frm.refresh_field("custom_item_number");
        frm.set_df_property("custom_preferred_supplier", "reqd", reqd_value);
        frm.refresh_field("custom_preferred_supplier");        
}

function setFieldsToReadyOnly(frm) {
    if (!frm.is_new()) {
            const locked_fields = [
                "custom_select_master",
                "item_group",
                "item_name",
                "custom_colour_name",
                "custom_colour_code",
                "custom_item_number",
                "custom_style_master"
            ]

            locked_fields.forEach(field => {
                frm.set_df_property(field, "read_only", 1);
            });
        }
}

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
            frm.refresh_field('custom_select_master');
        }
    });
}

// --- Label Update Logic (only change heading in new mode) ---
function updateItemLabels(frm) {
    let masterLabel = ( $('#custom-master-type-select').val() || frm.doc.custom_select_master || "Item").trim();
    let wordBoundaryRegex = /\bItem\b/gi;

    isMachineOrSpareParts = ['Machines', 'Spare Parts'].includes(masterLabel);


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
            if (isMachineOrSpareParts && fieldname === 'item_group'){
                $label.text('Item Group');
            }
            else{
                $label.text(updated);
            }
            
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

    machinesAndSparePartsChanges(frm);
    
}

// --- SPA safety: Remove injected dropdown on route change ---
frappe.router.on('change', () => {
    $('#custom-master-type-select').remove();
});

function machinesAndSparePartsChanges(frm)
{
    isMachineOrSpareParts = ['Machines', 'Spare Parts'].includes(frm.doc.custom_select_master);

    if(isMachineOrSpareParts){
        frm.set_df_property('item_group', 'label', 'Item Group');
        frm.toggle_reqd("item_name", false);
        frm.set_df_property('item_name', 'hidden', true);
        
        frm.refresh_field('item_group');
        frm.refresh_field('item_name');
    }
    else{
        frm.toggle_reqd("item_name", true);
        frm.set_df_property('item_name', 'hidden', false);
        
        frm.refresh_field('item_name');
    }
}

function setItemGroupFilter(frm) {
    const master = frm.doc.custom_select_master;

    const root_mapping = frappe.boot.item_constants.item_master_item_group_filter;

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

function setDefaultUOM(frm) {
    console.log("reached here")
    if (!frm.is_new()) return; // Only for new items

    const master = frm.doc.custom_select_master;
    const uomMap = frappe.boot.item_constants?.item_master_uom_defaults || {
        "Finished Goods": "Nos",
        "Fabrics": "Meter",
        "Trims": "Meter",
        "Yarns": "Kg",
        "Accessories": "Nos",
        "Labels": "Nos",
        "Packing Materials": "Nos",
        "Semi Finished Goods": "Nos",
        "Spare Parts": "Nos",
        "Machines": "Nos"
    };

    const defaultUOM = uomMap[master];
    if (defaultUOM) {
        // Set stock_uom (standard field for Item)
        frm.set_value('stock_uom', defaultUOM);
        // Optional: make it read-only after setting
        //frm.set_df_property('stock_uom', 'read_only', 1);
    } else {
        // If no mapping, allow user to choose (or keep as is)
        //frm.set_df_property('stock_uom', 'read_only', 0);
    }
}

function filterCustomSelectMasterOptionsBasedOnRole(frm) {
    const role_map = frappe.boot.item_constants.item_master_role_map;

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

function setItemMasterOptions(frm){
    console.log("Getting Item Master from the constants")
    if (frappe.boot.item_constants && frappe.boot.item_constants.item_master) {
        const options = frappe.boot.item_constants.item_master.join('\n');
        console.log("Got Item Master from the constants")

        console.log(options);

        // Dynamically set options for the Select field
        frm.set_df_property('custom_select_master', 'options', options);
        frm.refresh_field('custom_select_master');
    }
    
}
    

function copy_operations_from_style_master(frm) {
    // Clear existing BOM Operations in the BOM
    frm.clear_table("custom_bom_operations");
    
    // Fetch the Item document to get BOM Operations
    frappe.call({
        method: 'frappe.client.get',
        args: {
            doctype: 'Style Master',
            name: frm.doc.custom_style_master
        },
        callback: function(r) {
            if(r.message && r.message.with_operations) {
                frm.set_value("custom_with_operations",r.message.with_operations );
                frm.refresh_field("custom_with_operations");
            }
            if (r.message && r.message.bom_operations) {
                // Copy each BOM Operation row from Item to BOM
                r.message.bom_operations.forEach(function(operation) {
                    let new_row = frm.add_child("custom_bom_operations");
                    
                    // Copy all fields from Item BOM Operation to BOM Operation
                    // Exclude system fields like name, owner, creation, etc.
                    Object.keys(operation).forEach(function(key) {
                        if (!['name', 'owner', 'creation', 'modified', 'modified_by', 'docstatus', 'idx', 'parent', 'parentfield', 'parenttype'].includes(key)) {
                            new_row[key] = operation[key];
                        }
                    });
                });
                
                // Refresh the operations table to show the copied data
                frm.refresh_field("custom_bom_operations");
                
                // Show success message
                frappe.show_alert({
                    message: __('BOM Operations copied from Item successfully'),
                    indicator: 'green'
                });
            } else {
                frappe.show_alert({
                    message: __('No BOM Operations found in the selected Item'),
                    indicator: 'orange'
                });
            }
        },
        error: function() {
            frappe.msgprint(__('Error fetching Item data'));
        }
    });
}






// Handle item location changes
frappe.ui.form.on('FG Components', {
    component_name: function(frm, cdt, cdn) {
        
        set_parent_component_options(frm, cdt, cdn);
    },
    
});

// A helper function to fetch the component names and set the options.
function set_parent_component_options(frm) {
    // Collect all the component names from the "custom_fg_components" child table.
    let component_names = frm.doc.custom_fg_components.filter(row => row.component_name).map(row => row.component_name);

    frm.doc.custom_fg_components.forEach(function(row, index) {
            let field = frm.fields_dict.custom_fg_components.grid.grid_rows[index].docfields.find(f => f.fieldname === 'parent_component');
            if (field) {
                field.options = [''].concat(component_names);
            }
        });
    
   
    frm.refresh_fields('custom_fg_components');
}