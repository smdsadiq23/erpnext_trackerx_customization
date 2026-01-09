// Copyright (c) 2025, CognitionX and contributors
// For license information, please see license.txt

frappe.ui.form.on("Goods Receipt Note", {
    refresh(frm) {
        // Only run for new documents
        if (frm.doc.__islocal && (frm.doc.document_checklist?.length || 0) === 0) {
            const standard_docs = [
                'Delivery Challan / Invoice',
                'Packing List',
                'Material Test Certificate (MTC)',
                'Inspection Report',
                'Gate Entry Register / Inward Register'
            ];

            const optional_docs = [
                'Purchase Order',
                'GRN Document (System-Generated)',
                'Advance Shipping Notice (ASN)',
                'Waybill / Transport Document',
                'Certificate of Conformance (CoC)'
            ];

            // Add standard (required) documents
            standard_docs.forEach(doc => {
                const row = frm.add_child('document_checklist');
                frappe.model.set_value(row.doctype, row.name, 'document_type', doc);
                frappe.model.set_value(row.doctype, row.name, 'is_required', 1);
            });

            // Add optional documents (not mandatory)
            optional_docs.forEach(doc => {
                const row = frm.add_child('document_checklist');
                frappe.model.set_value(row.doctype, row.name, 'document_type', doc);
                frappe.model.set_value(row.doctype, row.name, 'is_required', 0);
            });

            frm.refresh_field('document_checklist');
        }
        set_item_code_query(frm);

        // Set up click handler for selected_warehouse after grid is rendered
        const grid = frm.fields_dict["items"]?.grid;
        if (grid && grid.wrapper) {
            grid.wrapper.off('click', '.grid-row [data-fieldname="selected_warehouse"] input');
            grid.wrapper.on('click', '.grid-row [data-fieldname="selected_warehouse"] input', function () {
                const row = $(this).closest('.grid-row');
                const cdn = row.data('name');
                if (cdn) {
                    openLocationDialog(frm, 'Goods Receipt Item', cdn);
                }
            });
        }
    },

    onload(frm) {
        buildHierarchy("Test Warehouse - Logic", "zones", function (tree) {
            console.log("Final Warehouse Hierarchy:", tree);
        }); 
        
        frm.set_query('fg_item', () => ({
            filters: { name: ['=', ''] } // Impossible filter → empty list
        }));
    },

    validate(frm) {
        const missing_required = [];
        const missing_date = [];

        (frm.doc.document_checklist || []).forEach(function (row) {
            if (row.is_required && !row.received) {
                missing_required.push(row.document_type);
            }
            if (row.received && !row.received_date) {
                missing_date.push(row.document_type);
            }
        });

        if (missing_required.length > 0) {
            frappe.throw(__("The following required documents are not marked as received:<br>{0}", [missing_required.map(d => `<li>${d}</li>`).join('')]));
        }

        if (missing_date.length > 0) {
            frappe.throw(__("Received Date is mandatory for:<br>{0}", [missing_date.map(d => `<li>${d}</li>`).join('')]));
        }
    },

    purchase_order(frm) {
        if (!frm.doc.purchase_order) return;

        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Purchase Order',
                name: frm.doc.purchase_order
            },
            callback(r) {
                if (r.message) {
                    const po = r.message;
                    const po_items = po.items || [];

                    frm.clear_table('items');

                    let promises = po_items.map(po_item => {
                        return frappe.db.get_doc('Item', po_item.item_code)
                            .then(item_doc => {
                                const row = frm.add_child('items');
                                frappe.model.set_value(row.doctype, row.name, 'item_code', po_item.item_code);
                                frappe.model.set_value(row.doctype, row.name, 'item_name', po_item.item_name);
                                frappe.model.set_value(row.doctype, row.name, 'ordered_quantity', po_item.qty);
                                frappe.model.set_value(row.doctype, row.name, 'amount', po_item.rate);
                                frappe.model.set_value(row.doctype, row.name, 'uom', po_item.uom);

                                frappe.model.set_value(row.doctype, row.name, 'color', item_doc.custom_colour_name);
                                frappe.model.set_value(row.doctype, row.name, 'composition', item_doc.custom_material_composition);
                                frappe.model.set_value(row.doctype, row.name, 'material_type', item_doc.custom_select_master);

                                if (frm.doc.set_warehouse) {
                                    frappe.model.set_value(row.doctype, row.name, 'accepted_warehouse', frm.doc.set_warehouse);
                                }
                            });
                    });

                    Promise.all(promises).then(() => {
                        frm.refresh_field('items');
                        set_item_code_query(frm);
                    });
                }
            }
        });
    },

    set_warehouse(frm) {
        if (!frm.doc.set_warehouse) return;

        (frm.doc.items || []).forEach(row => {
            frappe.model.set_value(row.doctype, row.name, 'accepted_warehouse', frm.doc.set_warehouse);
        });

        frm.refresh_field('items');
    },

    before_save(frm) {
        (frm.doc.document_checklist || []).forEach(row => {
            if (row.photo_upload && row.document_type === 'Photo Evidence') {
                frappe.model.set_value(row.doctype, row.name, 'attached_to_doctype', 'Goods Receipt Note');
                frappe.model.set_value(row.doctype, row.name, 'attached_to_name', frm.doc.name);
            }
        });
    },

    items_add(frm, cdt, cdn) {
        if (frm.doc.set_warehouse) {
            frappe.model.set_value(cdt, cdn, 'accepted_warehouse', frm.doc.set_warehouse);
        }
        set_item_code_query(frm);
        update_total_received_quantity(frm);
    },

    ocn: function(frm) {
        // Clear fg_item when ocn changes (good UX)
        frm.set_value('fg_item', '');

        if (!frm.doc.ocn) {
            // Blank filter if no OCN
            frm.set_query('fg_item', () => ({ filters: { name: ['=', ''] } }));
            return;
        }

        // Fetch FG items linked to this OCN (Sales Order)
        frappe.call({
            method: 'erpnext_trackerx_customization.erpnext_trackerx_customization.doctype.goods_receipt_note.goods_receipt_note.get_fg_items_by_ocn',
            args: { ocn: frm.doc.ocn },
            callback: function(r) {
                const allowed_items = r.message || [];

                // Apply dynamic filter on fg_item
                frm.set_query('fg_item', () => ({
                    filters: allowed_items.length 
                        ? { name: ['in', allowed_items] } 
                        : { name: ['=', ''] }
                }));

                if (allowed_items.length === 0) {
                    frappe.msgprint(__('No finished goods items found for OCN {0}', [frm.doc.ocn]));
                }
            }
        });
    },

    fg_item: function(frm) {
        frm.clear_table('items');
        frm.refresh_field('items');

        if (!frm.doc.fg_item) {
            // Show nothing when fg_item is cleared
            frm.set_query('item_code', 'items', () => ({
                filters: { name: ['=', ''] }
            }));
            return;
        }

        frappe.call({
            method: 'erpnext_trackerx_customization.erpnext_trackerx_customization.doctype.goods_receipt_note.goods_receipt_note.get_fabric_items_from_fg_bom',
            args: { fg_item: frm.doc.fg_item },
            callback: function(r) {
                const allowed_items = r.message || [];

                frm.set_query('item_code', 'items', () => ({
                    filters: allowed_items.length 
                        ? { name: ['in', allowed_items] } 
                        : { name: ['=', ''] }
                }));

                if (allowed_items.length === 0) {
                    frappe.msgprint(__('No fabric items found in the default BOM for {0}', [frm.doc.fg_item]));
                }
            }
        });
    }
});

// Only allow PO items as item_code
function set_item_code_query(frm) {
    let po = frm.doc.purchase_order;
    if (!po) {
        frm.fields_dict['items'].grid.get_field('item_code').get_query = function () { return {}; };
        return;
    }
    frappe.call({
        method: "frappe.client.get",
        args: {
            doctype: "Purchase Order",
            name: po
        },
        callback: function (r) {
            if (r.message) {
                let valid_items = (r.message.items || []).map(item => item.item_code);
                frm.fields_dict['items'].grid.get_field('item_code').get_query = function (doc, cdt, cdn) {
                    return {
                        filters: [
                            ['Item', 'item_code', 'in', valid_items]
                        ]
                    };
                };
                frm.refresh_field('items');
            }
        }
    });
}

// --- Goods Receipt Item Child Table Events ---
frappe.ui.form.on("Goods Receipt Item", {
    items_add(frm, cdt, cdn) {
        update_total_received_quantity(frm);
    },    
    items_remove(frm) {
        update_total_received_quantity(frm);
    },    
    received_quantity(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        const amount = (row.received_quantity || 0) * (row.rate || 0);
        frappe.model.set_value(cdt, cdn, 'amount', amount);
        update_total_received_quantity(frm);
    },
    rate(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        const amount = (row.received_quantity || 0) * (row.rate || 0);
        frappe.model.set_value(cdt, cdn, 'amount', amount);
    },
    // 👇 NEW: Auto-fill color & composition when item_code changes
    item_code(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        const item_code = row.item_code;

        if (!item_code) {
            frappe.model.set_value(cdt, cdn, 'color', '');
            frappe.model.set_value(cdt, cdn, 'composition', '');
            frappe.model.set_value(cdt, cdn, 'material_type', '');
            return;
        }

        frappe.db.get_doc('Item', item_code)
            .then(item_doc => {
                frappe.model.set_value(cdt, cdn, 'color', item_doc.custom_colour_name || '');
                frappe.model.set_value(cdt, cdn, 'composition', item_doc.custom_material_composition || '');
                frappe.model.set_value(cdt, cdn, 'material_type', item_doc.custom_select_master || '');
            })
            .catch(err => {
                console.warn("Could not fetch Item details for:", item_code, err);
                // Optionally show a message
                frappe.msgprint({
                    title: __("Item Not Found"),
                    indicator: "orange",
                    message: __("Could not load details for item {0}", [item_code])
                });
            });
    }    
});

function update_total_received_quantity(frm) {
    let total = 0;
    (frm.doc.items || []).forEach(row => {
        total += flt(row.received_quantity);
    });
    frm.set_value('total_received_quantity', total);
}

// --- Checklist Table Events ---
frappe.ui.form.on('Goods Receipt Document Checklist', {
    received(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.received) {
            const default_date = frm.doc.transaction_date || frappe.datetime.nowdate();
            if (!row.received_date) {
                frappe.model.set_value(cdt, cdn, 'received_date', default_date);
            }
        } else {
            if (row.received_date) {
                frappe.model.set_value(cdt, cdn, 'received_date', '');
            }
        }
    },

    received_date(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.received && !row.received_date) {
            frappe.msgprint(__('Received Date is mandatory when document is marked as received.'));
            frappe.model.set_value(cdt, cdn, 'received', 0);
        }
    }
});

// --- Warehouse Selection Dialog ---
// function openLocationDialog(frm, cdt, cdn) {
//     let ROOT = ""; // Empty by default

//     frappe.call({
//         method: "frappe.client.get_list",
//         args: {
//             doctype: "Warehouse",
//             fields: ["name"],
//             filters: {
//                 "warehouse_type": "Main Warehouse"
//             },
//             limit_page_length: 100
//         },
//         callback: function(res) {
//             const warehouses = res.message || [];
//             console.log("Warehouse list:", warehouses);

//             let d = new frappe.ui.Dialog({
//                 title: __("Select Warehouse Location"),
//                 size: "large",
//                 fields: [
//                     {
//                         fieldname: "root_warehouse",
//                         fieldtype: "Select",
//                         label: __("Root Warehouse"),
//                         options: warehouses.map(w => w.name),
//                         default: ROOT,
//                         onchange: function() {
//                             ROOT = d.get_value("root_warehouse");
//                             console.log("Selected root warehouse:", ROOT);
//                             if (!ROOT) {
//                                 // Clear all fields if ROOT is empty
//                                 console.log("ROOT is empty, clearing fields");
//                                 d.fields_dict.html_zone.$wrapper.html(`<div><b>Zone:</b> ${__("No options available")}</div>`);
//                                 d.fields_dict.html_rack.$wrapper.empty();
//                                 d.fields_dict.html_level.$wrapper.empty();
//                                 d.fields_dict.html_bin.$wrapper.empty();
//                                 return;
//                             }
//                             // Fetch and render children
//                             frappe.call({
//                                 method: "frappe.desk.treeview.get_children",
//                                 args: { doctype: "Warehouse", parent: ROOT },
//                                 callback: function(res2) {
//                                     console.log("Children response for", ROOT, ":", res2);
//                                     const top = (res2 && res2.message) ? res2.message : [];
//                                     if (!top.length) {
//                                         frappe.msgprint(__('No children found under {0}', [ROOT]));
//                                         d.fields_dict.html_zone.$wrapper.html(`<div><b>Zone:</b> ${__("No options available")}</div>`);
//                                         d.fields_dict.html_rack.$wrapper.empty();
//                                         d.fields_dict.html_level.$wrapper.empty();
//                                         d.fields_dict.html_bin.$wrapper.empty();
//                                         return;
//                                     }
//                                     const firstLabel = detectLabelFromNames(top.map(n => n.value));
//                                     const labels = buildLabelSequence(firstLabel);
//                                     console.log("Rendering zones with label:", firstLabel, "items:", top.map(x => x.value));
//                                     d.fields_dict.html_zone.$wrapper.empty();
//                                     d.fields_dict.html_rack.$wrapper.empty();
//                                     d.fields_dict.html_level.$wrapper.empty();
//                                     d.fields_dict.html_bin.$wrapper.empty();
//                                     renderBoxes(d, d.fields_dict.html_zone.$wrapper, top.map(x => x.value), labels[0], zoneSelected);
//                                 },
//                                 error: function(err) {
//                                     console.error("Error fetching children for", ROOT, ":", err);
//                                     frappe.msgprint({
//                                         title: __("Error"),
//                                         indicator: "red",
//                                         message: __("Failed to load children for {0}", [ROOT])
//                                     });
//                                 }
//                             });
//                         }
//                     },
//                     { fieldname: "html_zone", fieldtype: "HTML" },
//                     { fieldname: "html_rack", fieldtype: "HTML" },
//                     { fieldname: "html_level", fieldtype: "HTML" },
//                     { fieldname: "html_bin", fieldtype: "HTML" }
//                 ],
//                 primary_action_label: __("Set Warehouse"),
//                 primary_action(values) {
//                     let warehouse = d.selected_bin || "";
//                     if (!warehouse) {
//                         frappe.msgprint(__("Please select a location"));
//                         return;
//                     }
//                     // Set both selected_warehouse and accepted_warehouse to the same bin value
//                     frappe.model.set_value(cdt, cdn, "selected_warehouse", warehouse);
//                     frappe.model.set_value(cdt, cdn, "accepted_warehouse", warehouse);
//                     d.hide();
//                 }
//             });

//             d.show();

//             // Only fetch children if ROOT is not empty
//             if (ROOT) {
//                 frappe.call({
//                     method: "frappe.desk.treeview.get_children",
//                     args: { doctype: "Warehouse", parent: ROOT },
//                     callback: function(res) {
//                         console.log("Initial children response for", ROOT, ":", res);
//                         const top = (res && res.message) ? res.message : [];
//                         if (!top.length) {
//                             frappe.msgprint(__('No children found under {0}', [ROOT]));
//                             return;
//                         }
//                         const firstLabel = detectLabelFromNames(top.map(n => n.value));
//                         const labels = buildLabelSequence(firstLabel);
//                         console.log("Initial rendering zones with label:", firstLabel, "items:", top.map(x => x.value));
//                         renderBoxes(d, d.fields_dict.html_zone.$wrapper, top.map(x => x.value), labels[0], zoneSelected);
//                     },
//                     error: function(err) {
//                         console.error("Error fetching initial children for", ROOT, ":", err);
//                         frappe.msgprint({
//                             title: __("Error"),
//                             indicator: "red",
//                             message: __("An error occurred while loading warehouse data")
//                         });
//                     }
//                 });
//             } else {
//                 // Display "No options available" for all fields if ROOT is empty
//                 console.log("ROOT is empty on load, setting no options");
//                 d.fields_dict.html_zone.$wrapper.html(`<div><b>Zone:</b> ${__("No options available")}</div>`);
//                 d.fields_dict.html_rack.$wrapper.empty();
//                 d.fields_dict.html_level.$wrapper.empty();
//                 d.fields_dict.html_bin.$wrapper.empty();
//             }
//         },
//         error: function(err) {
//             console.error("Error fetching warehouse list:", err);
//         }
//     });
// }

// --- Supporting Functions ---
// function renderBoxes(dialog, wrapper, items, label, clickHandler, selected) {
//     if (!items || !items.length) {
//         wrapper.html(`<div><b>${label}:</b> ${__("No options available")}</div>`);
//         return;
//     }
//     let html = `<div><b>${label}:</b></div><div style="display: flex; flex-wrap: wrap; gap: 10px; margin-top: 5px; margin-bottom:10px">`;
//     html += items.map(i => `
//         <div class="wh-box ${selected === i ? "active" : ""}" 
//              data-value="${i}"
//              style="padding: 10px 15px; border: 1px solid #ccc; border-radius: 6px; 
//                     cursor: pointer; text-align: center;
//                     background: ${selected === i ? '#4B7BEC' : '#fff'};
//                     color: ${selected === i ? '#fff' : '#000'};">
//             ${i}
//         </div>`
//     ).join("");
//     html += "</div>";
//     wrapper.html(html);

//     wrapper.find(".wh-box").on("click", function() {
//         wrapper.find(".wh-box").removeClass("active")
//             .css({ background: "#fff", color: "#000" });
//         $(this).addClass("active")
//             .css({ background: "#96be37", color: "#fff" });
//         clickHandler(dialog, $(this).data("value"));
//     });
// }

function openLocationDialog(frm, cdt, cdn) {
    let ROOT = "";

    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "Warehouse",
            fields: ["name"],
            filters: { "warehouse_type": "Main Warehouse" },
            limit_page_length: 100
        },
        callback: function (res) {
            const warehouses = res.message || [];

            let d = new frappe.ui.Dialog({
                title: __("Select Warehouse Location"),
                size: "large",
                fields: [
                    {
                        fieldname: "root_warehouse",
                        fieldtype: "Select",
                        label: __("Root Warehouse"),
                        options: warehouses.map(w => w.name),
                        default: ROOT,
                        onchange: function () {
                            ROOT = d.get_value("root_warehouse");
                            d.fields_dict.html_levels.$wrapper.empty();
                            d.selected_bin = null;

                            if (ROOT) {
                                loadChildrenRecursive(d, ROOT, 1);
                            }
                        }
                    },
                    { fieldname: "html_levels", fieldtype: "HTML" }
                ],
                primary_action_label: __("Set Warehouse"),
                primary_action() {
                    let warehouse = d.selected_bin || "";
                    if (!warehouse) {
                        frappe.msgprint(__("Please select a Bin (final level)"));
                        return;
                    }
                    frappe.model.set_value(cdt, cdn, "selected_warehouse", warehouse);
                    frappe.model.set_value(cdt, cdn, "accepted_warehouse", warehouse);
                    d.hide();
                }
            });

            d.show();
        }
    });
}

// Recursive loader: strict Level 1,2,3… then Bin
function loadChildrenRecursive(dialog, parentName, level) {
    frappe.call({
        method: "frappe.desk.treeview.get_children",
        args: { doctype: "Warehouse", parent: parentName },
        callback(res) {
            const children = (res && res.message) ? res.message.map(x => x.value) : [];

            if (!children.length) {
                // no children → this is a Bin
                dialog.selected_bin = parentName;
                frappe.msgprint(__("Selected Bin: {0}", [parentName]));
                return;
            }

            // label = Level N, unless we are at leaf → Bin
            const wrapper = dialog.fields_dict.html_levels.$wrapper;
            const label = (children.every(c => isLeaf(c)))
                ? __("Bin")
                : __("Level {0}", [level]);

            renderBoxes(dialog, wrapper, children, label, (dlg, child) => {
                dlg.selected_bin = null;
                loadChildrenRecursive(dlg, child, level + 1);
            });
        }
    });
}

function renderBoxes(dialog, wrapper, items, label, clickHandler) {
    let html = `
        <div><b>${label}:</b></div>
        <div style="display:flex; flex-wrap:wrap; gap:10px; margin:5px 0 15px">
            ${items.map(i => `
                <div class="wh-box"
                     data-value="${i}"
                     style="padding:8px 14px; border:1px solid #ccc; border-radius:6px;
                            cursor:pointer; background:#fff; color:#000;">
                    ${i}
                </div>`).join("")}
        </div>`;
    wrapper.append(html);

    wrapper.find(".wh-box").off("click").on("click", function () {
        wrapper.find(".wh-box").css({ background: "#fff", color: "#000" });
        $(this).css({ background: "#82a52f", color: "#fff" });
        clickHandler(dialog, $(this).data("value"));
    });
}

// Helper: check if node has children
function isLeaf(nodeName) {
    let hasChild = false;
    frappe.call({
        method: "frappe.desk.treeview.get_children",
        args: { doctype: "Warehouse", parent: nodeName },
        async: false,  // block check (safe because it’s just a small call)
        callback(res) {
            hasChild = !(res && res.message && res.message.length);
        }
    });
    return hasChild;
}


function zoneSelected(dialog, zone) {
    dialog.selected_zone = zone;
    dialog.selected_rack = null;
    dialog.selected_level = null;
    dialog.selected_bin = null;
    dialog.fields_dict.html_level.$wrapper.empty();
    dialog.fields_dict.html_bin.$wrapper.empty();
    console.log("Zone selected:", zone);

    loadChildren(zone, (racks) => {
        renderBoxes(dialog, dialog.fields_dict.html_rack.$wrapper, racks, "Rack", rackSelected);
    });
}

function rackSelected(dialog, rack) {
    dialog.selected_rack = rack;
    dialog.selected_level = null;
    dialog.selected_bin = null;
    dialog.fields_dict.html_level.$wrapper.empty();
    dialog.fields_dict.html_bin.$wrapper.empty();
    console.log("Rack selected:", rack);

    loadChildren(rack, (levels) => {
        renderBoxes(dialog, dialog.fields_dict.html_level.$wrapper, levels, "Level", levelSelected);
    });
}

function levelSelected(dialog, level) {
    dialog.selected_level = level;
    dialog.selected_bin = null;
    console.log("Level selected:", level);

    loadChildren(level, (bins) => {
        renderBoxes(dialog, dialog.fields_dict.html_bin.$wrapper, bins, "Bin", binSelected); // Fixed to html_bin
    });
}

function binSelected(dialog, bin) {
    dialog.selected_bin = bin;
    console.log("Bin selected:", bin);
}

function loadChildren(parentName, callback) {
    frappe.call({
        method: "frappe.desk.treeview.get_children",
        args: { doctype: "Warehouse", parent: parentName },
        callback(res2) {
            let opts = (res2 && res2.message) ? res2.message.map(x => x.value) : [];
            callback(opts);
        },
        error() {
            frappe.msgprint({
                title: __("Error"),
                indicator: "red",
                message: __("Failed to load children for {0}", [parentName])
            });
            callback([]);
        }
    });
}

function detectLabelFromNames(names) {
    const labelMap = {
        zone: ["zone", "area", "section"],
        rack: ["rack", "shelf", "stand"],
        level: ["level", "floor", "tier"],
        bin: ["bin", "slot", "cell"]
    };
    const low = names.join(" ").toLowerCase();
    for (let [label, keywords] of Object.entries(labelMap)) {
        if (keywords.some(k => low.includes(k))) return label.charAt(0).toUpperCase() + label.slice(1);
    }
    return "Zone";
}

function buildLabelSequence(start) {
    const seq = ["Zone", "Rack", "Level", "Bin"];
    const idx = seq.indexOf(start);
    if (idx === -1) return seq;
    const out = [];
    for (let i = idx; i < seq.length; i++) out.push(seq[i]);
    while (out.length < 4) out.push("Level");
    return out;
}


function buildHierarchy(parent, childKey, callback) {
    frappe.call({
        method: "frappe.desk.treeview.get_children",
        args: { doctype: "Warehouse", parent: parent },
        callback: function (r) {
            if (!r.message || r.message.length === 0) {
                callback({ name: parent });
                return;
            }
            let node = { name: parent };
            node[childKey] = [];
            let pending = r.message.length;
            r.message.forEach(child => {
                let nextKey = "bins";
                if (childKey === "zones") nextKey = "racks";
                else if (childKey === "racks") nextKey = "levels";
                else if (childKey === "levels") nextKey = "bins";
                buildHierarchy(child.value, nextKey, function (subtree) {
                    node[childKey].push(subtree);
                    if (--pending === 0) {
                        callback(node);
                    }
                });
            });
        },
        error() {
            frappe.msgprint({
                title: __("Error"),
                indicator: "red",
                message: __("An error occurred while building warehouse hierarchy")
            });
            callback({ name: parent });
        }
    });
}

function reset_item_filter(frm) {
    frm.set_query('item_code', 'items', () => ({ filters: {} }));
}