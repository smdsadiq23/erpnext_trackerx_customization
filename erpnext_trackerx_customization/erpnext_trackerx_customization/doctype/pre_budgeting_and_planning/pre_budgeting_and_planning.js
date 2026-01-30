// Copyright (c) 2026, CognitionX and contributors
// For license information, please see license.txt


frappe.ui.form.on('Pre-Budgeting and Planning', {
    // Trigger when Style field changes
    style: function(frm) {
        set_sales_order_filter(frm);
        
        // Clear dependent fields when style changes
        if (frm.doc.sales_order) {
            frm.set_value('sales_order', '');
            frm.clear_table('table_itma');
            frm.clear_table('table_wfui');
            frm.refresh_field('table_itma');
            frm.refresh_field('table_wfui');
            clear_cost_fields(frm);
        }
    },

    // Trigger when Sales Order is selected
    sales_order: function(frm) {
        if (!frm.doc.sales_order) {
            frm.clear_table('table_itma');
            frm.clear_table('table_wfui'); 
            frm.refresh_field('table_itma');
            frm.refresh_field('table_wfui');
            clear_cost_fields(frm);
            return;
        }

        // First fetch SO totals BEFORE loading components
        fetch_so_totals(frm, function() {
            // Then fetch yarn/accessories data
            frm.call({
                method: 'erpnext_trackerx_customization.erpnext_trackerx_customization.doctype.pre_budgeting_and_planning.pre_budgeting_and_planning.fetch_yarn_accessories_from_sales_order',
                args: {
                    sales_order: frm.doc.sales_order,
                    style: frm.doc.style
                },
                freeze: true,
                freeze_message: __('Loading yarn and accessories data...'),
                callback: function(r) {
                    frm.clear_table('table_itma');
                    
                    if (r.message && r.message.length > 0) {
                        r.message.forEach(row => {
                            frm.add_child('table_itma', row);
                        });
                        frm.refresh_field('table_itma');
                        
                        // Recalculate all totals including profit fields
                        recalculate_totals(frm);
                        recalculate_fg_wise(frm);
                        
                        // Show success message
                        const fgItemCount = [...new Set(r.message.map(r => r.fg_item))].length;
                        const itemsWithZeroRate = r.message.filter(r => !r.rate || r.rate === 0).length;
                        
                        let alertMsg = __('Loaded {0} component rows from {1} FG items', [r.message.length, fgItemCount]);
                        if (itemsWithZeroRate > 0) {
                            alertMsg += __('<br><small style="color:orange">{0} items have zero/no rate - please verify pricing</small>', [itemsWithZeroRate]);
                        }
                        
                        frappe.show_alert({
                            message: alertMsg,
                            indicator: itemsWithZeroRate > 0 ? 'orange' : 'green'
                        });
                        
                        // Auto-fetch process data if category is already selected
                        if (frm.doc.category) {
                            fetch_process_data(frm);
                        }
                    } else {
                        frappe.msgprint({
                            title: __('No Data Found'),
                            message: __('No yarn/accessories data found. Please verify:<br>1. BOMs exist for FG items<br>2. Items have matching style<br>3. Item Prices exist for components'),
                            indicator: 'orange'
                        });
                    }
                }
            });
        });
    },

    // Trigger when Overhead % changes
    overhead_: function(frm) {
        recalculate_totals(frm);
    },

    // Trigger when Actual Sales Amount changes (manual override)
    actual_sales_amount: function(frm) {
        recalculate_totals(frm);
    },

    // Trigger when Category field changes - LOAD PROCESS DATA
    category: function(frm) {
        frm.clear_table('table_wfui');
        frm.refresh_field('table_wfui');     
        if (frm.doc.category && frm.doc.style && frm.doc.sales_order) {
            fetch_process_data(frm);
        } else if (frm.doc.category) {
            if (!frm.doc.style) {
                frappe.show_alert({
                    message: __('Please select Style first'),
                    indicator: 'orange'
                });
            } else if (!frm.doc.sales_order) {
                frappe.show_alert({
                    message: __('Please select Sales Order first'),
                    indicator: 'orange'
                });
            }
        } else {
            recalculate_totals(frm);
            recalculate_fg_wise(frm);
        }
    },    

    // Initialize on form load
    refresh: function(frm) {
        if (frm.doc.style && frm.doc.__islocal) {
            set_sales_order_filter(frm);
        }
        
        // // Recalculate all totals for existing documents
        // if (!frm.doc.__islocal) {
        //     recalculate_totals(frm);
        //     if (frm.doc.table_itma && frm.doc.table_itma.length > 0) {
        //         recalculate_fg_wise(frm);
        //     }
        // }
    },

    onload: function(frm) {
        if (!frm.doc.sales_order && !frm.doc.style) {
            frm.clear_table('table_itma');
            frm.clear_table('table_wfui');
            frm.refresh_field('table_itma');
            frm.refresh_field('table_wfui');
        }
    }
});

// Helper: Fetch SO totals (qty and amount) for the selected style
function fetch_so_totals(frm, callback) {
    if (!frm.doc.sales_order || !frm.doc.style) {
        if (callback) callback();
        return;
    }
    
    frm.call({
        method: 'erpnext_trackerx_customization.erpnext_trackerx_customization.doctype.pre_budgeting_and_planning.pre_budgeting_and_planning.get_so_totals',
        args: {
            sales_order: frm.doc.sales_order,
            style: frm.doc.style
        },
        freeze: true,
        freeze_message: __('Fetching order totals...'),
        callback: function(r) {
            if (r.message) {
                frm.set_value('total_qty', flt(r.message.total_qty, 2));
                // Only set actual_sales_amount if not manually overridden by user
                if (!frm.doc.actual_sales_amount || frm.doc.actual_sales_amount === 0) {
                    frm.set_value('actual_sales_amount', flt(r.message.actual_sales_amount, 2));
                }
            }
            if (callback) callback();
        }
    });
}

// Helper function to set dynamic query on Sales Order field
function set_sales_order_filter(frm) {
    frm.set_query('sales_order', function() {
        if (!frm.doc.style) {
            return {
                filters: {
                    docstatus: 1
                }
            };
        }
        
        return {
            query: 'erpnext_trackerx_customization.erpnext_trackerx_customization.doctype.pre_budgeting_and_planning.pre_budgeting_and_planning.get_sales_orders_by_style',
            filters: {
                style: frm.doc.style
            }
        };
    });
}

// Helper function to clear cost fields
function clear_cost_fields(frm) {
    frm.set_value('total_yarn_cost', 0);
    frm.set_value('total_accessories_cost', 0);
    frm.set_value('total_cost', 0);
    frm.set_value('process_cost', 0);
    frm.set_value('grand_total', 0);
    frm.set_value('total_qty', 0);
    frm.set_value('actual_sales_amount', 0);
    frm.set_value('salepack', 0);
    frm.set_value('budget_price_per_pack', 0);
    frm.set_value('actual_profit', 0);
    frm.set_value('profitpack', 0);
    frm.set_value('actual_profit_percent', 0);
}

// Child table event handlers for Pre-Budget - Yarn and Accessories
frappe.ui.form.on('Pre-Budget - Yarn and Accessories', {
    rate: function(frm, cdt, cdn) {
        calculate_row_amount(cdt, cdn);
        recalculate_totals(frm);
        recalculate_fg_wise(frm);
    },
    
    total_qty: function(frm, cdt, cdn) {
        calculate_row_amount(cdt, cdn);
        recalculate_totals(frm);
        recalculate_fg_wise(frm);
    },
    
    table_itma_remove: function(frm) {
        recalculate_totals(frm);
        recalculate_fg_wise(frm);
    },
    
    item_code: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.item_code && (!row.rate || row.rate === 0)) {
            frappe.call({
                method: 'erpnext_trackerx_customization.erpnext_trackerx_customization.doctype.pre_budgeting_and_planning.pre_budgeting_and_planning.get_item_price',
                args: {
                    item_code: row.item_code,
                    price_list: frappe.boot.sysdefaults.buying_price_list || 'Standard Buying'
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.model.set_value(cdt, cdn, 'rate', flt(r.message, 2));
                        calculate_row_amount(cdt, cdn);
                        recalculate_totals(frm);
                        recalculate_fg_wise(frm);
                    }
                }
            });
        }
    }
});

// Calculate amount for a single row (total_qty × rate)
function calculate_row_amount(cdt, cdn) {
    let row = locals[cdt][cdn];
    if (!row) return;
    
    const total_qty = flt(row.total_qty) || 0;
    const rate = flt(row.rate) || 0;
    const amount = total_qty * rate;
    
    frappe.model.set_value(cdt, cdn, 'currency', flt(amount, 2));
}

// Fetch process data from CMT Planning using CATEGORY field
function fetch_process_data(frm) {
    if (!frm.doc.style || !frm.doc.sales_order || !frm.doc.category) {
        console.log('Skipping process fetch: missing required fields');
        return;
    }
    
    frm.call({
        method: 'erpnext_trackerx_customization.erpnext_trackerx_customization.doctype.pre_budgeting_and_planning.pre_budgeting_and_planning.fetch_process_from_cmt_planning',
        args: {
            style: frm.doc.style,
            sales_order: frm.doc.sales_order,
            category: frm.doc.category
        },
        freeze: true,
        freeze_message: __('Loading process data from CMT Planning...'),
        callback: function(r) {
            frm.clear_table('table_wfui');
            
            if (r.message && r.message.length > 0) {
                r.message.forEach(row => {
                    frm.add_child('table_wfui', row);
                });
                frm.refresh_field('table_wfui');
                
                const fgItemCount = [...new Set(r.message.map(r => r.fg_item))].length;
                frappe.show_alert({
                    message: __('Loaded {0} process rows across {1} FG items', [
                        r.message.length,
                        fgItemCount
                    ]),
                    indicator: 'green'
                });
            } else {
                frappe.show_alert({
                    message: __('No process data found for category: {0}', [frm.doc.category]),
                    indicator: 'orange'
                });
            }
            
            recalculate_totals(frm);
            recalculate_fg_wise(frm);
        }
    });
}

// Recalculate ALL parent totals including profit calculations
function recalculate_totals(frm) {
    let total_yarn = 0;
    let total_accessories = 0;
    let total_process = 0;
    
    // Yarn/Accessories calculation
    (frm.doc.table_itma || []).forEach(row => {
        const item_type = (row.item_type || '').toLowerCase().trim();
        const amount = flt(row.currency) || 0;
        
        if (item_type === 'yarns') {
            total_yarn += amount;
        } else if (item_type === 'accessories') {
            total_accessories += amount;
        }
    });
    
    // Process costs calculation
    (frm.doc.table_wfui || []).forEach(row => {
        total_process += flt(row.amount) || 0;
    });
    
    // Update cost fields
    frm.set_value('total_yarn_cost', flt(total_yarn, 2));
    frm.set_value('total_accessories_cost', flt(total_accessories, 2));
    frm.set_value('process_cost', flt(total_process, 2));
    frm.set_value('total_cost', flt(total_yarn + total_accessories + total_process, 2));
    
    // Calculate Grand Total with overhead
    const overhead_pct = flt(frm.doc.overhead_) || 0;
    const base_total = flt(total_yarn) + flt(total_accessories) + flt(total_process);
    const grand_total = base_total * (1 + overhead_pct / 100);
    frm.set_value('grand_total', flt(grand_total, 2));
    
    // ===== PROFIT CALCULATIONS (using SO-derived values) =====
    const total_qty = flt(frm.doc.total_qty) || 0;
    const actual_sales_amount = flt(frm.doc.actual_sales_amount) || 0;
    const grand_total_val = flt(grand_total);
    
    // Sale/Pack = Actual Sales Amount / Total Qty
    let salepack = 0;
    if (total_qty > 0) {
        salepack = actual_sales_amount / total_qty;
    }
    frm.set_value('salepack', flt(salepack, 2));
    
    // Budget Price per Pack = Grand Total / Total Qty
    let budget_price_per_pack = 0;
    if (total_qty > 0) {
        budget_price_per_pack = grand_total_val / total_qty;
    }
    frm.set_value('budget_price_per_pack', flt(budget_price_per_pack, 2));
    
    // Actual Profit = Actual Sales Amount - Grand Total
    const actual_profit = actual_sales_amount - grand_total_val;
    frm.set_value('actual_profit', flt(actual_profit, 2));
    
    // Profit/Pack = Actual Profit / Total Qty
    let profitpack = 0;
    if (total_qty > 0) {
        profitpack = actual_profit / total_qty;
    }
    frm.set_value('profitpack', flt(profitpack, 2));
    
    // Actual Profit % = (Actual Profit / Actual Sales Amount) * 100
    let actual_profit_percent = 0;
    if (actual_sales_amount > 0) {
        actual_profit_percent = (actual_profit / actual_sales_amount) * 100;
    }
    frm.set_value('actual_profit_percent', flt(actual_profit_percent, 2));
    // ================================
}

// Child table: Pre-Budget - Process
frappe.ui.form.on('Pre-Budget - Process', {
    rate: function(frm, cdt, cdn) {
        calculate_process_row_amount(cdt, cdn);
        recalculate_totals(frm);
        recalculate_fg_wise(frm);
    },
    qty: function(frm, cdt, cdn) {
        calculate_process_row_amount(cdt, cdn);
        recalculate_totals(frm);
        recalculate_fg_wise(frm);
    },
    table_wfui_remove: function(frm) {
        recalculate_totals(frm);
        recalculate_fg_wise(frm);
    }
});

// Calculate amount for process row (qty × rate)
function calculate_process_row_amount(cdt, cdn) {
    let row = locals[cdt][cdn];
    if (!row) return;
    
    const qty = flt(row.qty) || 0;
    const rate = flt(row.rate) || 0;
    const amount = qty * rate;
    
    frappe.model.set_value(cdt, cdn, 'amount', flt(amount, 2));
}

// Recalculate and populate Pre-Budget FG Wise table (table_hwmy)
function recalculate_fg_wise(frm) {
    // Get all unique FG items from yarn/accessories table
    const fg_items = {};
    
    // 1. Aggregate yarn/accessories costs by FG item
    (frm.doc.table_itma || []).forEach(row => {
        const fg_item = row.fg_item || '';
        if (!fg_item) return;
        
        if (!fg_items[fg_item]) {
            fg_items[fg_item] = {
                fg_item: fg_item,
                fg_qty: 0,
                fg_material_cost: 0,
                accessories_cost: 0,
                fg_process_cost: 0,
                bom: ''
            };
        }
        
        // Use first occurrence's fg_qty
        if (fg_items[fg_item].fg_qty === 0) {
            fg_items[fg_item].fg_qty = flt(row.fg_qty) || 0;
        }
        
        // Classify costs
        const amount = flt(row.currency) || 0;
        const item_type = (row.item_type || '').toLowerCase().trim();
        
        if (item_type === 'yarns') {
            fg_items[fg_item].fg_material_cost += amount;
        } else if (item_type === 'accessories') {
            fg_items[fg_item].accessories_cost += amount;
        }
    });
    
    // 2. Aggregate process costs by FG item
    (frm.doc.table_wfui || []).forEach(row => {
        const fg_item = row.fg_item || '';
        if (!fg_item || !fg_items[fg_item]) return;
        
        fg_items[fg_item].fg_process_cost += flt(row.amount) || 0;
    });
    
    // 3. Prepare FG list for table update
    const fg_item_list = Object.values(fg_items);
    
    // 4. Fetch BOMs asynchronously
    fg_item_list.forEach(fg => {
        if (fg.fg_item && !fg.bom) {
            frappe.db.get_value('BOM', {
                'item': fg.fg_item,
                'is_active': 1,
                'docstatus': 1
            }, 'name', null, {
                order_by: 'is_default DESC, creation DESC'
            }).then(r => {
                if (r.message && r.message.name) {
                    const fg_row = fg_item_list.find(item => item.fg_item === fg.fg_item);
                    if (fg_row) {
                        fg_row.bom = r.message.name;
                        update_fg_wise_table(frm, fg_item_list);
                    }
                }
            }).catch(e => {
                console.warn('Error fetching BOM for', fg.fg_item, ':', e);
            });
        }
    });
    
    // 5. Calculate final costs
    fg_item_list.forEach(fg => {
        fg.fg_total_cost = flt(fg.fg_material_cost) + flt(fg.accessories_cost) + flt(fg.fg_process_cost);
        fg.fg_costpc = fg.fg_qty > 0 ? (fg.fg_total_cost / fg.fg_qty) : 0;
    });
    
    // 6. Update table
    update_fg_wise_table(frm, fg_item_list);
}

// Helper: Update FG Wise child table with calculated data
function update_fg_wise_table(frm, fg_item_list) {
    frm.clear_table('table_hwmy');
    
    fg_item_list.forEach(fg => {
        const row = frm.add_child('table_hwmy', {
            fg_item: fg.fg_item,
            fg_qty: flt(fg.fg_qty, 2),
            bom: fg.bom || '',
            fg_material_cost: flt(fg.fg_material_cost, 2),
            accessories_cost: flt(fg.accessories_cost, 2),
            fg_process_cost: flt(fg.fg_process_cost, 2),
            fg_total_cost: flt(fg.fg_total_cost, 2),
            fg_costpc: flt(fg.fg_costpc, 2)
        });
    });
    
    frm.refresh_field('table_hwmy');
}