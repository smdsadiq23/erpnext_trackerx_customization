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
                    frappe.model.set_value(cdt, cdn, "custom_selected_warehouse", warehouse);
                    frappe.model.set_value(cdt, cdn, "warehouse", warehouse);
                    d.hide();
                }
            });

            d.show();
        }
    });
}

// --- Recursive Child Loader ---
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

            const wrapper = dialog.fields_dict.html_levels.$wrapper;
            const label = __("Level {0}", [level]);

            renderBoxes(dialog, wrapper, children, label, (dlg, child) => {
                dlg.selected_bin = null;
                loadChildrenRecursive(dlg, child, level + 1);
            });
        }
    });
}

// --- Render clickable boxes ---
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
