frappe.ui.form.on('BOM', {
    validate(frm) {
        frappe.model.clear_table(frm.doc, 'items');

        const merge_items = (source_table, item_type) => {
            (frm.doc[source_table] || []).forEach(row => {
                let new_row = frm.add_child('items');

                // Copy only necessary fields
                new_row.item_code = row.item_code;
                new_row.item_name = row.item_name;
                new_row.uom = row.uom;
                new_row.qty = row.qty;
                new_row.rate = row.rate;
                new_row.amount = row.amount;
                new_row.description = row.description;
                new_row.stock_uom = row.stock_uom;
                new_row.custom_item_type = item_type;

                // Copy any other custom fields you’re using here if needed
            });
        };

        merge_items('custom_fabrics_items', 'Fabrics');
        merge_items('custom_trims_items', 'Trims');
        merge_items('custom_accessories_items', 'Accessories');

         // 🔴 Clear the UI-only virtual tables so they don't save to DB
        frappe.model.clear_table(frm.doc, 'custom_fabrics_items');
        frappe.model.clear_table(frm.doc, 'custom_trims_items');
        frappe.model.clear_table(frm.doc, 'custom_accessories_items');
    },
     refresh(frm) {
        // Repopulate tables after save
        frm.events.sync_virtual_tables(frm);
    },
    after_save(frm) {
        frm.reload_doc().then(() => {
            frm.events.sync_virtual_tables(frm);
        });
    },

    onload_post_render(frm) {
        frm.events.sync_virtual_tables(frm);
    },

    sync_virtual_tables(frm) {
        frappe.model.clear_table(frm.doc, 'custom_fabrics_items');
        frappe.model.clear_table(frm.doc, 'custom_trims_items');
        frappe.model.clear_table(frm.doc, 'custom_accessories_items');

        (frm.doc.items || []).forEach(row => {
            let target_table = null;
            switch (row.custom_item_type) {
                case 'Fabrics': target_table = 'custom_fabrics_items'; break;
                case 'Trims': target_table = 'custom_trims_items'; break;
                case 'Accessories': target_table = 'custom_accessories_items'; break;
            }

            if (target_table) {
                let new_row = frm.add_child(target_table);

                new_row.item_code = row.item_code;
                new_row.item_name = row.item_name;
                new_row.uom = row.uom;
                new_row.qty = row.qty;
                new_row.rate = row.rate;
                new_row.amount = row.amount;
                new_row.description = row.description;
                new_row.stock_uom = row.stock_uom;
                new_row.custom_item_type = row.custom_item_type;
            }
        });

        frm.refresh_field('custom_fabrics_items');
        frm.refresh_field('custom_trims_items');
        frm.refresh_field('custom_accessories_items');
    }
});
