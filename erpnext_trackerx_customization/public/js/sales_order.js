frappe.ui.form.on('Sales Order', {
    onload(frm) {
        // Initialize tree view data structure
        frm.tree_data = [];
        // Flag to prevent re-initialization
        frm.tree_view_initialized = false;
        // Hash to track if items changed after save
        frm._last_items_hash = '';
    },

    refresh(frm) {
        // Apply filters to custom_merchant (only users with role "Merchant")
        frm.set_query('custom_merchant', function() {
            return {
                query: 'frappe.core.doctype.user.user.user_query',
                filters: {
                    role: 'Merchant'
                }
            };
        });

        // Apply filters to custom_merchant_manager (only users with role "Merchant Manager")
        frm.set_query('custom_merchant_manager', function() {
            return {
                query: 'frappe.core.doctype.user.user.user_query',
                filters: {
                    role: 'Merchant Manager'
                }
            };
        });
                
        // Wait for default buttons to load, then remove Work Order
        setTimeout(() => {
          frm.remove_custom_button('Work Order', 'Create');
        }, 1000); 
        
        // Now re-add your own custom button
        if (frm.doc.docstatus === 1 && frm.doc.status !== "Closed") {
          frm.add_custom_button(__('Work Order(s)'), () => {
              open_custom_work_order_dialog(frm);
          }, __('Create'));
        }

        // Initialize tree view only once after form is loaded
        if (!frm.tree_view_initialized) {
            setTimeout(() => {
                setup_tree_view(frm);
                frm.tree_view_initialized = true;
            }, 500);
        } else {
            // Tree view already exists, just sync data if needed
            // This handles the case when form is reloaded after save
            if (frm.doc.__islocal === 0 && frm.doc.items && frm.doc.items.length > 0) {
                // Check if tree_data needs to be reloaded from saved data
                const items_hash = JSON.stringify(frm.doc.items.map(i => 
                    `${i.item_code}_${i.custom_lineitem}_${i.custom_size}_${i.qty}`
                ));
                if (frm._last_items_hash !== items_hash) {
                    load_table_to_tree(frm);
                    render_tree_view(frm);
                    frm._last_items_hash = items_hash;
                }
            }
        }
    },

    before_save(frm) {
        // Convert tree data to child table before saving
        convert_tree_to_table(frm);
        
        // Update hash to track changes
        frm._last_items_hash = JSON.stringify(frm.doc.items.map(i => 
            `${i.item_code}_${i.custom_lineitem}_${i.custom_size}_${i.qty}`
        ));
    }  
});

function update_total_qty(frm){
  total = 0;
  frm.tree_data.forEach(item => {
      console.log(item);
      item.sizes.forEach(size =>{
          total += size.qty;
      });
  });
  console.log(total);
  frm.set_value("total_qty", total);
  frm.refresh_field("total_qty");
}

function setup_tree_view(frm) {
    // Prevent duplicate initialization
    if ($('.tree-view-container').length > 0) {
        return;
    }
    
    // Hide the original items table
    $(frm.fields_dict.items.wrapper).hide();
    
    // Remove any existing tree view
    $('.tree-view-container').remove();
    
    // Add enhanced CSS styles with app theme colors
    const css = `
        <style>
            .tree-view-container {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }
            .tree-item {
                margin-bottom: 12px;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                transition: all 0.2s ease;
            }
            .tree-item:hover {
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .tree-item-header {
                background: linear-gradient(135deg, #82a52f 0%, #6b8726 100%);
                color: white;
                padding: 16px 20px;
                display: flex;
                align-items: center;
                gap: 15px;
                cursor: pointer;
                user-select: none;
                flex-wrap: wrap;
            }
            .tree-item-header:hover {
                background: linear-gradient(135deg, #82a52f 0%, #5d741f 100%);
            }
            .collapse-icon {
                font-size: 14px;
                transition: transform 0.2s ease;
                width: 16px;
                text-align: center;
                min-width: 16px;
            }
            .collapse-icon.collapsed {
                transform: rotate(-90deg);
            }
            .header-field {
                display: flex;
                align-items: center;
                gap: 8px;
                min-width: 0;
            }
            .header-field label {
                font-weight: 600;
                white-space: nowrap;
                margin: 0;
                font-size: 13px;
            }
            .header-controls {
                margin-left: auto;
                display: flex;
                gap: 8px;
                flex-shrink: 0;
            }

            .header-field .form-control[readonly] {
                background-color: #f8f9fa;
                color: #4a5568;
                border-color: #e2e8f0;
                cursor: default;
            }

            .item-code-link-wrapper .link-field {
                margin: 0;
            }

            .item-code-link-wrapper .control-input-wrapper {
                margin: 0;
            }

            .item-code-link-wrapper input {
                height: 32px;
                font-size: 13px;
            }

            .size-item {
                display: flex;
                align-items: center;
                gap: 12px;
                margin: 8px 0;
                padding: 12px 16px;
                background: white;
                border-radius: 6px;
                border: 1px solid #e2e8f0;
                transition: all 0.2s ease;
            }
            .size-item:hover {
                border-color: #82a52f;
                box-shadow: 0 2px 4px rgba(130, 165, 47, 0.1);
            }
            .size-field {
                display: flex;
                align-items: center;
                gap: 6px;
            }
            .size-field label {
                font-weight: 500;
                color: #4a5568;
                min-width: fit-content;
                font-size: 13px;
                margin: 0;
            }
            .btn-icon {
                width: 32px;
                height: 32px;
                padding: 0;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 6px;
                border: none;
                cursor: pointer;
                transition: all 0.2s ease;
                font-size: 14px;
            }
            .btn-icon.btn-add {
                background: #82a52f;
                color: white;
            }
            .btn-icon.btn-add:hover {
                background: #6b8726;
                transform: scale(1.05);
            }
            .btn-icon.btn-remove {
                background: #e53e3e;
                color: white;
            }
            .btn-icon.btn-remove:hover {
                background: #c53030;
                transform: scale(1.05);
            }
            .form-control {
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                padding: 6px 10px;
                transition: border-color 0.2s ease;
                font-size: 13px;
            }
            .form-control:focus {
                border-color: #82a52f;
                outline: none;
                box-shadow: 0 0 0 3px rgba(130, 165, 47, 0.1);
            }
            .tree-content-empty {
                text-align: center;
                color: #82a52f;
                margin: 60px 0;
                font-style: italic;
                font-size: 16px;
            }
            .add-item-btn-main {
                background: linear-gradient(135deg, #82a52f 0%, #6b8726 100%);
                border: none;
                color: white;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: 600;
                transition: all 0.2s ease;
                font-size: 14px;
            }
            .add-item-btn-main:hover {
                background: linear-gradient(135deg, #6b8726 0%, #5d741f 100%);
                transform: translateY(-1px);
                box-shadow: 0 4px 8px rgba(130, 165, 47, 0.3);
            }
            .collapsible-content {
                overflow: hidden;
                transition: max-height 0.3s ease;
            }
            .sizes-container {
                padding: 15px 20px;
                background: #f8f9fa;
            }
            .sizes-container h5 {
                margin: 0 0 15px 0;
                color: #82a52f;
                font-weight: 600;
                font-size: 14px;
            }
        </style>
    `;
    
    // Create tree view container HTML
    const tree_html = `
        ${css}
        <div class="tree-view-container" style="margin: 15px 0;">
            <div class="tree-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h4 style="margin: 0; color: #000000ff; font-weight: 600;">Line Items</h4>
                <button class="add-item-btn-main">
                    <i class="fa fa-plus"></i> Add New Item
                </button>
            </div>
            <div class="tree-content" style="min-height: 200px;"></div>
        </div>
    `;
    
    // Insert tree view after the items field wrapper
    $(frm.fields_dict.items.wrapper).after(tree_html);
    
    // Load existing data into tree view
    load_table_to_tree(frm);
    
    // Bind add item button event
    $('.add-item-btn-main').off('click').on('click', function() {
        add_new_item(frm);
    });
    
    // Render tree view
    render_tree_view(frm);
}

function load_table_to_tree(frm) {
    // Convert existing child table data to 2-level tree structure
    frm.tree_data = [];
    const grouped_items = {};
    
    // Group items by item_code + custom_lineitem combination
    frm.doc.items.forEach(item => {
        const key = `${item.item_code}_${item.custom_lineitem || ''}`;
        if (!grouped_items[key]) {
            grouped_items[key] = {
                id: frappe.utils.get_random(8),
                item_code: item.item_code,
                custom_style: item.custom_style,
                custom_color: item.custom_color,
                custom_lineitem: item.custom_lineitem,
                delivery_date: item.delivery_date,
                custom_ex_fty_date: item.custom_ex_fty_date,
                uom: item.uom,
                conversion_factor: item.conversion_factor,
                sizes: [],
                collapsed: false
            };
        }
        
        grouped_items[key].sizes.push({
            id: frappe.utils.get_random(8),
            custom_size: item.custom_size,
            custom_order_qty: item.custom_order_qty,
            custom_tolerance_percentage: item.custom_tolerance_percentage,
            qty: item.qty,
            original_row: item
        });
    });
    
    // Convert to tree structure
    frm.tree_data = Object.values(grouped_items);
}

function convert_tree_to_table(frm) {
    // Smart update instead of clearing and adding
    const existing_items = [...frm.doc.items];
    const new_items_map = new Map();
    const items_to_update = [];
    
    //validate for line items
    if(!frm.tree_data){
      frappe.throw('Atleast one line item is required!');
    }

    // Build map of new items
    frm.tree_data.forEach(item => {
        if(!item.item_code)
        {
          frappe.throw('Item code is mandatory, Pleae choose valid Finished Goods Item');
        }
        if(!item.custom_lineitem)
        {
          frappe.throw('Line Item is required');
        }        
        if(item.sizes.length < 1){
          frappe.throw('Size details required for Line items');
        }        
        item.sizes.forEach(size => {

            if(size.custom_order_qty <= 0){
              frappe.throw('Please provide qty more than 0');
            }
            
            const key = `${item.item_code}_${item.custom_lineitem || ''}_${size.custom_size || ''}`;
            new_items_map.set(key, {
                item_code: item.item_code || '',
                custom_color: item.custom_color || '',
                custom_colour: item.custom_color || '',
                custom_style: item.custom_style || '',
                custom_lineitem: item.custom_lineitem || '',
                delivery_date: item.delivery_date || '',
                custom_ex_fty_date: item.custom_ex_fty_date || '',
                custom_size: size.custom_size || '',
                custom_order_qty: size.custom_order_qty || 0,
                custom_tolerance_percentage: size.custom_tolerance_percentage || 0,
                qty: size.qty || 0,
                item_name: item.item_code || '',
                custom_pending_qty_for_work_order: 0,
                custom_allocated_qty_for_work_order: 0,
                uom: item.uom || 'Nos',
                conversion_factor: item.conversion_factor || 1
            });
        });
    });
    
    // Update existing items or mark for deletion
    existing_items.forEach((existing_item, index) => {
        const key = `${existing_item.item_code}_${existing_item.custom_lineitem || ''}_${existing_item.custom_size || ''}`;
        if (new_items_map.has(key)) {
            // Update existing item
            const new_data = new_items_map.get(key);
            Object.assign(existing_item, new_data);
            new_items_map.delete(key); // Remove from map as it's been processed
        } else {
            // Mark for deletion
            existing_item._to_delete = true;
        }
    });
    
    // Remove items marked for deletion
    frm.doc.items = frm.doc.items.filter(item => !item._to_delete);
    
    // Add new items
    new_items_map.forEach(new_item_data => {
        const new_row = frm.add_child('items');
        Object.assign(new_row, new_item_data);
    });
    
    frm.refresh_field('items');
}

// Enhanced get_item_attributes function with proper async handling
async function get_item_attributes(item_code) {
    return new Promise((resolve) => {
        if (!item_code) {
            resolve({ uom: "Nos", conversion_factor: 1 });
            return;
        }
        
        frappe.db.get_value('Item', item_code, ['stock_uom', 'uoms'])
            .then((r) => {
                let uom = "Nos";
                let conversion_factor = 1;
                
                default_uom = r.message.stock_uom || '';
                if (r.message && default_uom) {
                    uom = default_uom;
                    
                    if (r.message.uoms && r.message.uoms.length > 0) {
                        const defaultUomEntry = r.message.uoms.find(u => u.uom === r.message.default_uom);
                        if (defaultUomEntry) {
                            conversion_factor = defaultUomEntry.conversion_factor || 1;
                        }
                    }
                }
                
                resolve({ uom, conversion_factor });
            })
            .catch(() => {
                resolve({ uom: "Nos", conversion_factor: 1 });
            });
    });
}

function calculate_summary(sizes) {
    const total_qty = sizes.reduce((sum, size) => sum + (size.qty || 0), 0);
    const total_rows = sizes.length;
    const total_order_qty = sizes.reduce((sum, size) => sum + (size.custom_order_qty || 0), 0);
    
    return {
        total_qty: total_qty.toFixed(2),
        total_rows,
        total_order_qty: total_order_qty.toFixed(2)
    };
}

function render_tree_view(frm) {
    const tree_content = $('.tree-content');
    tree_content.empty();
    
    if (frm.tree_data.length === 0) {
        tree_content.html('<div class="tree-content-empty">No items added. Click "Add New Item" to get started.</div>');
        return;
    }
    
    frm.tree_data.forEach((item, item_index) => {
        const item_code_val = item.item_code || '';
        const color_val = item.custom_color || '';
        const line_item_val = item.custom_lineitem || '';
        const delivery_date_val = item.delivery_date || '';
        const ex_fty_date_val = item.custom_ex_fty_date || '';
        const is_collapsed = item.collapsed || false;
        
        // Calculate summary information
        const summary = calculate_summary(item.sizes);
        
        const item_html = $(`
            <div class="tree-item">
                <div class="tree-item-header" data-item-index="${item_index}">
                    <span class="collapse-icon ${is_collapsed ? 'collapsed' : ''}">▼</span>
                    
                    <div class="header-field">
                        <label>Item:</label>
                        <div class="item-code-link-wrapper" data-item-index="${item_index}" style="width: 180px;"></div>
                    </div>

                    <div class="header-field">
                        <label>Style:</label>
                        <input type="text" class="form-control style-display" style="width: 120px;" 
                            value="${item.custom_style || ''}" data-item-index="${item_index}" readonly>
                    </div>                    
                    
                    <div class="header-field">
                        <label>Color:</label>
                        <input type="text" class="form-control custom-color-input" style="width: 120px;" 
                               value="${color_val}" data-item-index="${item_index}" readonly>
                    </div>
                    
                    <div class="header-field">
                        <label>Line Item:</label>
                        <input type="text" class="form-control line-item-input" style="width: 120px;" 
                               value="${line_item_val}" data-item-index="${item_index}" placeholder="Line Item">
                    </div>
                    
                    <div class="header-field">
                        <label>Delivery:</label>
                        <input type="date" class="form-control delivery-date-input" style="width: 140px;" 
                               value="${delivery_date_val}" data-item-index="${item_index}">
                    </div>
                    
                    <div class="header-field">
                        <label>Ex-Factory:</label>
                        <input type="datetime-local" class="form-control ex-fty-date-input" style="width: 200px;" 
                               value="${ex_fty_date_val}" data-item-index="${item_index}">
                    </div>

                    <div class="header-field">
                        <label>Total Qty:</label>
                        <input type="text" class="form-control total-qty-display" style="width: 100px;" 
                               value="${summary.total_qty}" data-item-index="${item_index}" readonly>
                    </div>

                    <div class="header-field">
                        <label>Sizes:</label>
                        <input type="text" class="form-control total-rows-display" style="width: 100px;" 
                               value="${summary.total_rows}" data-item-index="${item_index}" readonly>
                    </div>

                    <div class="header-field">
                        <label>Order Qty:</label>
                        <input type="text" class="form-control total-order-qty-display" style="width: 100px;" 
                               value="${summary.total_order_qty}" data-item-index="${item_index}" readonly>
                    </div>

                    <div class="header-field">
                        <label>UOM:</label>
                        <input id="uom-input" type="text" class="form-control uom-display" style="width: 100px;" 
                               value="${item.uom}" data-item-index="${item_index}" readonly>
                    </div>

                    <div class="header-field">
                        <label>Conversion factor:</label>
                        <input type="text" class="form-control conversion-factor-display" style="width: 100px;" 
                               value="${item.conversion_factor}" data-item-index="${item_index}" readonly>
                    </div>
                    
                   
                    
                    <div class="header-controls">
                        <button class="btn-icon btn-add add-size-btn" data-item-index="${item_index}" title="Add Size">
                            <i class="fa fa-plus"></i>
                        </button>
                        <button class="btn-icon btn-remove remove-item-btn" data-item-index="${item_index}" title="Remove Item">
                            <i class="fa fa-trash"></i>
                        </button>
                    </div>
                </div>
                <div class="collapsible-content sizes-container" style="max-height: ${is_collapsed ? '0' : '1000px'}; padding: ${is_collapsed ? '0' : '15px 20px'};"></div>
            </div>
        `);
        
        tree_content.append(item_html);
        
        // Render sizes
        if (!is_collapsed) {
            render_sizes(item_html.find('.sizes-container'), item.sizes, item_index);
        }
    });
    
    // Setup Link controls for all item fields
    setTimeout(() => {
        setup_item_link_controls(frm);
    }, 100);
    
    // Bind events
    bind_tree_events(frm);
    
    // Bind size events for all items that have rendered sizes
    frm.tree_data.forEach((item, item_index) => {
        if (!item.collapsed) {
            bind_size_events(frm, item_index);
        }
    });
}

function setup_item_link_controls(frm) {
    $('.item-code-link-wrapper').each(function() {
        const wrapper = $(this);
        const item_index = wrapper.data('item-index');
        const current_value = frm.tree_data[item_index].item_code || '';
        
        // Skip if already initialized
        if (wrapper.data('link-control')) {
            return;
        }
        
        // Create a unique field name for this control
        const fieldname = `item_code_${item_index}_${frappe.utils.get_random(4)}`;
        
        // Create the Link control
        const link_field = frappe.ui.form.make_control({
            parent: wrapper,
            df: {
                fieldtype: 'Link',
                fieldname: fieldname,
                options: 'Item',
                placeholder: 'Select Item',
                get_query: function() {
                    return {
                        filters: {
                            custom_select_master: 'Finished Goods'
                        }
                    };
                },
                onchange: async function() {
                    const item_code = this.get_value();
                    const current_item_code = frm.tree_data[item_index].item_code;
                    
                    // Only reset if the item code actually changed
                    if (item_code !== current_item_code) {
                        // Reset fields only when item changes
                        frm.tree_data[item_index].item_code = item_code;
                        frm.tree_data[item_index].custom_style = '';
                        frm.tree_data[item_index].custom_color = '';
                        frm.tree_data[item_index].sizes = [];
                        
                        if (item_code) {
                            try {
                                // Fetch UOM/conversion
                                const attributes = await get_item_attributes(item_code);
                                frm.tree_data[item_index].uom = attributes.uom;
                                frm.tree_data[item_index].conversion_factor = attributes.conversion_factor;
                                // Fetch style and color from Item
                                const item_data = await frappe.db.get_value('Item', item_code,
                                    ['custom_style_master', 'custom_colour_name']
                                );
                                if (item_data.message) {
                                    frm.tree_data[item_index].custom_style = item_data.message.custom_style_master || '';
                                    frm.tree_data[item_index].custom_color = item_data.message.custom_colour_name || '';
                                }
                            } catch (error) {
                                console.warn('Failed to fetch item details:', error);
                                frm.tree_data[item_index].uom = 'Nos';
                                frm.tree_data[item_index].conversion_factor = 1;
                                frm.tree_data[item_index].custom_style = '';
                                frm.tree_data[item_index].custom_color = '';
                            }
                        }
                        // Update display fields directly without re-rendering
                        update_item_display_fields(frm, item_index);
                        frm.dirty();
                    }
                }
            }
        });
        
        link_field.refresh();
        
        // Set the current value if exists
        if (current_value) {
            link_field.set_value(current_value);
        }
        
        // Store reference to the control for later access if needed
        wrapper.data('link-control', link_field);
    });
}

function update_item_display_fields(frm, item_index) {
    const item = frm.tree_data[item_index];
    const item_element = $(`.tree-item-header[data-item-index="${item_index}"]`);
    
    // Update style field
    item_element.find('.style-display').val(item.custom_style || '');
    
    // Update color field
    item_element.find('.custom-color-input').val(item.custom_color || '');
    
    // Update UOM field
    item_element.find('.uom-display').val(item.uom || 'Nos');
    
    // Update conversion factor field
    item_element.find('.conversion-factor-display').val(item.conversion_factor || 1);
    
    // Clear sizes container since sizes were reset
    const sizes_container = item_element.siblings('.collapsible-content');
    if (!item.collapsed) {
        render_sizes(sizes_container, item.sizes, item_index);
        // Rebind size-specific events after rendering
        bind_size_events(frm, item_index);
    }
    
    // Update summary display
    update_summary_display(frm, item_index);
}

function bind_size_events(frm, item_index) {
    const item_selector = `[data-item-index="${item_index}"]`;
    
    // Size fields change
    $(`.size-input${item_selector}`).off('input').on('input', function() {
        const size_index = $(this).data('size-index');
        frm.tree_data[item_index].sizes[size_index].custom_size = $(this).val();
        frm.dirty();
    });
    
    $(`.order-qty-input${item_selector}, .tolerance-input${item_selector}`).off('input').on('input', function() {
        const size_index = $(this).data('size-index');
        const uom = $(`.tree-item-header[data-item-index="${item_index}"]`).find('.uom-display').val();
        
        const size_obj = frm.tree_data[item_index].sizes[size_index];
        
        if ($(this).hasClass('order-qty-input')) {
            size_obj.custom_order_qty = parseFloat($(this).val()) || 0;
        } else {
            size_obj.custom_tolerance_percentage = parseFloat($(this).val()) || 0;
        }
        
        // Calculate final qty
        let final_qty = size_obj.custom_order_qty + (size_obj.custom_order_qty * size_obj.custom_tolerance_percentage / 100);
        if(uom === "Nos")
        {
            final_qty = Math.ceil(final_qty);
        }
        size_obj.qty = final_qty;
        
        // Update display
        $(this).closest('.size-item').find('.qty-display').val(final_qty.toFixed(2));
        
        // Update summary information
        update_summary_display(frm, item_index);
        update_total_qty(frm);
        
        frm.dirty();
    });
    
    $(`.remove-size-btn${item_selector}`).off('click').on('click', function(e) {
        e.stopPropagation();
        const size_index = $(this).data('size-index');
        remove_size(frm, item_index, size_index);
        update_total_qty(frm);
        frm.dirty();
    });
}

function render_sizes(container, sizes, item_index) {
    container.empty();
    
    if (sizes.length === 0) {
        container.html('<div style="text-align: center; color: #82a52f; font-style: italic;">No sizes added. Click the + button above to add sizes.</div>');
        return;
    }
    
    container.append('<h5><i class="fa fa-resize-horizontal"></i> Size Details</h5>');
    
    sizes.forEach((size, size_index) => {
        const size_val = size.custom_size || '';
        const order_qty_val = size.custom_order_qty || 0;
        const tolerance_val = size.custom_tolerance_percentage || 0;
        const qty_val = size.qty || 0;
        
        const size_html = $(`
            <div class="size-item">
                <div class="size-field">
                    <label>Size:</label>
                    <input type="text" class="form-control size-input" style="width: 80px;" 
                           value="${size_val}" data-item-index="${item_index}" data-size-index="${size_index}">
                </div>
                <div class="size-field">
                    <label>Order Qty:</label>
                    <input type="number" class="form-control order-qty-input" style="width: 90px;" 
                           value="${order_qty_val}" data-item-index="${item_index}" data-size-index="${size_index}">
                </div>
                <div class="size-field">
                    <label>Tolerance %:</label>
                    <input type="number" class="form-control tolerance-input" style="width: 80px;" 
                           value="${tolerance_val}" data-item-index="${item_index}" data-size-index="${size_index}">
                </div>
                <div class="size-field">
                    <label>Final Qty:</label>
                    <input type="number" class="form-control qty-display" style="width: 90px; background-color: #f8f9fa;" 
                           value="${qty_val}" readonly>
                </div>
                <button class="btn-icon btn-remove remove-size-btn" data-item-index="${item_index}" data-size-index="${size_index}" title="Remove Size">
                    <i class="fa fa-trash"></i>
                </button>
            </div>
        `);
        
        container.append(size_html);
    });
}

function update_summary_display(frm, item_index) {
    const item = frm.tree_data[item_index];
    const summary = calculate_summary(item.sizes);
    
    const item_element = $(`.tree-item-header[data-item-index="${item_index}"]`);
    item_element.find('.total-qty-display').val(summary.total_qty);
    item_element.find('.total-rows-display').val(summary.total_rows);
    item_element.find('.total-order-qty-display').val(summary.total_order_qty);

}

function bind_item_header_events(frm, item_index) {
    const item_selector = `[data-item-index="${item_index}"]`;
    
    // Collapse/Expand functionality for this specific item
    $(`.tree-item-header${item_selector}`).off('click').on('click', function(e) {
        // Prevent collapsing when clicking on inputs, buttons, or elements within buttons
        if ($(e.target).closest('input, select, button, .link-field, .awesomplete').length > 0) return;
        
        const icon = $(this).find('.collapse-icon');
        const content = $(this).siblings('.collapsible-content');
        
        frm.tree_data[item_index].collapsed = !frm.tree_data[item_index].collapsed;
        
        if (frm.tree_data[item_index].collapsed) {
            icon.addClass('collapsed');
            content.css('max-height', '0');
            content.css('padding', '0');
        } else {
            icon.removeClass('collapsed');
            content.css('max-height', '1000px');
            content.css('padding', '15px 20px');
            // Re-render sizes when expanding
            render_sizes(content, frm.tree_data[item_index].sizes, item_index);
            // Rebind events for the sizes
            bind_size_events(frm, item_index);
        }
    });
    
    // Item level field changes
    $(`.custom-color-input${item_selector}`).off('input').on('input', function() {
        frm.tree_data[item_index].custom_color = $(this).val();
        frm.dirty();
    });
    
    $(`.line-item-input${item_selector}`).off('input').on('input', function() {
        frm.tree_data[item_index].custom_lineitem = $(this).val();
        frm.dirty();
    });
    
    $(`.delivery-date-input${item_selector}`).off('change').on('change', function() {
        frm.tree_data[item_index].delivery_date = $(this).val();
        frm.dirty();
    });
    
    $(`.ex-fty-date-input${item_selector}`).off('change').on('change', function() {
        frm.tree_data[item_index].custom_ex_fty_date = $(this).val();
        frm.dirty();
    });
    
    // Add size button
    $(`.add-size-btn${item_selector}`).off('click').on('click', function(e) {
        e.stopPropagation();
        add_size(frm, item_index);
        update_total_qty(frm);
        frm.dirty();
    });
    
    // Remove item button
    $(`.remove-item-btn${item_selector}`).off('click').on('click', function(e) {
        e.stopPropagation();
        remove_item(frm, item_index);
        update_total_qty(frm);
        frm.dirty();
    });
}

function bind_tree_events(frm) {
    // Bind header events for all items
    frm.tree_data.forEach((item, item_index) => {
        bind_item_header_events(frm, item_index);
    });
}

function add_new_item(frm) {
    const new_item_index = frm.tree_data.length;
    
    frm.tree_data.push({
        id: frappe.utils.get_random(8),
        item_code: '',
        custom_color: '',
        custom_lineitem: '',
        delivery_date: '',
        custom_ex_fty_date: '',
        uom: 'Nos',
        conversion_factor: 1,
        sizes: [],
        collapsed: false
    });
    
    // Instead of re-rendering entire tree, just append the new item
    const item = frm.tree_data[new_item_index];
    const summary = calculate_summary(item.sizes);
    
    const item_html = $(`
        <div class="tree-item">
            <div class="tree-item-header" data-item-index="${new_item_index}">
                <span class="collapse-icon">▼</span>
                
                <div class="header-field">
                    <label>Item:</label>
                    <div class="item-code-link-wrapper" data-item-index="${new_item_index}" style="width: 180px;"></div>
                </div>

                <div class="header-field">
                    <label>Style:</label>
                    <input type="text" class="form-control style-display" style="width: 120px;" 
                        value="" data-item-index="${new_item_index}" readonly>
                </div>                    
                
                <div class="header-field">
                    <label>Color:</label>
                    <input type="text" class="form-control custom-color-input" style="width: 120px;" 
                           value="" data-item-index="${new_item_index}" readonly>
                </div>
                
                <div class="header-field">
                    <label>Line Item:</label>
                    <input type="text" class="form-control line-item-input" style="width: 120px;" 
                           value="" data-item-index="${new_item_index}" placeholder="Line Item">
                </div>
                
                <div class="header-field">
                    <label>Delivery:</label>
                    <input type="date" class="form-control delivery-date-input" style="width: 140px;" 
                           value="" data-item-index="${new_item_index}">
                </div>
                
                <div class="header-field">
                    <label>Ex-Factory:</label>
                    <input type="datetime-local" class="form-control ex-fty-date-input" style="width: 200px;" 
                           value="" data-item-index="${new_item_index}">
                </div>

                <div class="header-field">
                    <label>Total Qty:</label>
                    <input type="text" class="form-control total-qty-display" style="width: 100px;" 
                           value="${summary.total_qty}" data-item-index="${new_item_index}" readonly>
                </div>

                <div class="header-field">
                    <label>Sizes:</label>
                    <input type="text" class="form-control total-rows-display" style="width: 100px;" 
                           value="${summary.total_rows}" data-item-index="${new_item_index}" readonly>
                </div>

                <div class="header-field">
                    <label>Order Qty:</label>
                    <input type="text" class="form-control total-order-qty-display" style="width: 100px;" 
                           value="${summary.total_order_qty}" data-item-index="${new_item_index}" readonly>
                </div>

                <div class="header-field">
                    <label>UOM:</label>
                    <input id="uom-input" type="text" class="form-control uom-display" style="width: 100px;" 
                           value="Nos" data-item-index="${new_item_index}" readonly>
                </div>

                <div class="header-field">
                    <label>Conversion factor:</label>
                    <input type="text" class="form-control conversion-factor-display" style="width: 100px;" 
                           value="1" data-item-index="${new_item_index}" readonly>
                </div>
                
                <div class="header-controls">
                    <button class="btn-icon btn-add add-size-btn" data-item-index="${new_item_index}" title="Add Size">
                        <i class="fa fa-plus"></i>
                    </button>
                    <button class="btn-icon btn-remove remove-item-btn" data-item-index="${new_item_index}" title="Remove Item">
                        <i class="fa fa-trash"></i>
                    </button>
                </div>
            </div>
            <div class="collapsible-content sizes-container" style="max-height: 1000px; padding: 15px 20px;"></div>
        </div>
    `);
    
    $('.tree-content').append(item_html);
    
    // Render sizes for the new item
    render_sizes(item_html.find('.sizes-container'), item.sizes, new_item_index);
    
    // Setup Link control for the new item
    setTimeout(() => {
        const wrapper = $(`.item-code-link-wrapper[data-item-index="${new_item_index}"]`);
        const fieldname = `item_code_${new_item_index}_${frappe.utils.get_random(4)}`;
        
        const link_field = frappe.ui.form.make_control({
            parent: wrapper,
            df: {
                fieldtype: 'Link',
                fieldname: fieldname,
                options: 'Item',
                placeholder: 'Select Item',
                get_query: function() {
                    return {
                        filters: {
                            custom_select_master: 'Finished Goods'
                        }
                    };
                },
                onchange: async function() {
                    const item_code = this.get_value();
                    
                    // Reset fields
                    frm.tree_data[new_item_index].item_code = item_code;
                    frm.tree_data[new_item_index].custom_style = '';
                    frm.tree_data[new_item_index].custom_color = '';
                    frm.tree_data[new_item_index].sizes = [];

                    if (item_code) {
                        try {
                            // Fetch UOM/conversion
                            const attributes = await get_item_attributes(item_code);
                            frm.tree_data[new_item_index].uom = attributes.uom;
                            frm.tree_data[new_item_index].conversion_factor = attributes.conversion_factor;

                            // Fetch style and color from Item
                            const item_data = await frappe.db.get_value('Item', item_code, 
                                ['custom_style_master', 'custom_colour_name']
                            );
                            if (item_data.message) {
                                frm.tree_data[new_item_index].custom_style = item_data.message.custom_style_master || '';
                                frm.tree_data[new_item_index].custom_color = item_data.message.custom_colour_name || '';
                            }
                        } catch (error) {
                            console.warn('Failed to fetch item details:', error);
                            frm.tree_data[new_item_index].uom = 'Nos';
                            frm.tree_data[new_item_index].conversion_factor = 1;
                            frm.tree_data[new_item_index].custom_style = '';
                            frm.tree_data[new_item_index].custom_color = '';
                        }
                    }

                    // Update display fields directly without re-rendering
                    update_item_display_fields(frm, new_item_index);
                    frm.dirty();
                }
            }
        });
        
        link_field.refresh();
        wrapper.data('link-control', link_field);
    }, 100);
    
    // Bind events for the new item's header
    bind_item_header_events(frm, new_item_index);
    
    // Bind size events for the new item
    bind_size_events(frm, new_item_index);
}

function add_size(frm, item_index) {
    frm.tree_data[item_index].sizes.push({
        id: frappe.utils.get_random(8),
        custom_size: '',
        custom_order_qty: 0,
        custom_tolerance_percentage: 0,
        qty: 0
    });
    
    // Only re-render this item's sizes, not the entire tree
    const item_element = $(`.tree-item-header[data-item-index="${item_index}"]`);
    const sizes_container = item_element.siblings('.collapsible-content');
    
    if (!frm.tree_data[item_index].collapsed) {
        render_sizes(sizes_container, frm.tree_data[item_index].sizes, item_index);
        bind_size_events(frm, item_index);
    }
    
    update_summary_display(frm, item_index);
}

function remove_item(frm, item_index) {
    if (confirm('Are you sure you want to remove this item and all its sizes?')) {
        frm.tree_data.splice(item_index, 1);
        render_tree_view(frm);
        update_total_qty(frm);
    }
}

function remove_size(frm, item_index, size_index) {
    frm.tree_data[item_index].sizes.splice(size_index, 1);
    
    // Only re-render this item's sizes, not the entire tree
    const item_element = $(`.tree-item-header[data-item-index="${item_index}"]`);
    const sizes_container = item_element.siblings('.collapsible-content');
    
    if (!frm.tree_data[item_index].collapsed) {
        render_sizes(sizes_container, frm.tree_data[item_index].sizes, item_index);
        bind_size_events(frm, item_index);
    }
    
    update_summary_display(frm, item_index);
}

// Work Order functions (keeping your existing functionality)
function open_custom_work_order_dialog(frm) {
  const items = frm.doc.items.map(item => ({
    item_code: item.item_code,
    qty: item.qty,
    custom_size: item.custom_size,
    custom_lineitem: item.custom_lineitem,
    so_detail: item.name
  }));

  const dialog = new frappe.ui.Dialog({
    title: 'Custom Work Order Creation',
    fields: [
      {
        fieldtype: 'Link',
        label: 'Source Warehouse',
        fieldname: 'source_warehouse',
        options: 'Warehouse',
        reqd: 1,
        description: 'Warehouse to source raw materials from'
      },
      {
        fieldtype: 'Link',
        label: 'WIP Warehouse',
        fieldname: 'wip_warehouse',
        options: 'Warehouse',
        reqd: 1,
        description: 'Work in Progress warehouse for manufacturing'
      },
      {
        fieldtype: 'Link',
        label: 'Target Warehouse',
        fieldname: 'fg_warehouse',
        options: 'Warehouse',
        reqd: 1,
        description: 'Finished goods warehouse'
      },
      {
        fieldtype: 'Column Break'
      },
      {
        fieldtype: 'Select',
        label: 'Work Order Creation Mode',
        fieldname: 'creation_mode',
        options: [
          'Single Work Order for All',
          'Separate Work Order per Line Item',
          'Separate Work Order per Size'
        ],
        default: 'Single Work Order for All',
        reqd: 1,
        change: function() {
          const mode = this.get_value();
          let button_text = 'Create Work Order(s)';
          
          if (mode === 'Single Work Order for All') {
            button_text = 'Create Single Work Order';
          } else if (mode === 'Separate Work Order per Line Item') {
            button_text = 'Create Work Orders by Line Item';
          } else if (mode === 'Separate Work Order per Size') {
            button_text = 'Create Work Orders by Size';
          }
          
          dialog.set_primary_action(button_text);
        }
      },
      {
        fieldtype: 'Section Break'
      },
      {
        fieldtype: 'Table',
        label: 'Sales Order Items',
        fieldname: 'items_table',
        cannot_add_rows: true,
        in_place_edit: false,
        data: items,
        get_data: () => items,
        fields: [
          {
            fieldtype: 'Data',
            fieldname: 'item_code',
            label: 'Item Code',
            in_list_view: true,
            read_only: true
          },
          {
            fieldtype: 'Data',
            fieldname: 'custom_lineitem',
            label: 'Line Item',
            in_list_view: true,
            read_only: true
          },
          {
            fieldtype: 'Data',
            fieldname: 'custom_size',
            label: 'Size',
            in_list_view: true,
            read_only: true
          },
          {
            fieldtype: 'Float',
            fieldname: 'qty',
            label: 'Qty',
            in_list_view: true,
            read_only: true
          }
        ]
      }
    ],
    primary_action_label: 'Create Single Work Order',
    primary_action(values) {
      const selected_items = dialog.fields_dict.items_table.grid.get_selected_children();
      if (selected_items.length === 0) {
        frappe.throw('Please select at least one line item to create a work order');
      }

      
      const mode = values.creation_mode;
      const source_warehouse = values.source_warehouse;
      const wip_warehouse = values.wip_warehouse;
      const fg_warehouse = values.fg_warehouse;
      
      if (mode === 'Single Work Order for All') {
        create_single_work_order(frm, selected_items, source_warehouse, wip_warehouse, fg_warehouse);
      } else if (mode === 'Separate Work Order per Line Item') {
        create_work_orders_by_line_item(frm, selected_items, source_warehouse, wip_warehouse, fg_warehouse);
      } else if (mode === 'Separate Work Order per Size') {
        create_work_orders_by_size(frm, selected_items, source_warehouse, wip_warehouse, fg_warehouse);
      }

      dialog.hide();
    }
  });

  dialog.show();
}

// Helper function to fetch BOM Items by getting the full BOM document
function get_bom_required_items(bom_no, production_qty, source_warehouse) {
    return new Promise((resolve, reject) => {
        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'BOM',
                name: bom_no
            },
            callback(response) {
                if (response.message && response.message.items) {
                    const required_items = response.message.items.map(bom_item => ({
                        item_code: bom_item.item_code,
                        required_qty: bom_item.qty * production_qty,
                        stock_qty: bom_item.stock_qty * production_qty,
                        uom: bom_item.uom,
                        rate: bom_item.rate || 0,
                        amount: (bom_item.rate || 0) * production_qty,
                        source_warehouse: source_warehouse
                    }));
                    resolve(required_items);
                } else {
                    resolve([]);
                }
            },
            error(error) {
                reject(error);
            }
        });
    });
}

function create_single_work_order(frm, items, source_warehouse, wip_warehouse, fg_warehouse) {
    // Calculate total quantity correctly
    let total_qty = 0;
    for (let item of items) {
        total_qty += item.qty;
    }

    const production_item = items[0].item_code;
    
    // First get BOM for the production item
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'BOM',
            filters: {
                item: production_item,
                is_active: 1,
                is_default: 1
            },
            fields: ['name']
        },
        callback: async function(bom_response) {
            let bom_no = null;
            let required_items = [];
            
            if (bom_response.message && bom_response.message.length > 0) {
                bom_no = bom_response.message[0].name;
                
                try {
                    // Get required items from BOM
                    required_items = await get_bom_required_items(bom_no, total_qty, source_warehouse);
                } catch (error) {
                    frappe.msgprint({
                        title: 'Error',
                        message: 'Failed to fetch BOM items: ' + error.message,
                        indicator: 'red'
                    });
                    return;
                }
            }
            
            // Create the Work Order
            frappe.call({
                method: 'frappe.client.insert',
                args: {
                    doc: {
                        doctype: 'Work Order',
                        production_item: production_item,
                        company: frm.doc.company,
                        qty: total_qty,
                        bom_no: bom_no,
                        source_warehouse: source_warehouse,
                        wip_warehouse: wip_warehouse,
                        fg_warehouse: fg_warehouse,
                        sales_order: frm.doc.name,
                        custom_sales_orders: [{
                            sales_order: frm.doc.name,
                        }],
                        required_items: required_items, // Now using BOM Items
                        custom_work_order_line_items: items.map(i => ({
                            work_order_allocated_qty: i.qty,
                            sales_order: frm.doc.name,
                            sales_order_item: i.so_detail,
                            size: i.custom_size,
                            line_item_no: i.custom_lineitem
                        })),
                    }
                },
                callback(r) {
                    if (r.message) {
                        frappe.set_route('Form', 'Work Order', r.message.name);
                        frappe.show_alert({
                            message: `Work Order ${r.message.name} created successfully`,
                            indicator: 'green'
                        });
                    }
                },
                error(r) {
                    frappe.msgprint({
                        title: 'Error',
                        message: r.message || 'An error occurred while creating the Work Order',
                        indicator: 'red'
                    });
                }
            });
        }
    });
}

function create_work_orders_by_line_item(frm, items, source_warehouse, wip_warehouse, fg_warehouse) {

  const grouped_by_lineitem = {};

    // Group the items
  items.forEach(item => {
    const lineitem_key = item.custom_lineitem;
    if (!grouped_by_lineitem[lineitem_key]) {
      grouped_by_lineitem[lineitem_key] = [];
    }
    grouped_by_lineitem[lineitem_key].push(item);
  });

  Object.keys(grouped_by_lineitem).forEach(lineitem => {
    const group = grouped_by_lineitem[lineitem];
    const first = group[0];
    const total_qty = group.reduce((sum, item) => sum + item.qty, 0);

    // Get BOM for each item
    frappe.call({
      method: 'frappe.client.get_list',
      args: {
        doctype: 'BOM',
        filters: {
          item: first.item_code,
          is_active: 1,
          is_default: 1
        },
        fields: ['name']
      },
      callback: async function(bom_response) {
        let bom_no = null;
        let required_items = [];
        
        if (bom_response.message && bom_response.message.length > 0) {
          bom_no = bom_response.message[0].name;
          
          try {
            // Get required items from BOM
            required_items = await get_bom_required_items(bom_no, total_qty, source_warehouse);
          } catch (error) {
            frappe.msgprint({
              title: 'Error',
              message: `Failed to fetch BOM items for ${first.item_code}: ${error.message}`,
              indicator: 'red'
            });
            return;
          }
        }

        frappe.call({
          method: 'frappe.client.insert',
          args: {
            doc: {
              doctype: 'Work Order',
              production_item: first.item_code,
              company: frm.doc.company,
              qty: total_qty,
              bom_no: bom_no,
              source_warehouse: source_warehouse,
              wip_warehouse: wip_warehouse,
              fg_warehouse: fg_warehouse,
              sales_order: frm.doc.name,
              custom_sales_orders: [{
                            sales_order: frm.doc.name,
                        }],
              custom_work_order_line_items: group.map(i => ({
                            work_order_allocated_qty: i.qty,
                            sales_order: frm.doc.name,
                            sales_order_item: i.so_detail,
                            size: i.custom_size,
                            line_item_no: i.custom_lineitem
                        })),
              required_items: required_items // Now using BOM Items
            }
          },
          callback(r) {
            if (r.message) {
              frappe.msgprint(`Created Work Order: ${r.message.name}`);
            }
          },
          error(r) {
            frappe.msgprint({
              title: 'Error',
              message: `Failed to create Work Order for ${first.item_code}: ${r.message}`,
              indicator: 'red'
            });
          }
        });
      }
    });
  });
}

function create_work_orders_by_size(frm, items, source_warehouse, wip_warehouse, fg_warehouse) {
  // Create separate work order for each individual item row
  items.forEach(item => {
    // Get BOM for each individual item
    frappe.call({
      method: 'frappe.client.get_list',
      args: {
        doctype: 'BOM',
        filters: {
          item: item.item_code,
          is_active: 1,
          is_default: 1
        },
        fields: ['name']
      },
      callback: async function(bom_response) {
        let bom_no = null;
        let required_items = [];
        
        if (bom_response.message && bom_response.message.length > 0) {
          bom_no = bom_response.message[0].name;
          
          try {
            // Get required items from BOM for this individual item
            required_items = await get_bom_required_items(bom_no, item.qty, source_warehouse);
          } catch (error) {
            frappe.msgprint({
              title: 'Error',
              message: `Failed to fetch BOM items for ${item.item_code} (${item.custom_size}): ${error.message}`,
              indicator: 'red'
            });
            return;
          }
        }

        frappe.call({
          method: 'frappe.client.insert',
          args: {
            doc: {
              doctype: 'Work Order',
              production_item: item.item_code,
              company: frm.doc.company,
              qty: item.qty,
              bom_no: bom_no,
              source_warehouse: source_warehouse,
              wip_warehouse: wip_warehouse,
              fg_warehouse: fg_warehouse,
              sales_order: frm.doc.name,
              custom_sales_orders: [{
                sales_order: frm.doc.name,
              }],
              required_items: required_items, // Now using BOM Items
              custom_work_order_line_items: [{
                work_order_allocated_qty: item.qty,
                sales_order: frm.doc.name,
                sales_order_item: item.so_detail,
                size: item.custom_size,
                line_item_no: item.custom_lineitem
              }]
            }
          },
          callback(r) {
            if (r.message) {
              frappe.msgprint(`Created Work Order for ${item.item_code} (Size: ${item.custom_size}, Line: ${item.custom_lineitem}): ${r.message.name}`);
            }
          },
          error(r) {
            frappe.msgprint({
              title: 'Error',
              message: `Failed to create Work Order for ${item.item_code} (${item.custom_size}): ${r.message}`,
              indicator: 'red'
            });
          }
        });
      }
    });
  });
}

frappe.ui.form.on('Sales Order Item', {
  custom_order_qty: function (frm, cdt, cdn) {
    update_qty_based_on_custom_fields(cdt, cdn);
  },

  custom_tolerance_percentage: function (frm, cdt, cdn) {
    update_qty_based_on_custom_fields(cdt, cdn);
  }
});

function update_qty_based_on_custom_fields(cdt, cdn) {
  const row = locals[cdt][cdn];

  const custom_qty = flt(row.custom_order_qty);
  const tolerance_pct = flt(row.custom_tolerance_percentage);

  if (custom_qty >= 0 && tolerance_pct >= 0) {
    const qty = custom_qty + (custom_qty * tolerance_pct / 100);
    frappe.model.set_value(cdt, cdn, 'qty', qty);
  }
}