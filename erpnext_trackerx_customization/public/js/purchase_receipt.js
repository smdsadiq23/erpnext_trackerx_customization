frappe.ui.form.on('Purchase Receipt', {
    refresh(frm) {
        const grid = frm.fields_dict["items"]?.grid;
        if (grid && grid.wrapper) {
            grid.wrapper.off('click', '.grid-row [data-fieldname="custom_selected_warehouse"] input');
            grid.wrapper.on('click', '.grid-row [data-fieldname="custom_selected_warehouse"] input', function () {
                const row = $(this).closest('.grid-row');
                const cdn = row.data('name');
                if (cdn) {
                    openLocationDialog(frm, 'Purchase Receipt Item', cdn);
                }
            });
        }
    }
});

// --- Warehouse Selection Dialog for Purchase Receipt ---
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
                            if (!ROOT) return;

                            // Fetch Zones under selected root
                            frappe.call({
                                method: "frappe.desk.treeview.get_children",
                                args: { doctype: "Warehouse", parent: ROOT },
                                callback: function (res2) {
                                    const zones = (res2.message || []).map(x => x.value);
                                    const labels = buildLabelSequence("Zone");
                                    d.fields_dict.html_zone.$wrapper.empty();
                                    renderBoxes(d, d.fields_dict.html_zone.$wrapper, zones, labels[0], zoneSelected);
                                }
                            });
                        }
                    },
                    { fieldname: "html_zone", fieldtype: "HTML" },
                    { fieldname: "html_rack", fieldtype: "HTML" },
                    { fieldname: "html_level", fieldtype: "HTML" },
                    { fieldname: "html_bin", fieldtype: "HTML" }
                ],
                primary_action_label: __("Set Warehouse"),
                primary_action(values) {
                    let warehouse = d.selected_bin || "";
                    if (!warehouse) {
                        frappe.msgprint(__("Please select a location"));
                        return;
                    }
                    frappe.model.set_value(cdt, cdn, "custom_selected_warehouse", warehouse);
                    frappe.model.set_value(cdt, cdn, "warehouse", warehouse);
                    d.hide();
                }
            });

            d.show();
        }
    });
}

// --- Supporting Functions ---
function renderBoxes(dialog, wrapper, items, label, clickHandler, selected) {
    if (!items || !items.length) {
        wrapper.html(`<div><b>${label}:</b> ${__("No options available")}</div>`);
        return;
    }
    let html = `<div><b>${label}:</b></div><div style="display: flex; flex-wrap: wrap; gap: 10px;">`;
    html += items.map(i => `
        <div class="wh-box ${selected === i ? "active" : ""}" 
             data-value="${i}"
             style="padding: 6px 12px; border: 1px solid #ccc; border-radius: 6px;
                    cursor: pointer; background:${selected === i ? '#4B7BEC' : '#fff'};
                    color:${selected === i ? '#fff' : '#000'};">
            ${i}
        </div>`).join("");
    html += "</div>";
    wrapper.html(html);

    wrapper.find(".wh-box").on("click", function () {
        wrapper.find(".wh-box").removeClass("active").css({ background: "#fff", color: "#000" });
        $(this).addClass("active").css({ background: "#96be37", color: "#fff" });
        clickHandler(dialog, $(this).data("value"));
    });
}

function zoneSelected(dialog, zone) {
    dialog.selected_zone = zone;
    loadChildren(zone, (racks) => {
        renderBoxes(dialog, dialog.fields_dict.html_rack.$wrapper, racks, "Rack", rackSelected);
    });
}

function rackSelected(dialog, rack) {
    dialog.selected_rack = rack;
    loadChildren(rack, (levels) => {
        renderBoxes(dialog, dialog.fields_dict.html_level.$wrapper, levels, "Level", levelSelected);
    });
}

function levelSelected(dialog, level) {
    dialog.selected_level = level;
    loadChildren(level, (bins) => {
        renderBoxes(dialog, dialog.fields_dict.html_bin.$wrapper, bins, "Bin", binSelected);
    });
}

function binSelected(dialog, bin) {
    dialog.selected_bin = bin;
}

function loadChildren(parentName, callback) {
    frappe.call({
        method: "frappe.desk.treeview.get_children",
        args: { doctype: "Warehouse", parent: parentName },
        callback(res) {
            let opts = (res.message || []).map(x => x.value);
            callback(opts);
        }
    });
}

function buildLabelSequence(start) {
    const seq = ["Zone", "Rack", "Level", "Bin"];
    const idx = seq.indexOf(start);
    return idx === -1 ? seq : seq.slice(idx);
}
