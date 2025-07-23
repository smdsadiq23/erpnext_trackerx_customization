frappe.ui.form.on('BOM', {
    validate(frm) {
        frappe.model.clear_table(frm.doc, 'items');




        const merge_items = (source_table, item_type) => {
            if((frm.doc[source_table] || []).length < 1)
            {
                frappe.throw(`Please add at least 1 row in <b>${item_type}</b> table.`);
            }
            (frm.doc[source_table] || []).forEach(row => {
                let new_row = frm.add_child('items');

                

                copy(new_row, row, item_type);

                // Copy any other custom fields you’re using here if needed
            });
        };

        merge_items('custom_fabrics_items', 'Fabrics');
        merge_items('custom_trims_items', 'Trims');
        merge_items('custom_accessories_items', 'Accessories');
        merge_items('custom_labels_items', 'Labels');
        merge_items('custom_packing_materials_items', 'Packing Materials');

         // 🔴 Clear the UI-only virtual tables so they don't save to DB
        frappe.model.clear_table(frm.doc, 'custom_fabrics_items');
        frappe.model.clear_table(frm.doc, 'custom_trims_items');
        frappe.model.clear_table(frm.doc, 'custom_accessories_items');
        frappe.model.clear_table(frm.doc, 'custom_labels_items');
        frappe.model.clear_table(frm.doc, 'custom_packing_materials_items');
    },
    onload(frm){
        frm.set_df_property('items', 'hidden', 1);

        //make qty fiedl in the bom item read only 
        modifyTheBOMItemTableFields(frm);

        set_item_code_filters(frm); 


    },
    custom_net_qty(frm, cdt, cdn) {
        calculate_qty_based_on_net_and_wastage(frm, cdt, cdn);
    },
    custom_wastage_percentage(frm, cdt, cdn) {
        calculate_qty_based_on_net_and_wastage(frm, cdt, cdn);
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
        frappe.model.clear_table(frm.doc, 'custom_labels_items');
        frappe.model.clear_table(frm.doc, 'custom_packing_materials_items');

        (frm.doc.items || []).forEach(row => {
            let target_table = null;
            switch (row.custom_item_type) {
                case 'Fabrics': target_table = 'custom_fabrics_items'; break;
                case 'Trims': target_table = 'custom_trims_items'; break;
                case 'Accessories': target_table = 'custom_accessories_items'; break;
                case 'Labels': target_table = 'custom_labels_items'; break;
                case 'Packing Materials': target_table = 'custom_packing_materials_items'; break;
            }

            if (target_table) {
                let new_row = frm.add_child(target_table);

              
                copy(new_row, row, row.custom_item_type)
            }
        });

        frm.refresh_field('custom_fabrics_items');
        frm.refresh_field('custom_trims_items');
        frm.refresh_field('custom_accessories_items');
        frm.refresh_field('custom_labels_items');
        frm.refresh_field('custom_packing_materials_items');
    }


});


 function copy(new_row, row, item_type){
    // Copy only necessary fields
                new_row.item_code = row.item_code;
                new_row.item_name = row.item_name;
                new_row.uom = row.uom;
                new_row.qty = row.qty;
                new_row.rate = row.rate;
                new_row.amount = row.amount;
                new_row.description = row.description;
                new_row.stock_uom = row.stock_uom;
                new_row.custom_fg_link = row.custom_fg_link;
                new_row.custom_article_no = row.custom_article_no;
                new_row.custom_size = row.custom_size;
                new_row.custom_consremarks = row.custom_consremarks;
                new_row.custom_artwork_reference = row.custom_artwork_reference;
                new_row.custom_wastage_percentage = row.custom_wastage_percentage;
                new_row.custom_gross_qty = row.custom_gross_qty;
                new_row.custom_gms = row.custom_gms;
                new_row.custom_item_type = item_type;
    
 }



 function modifyTheBOMItemTableFields(frm)
 {
     // Make qty read-only in all virtual child tables
    const tables = [
      'items',
      'custom_fabrics_items',
      'custom_trims_items',
      'custom_accessories_items',
      'custom_labels_items',
      'custom_packing_materials_items'
    ];

    tables.forEach(tablefield => {
      const grid = frm.fields_dict[tablefield]?.grid;
      if (!grid) return;

      frappe.meta.get_docfield('BOM Item', 'qty', frm.doc.name).read_only = 1;
      frappe.meta.get_docfield('BOM Item', 'item_name', frm.doc.name).read_only = 1;
      frappe.meta.get_docfield('BOM Item', 'qty', frm.doc.name).label = 'Cons Qty';

      //grid.fields_map['qty'].read_only = 1;
    });
 }

// /////////////
//////////////////
////////////////
///////////////
 // BOM item

 frappe.ui.form.on('BOM Item', {
  custom_net_qty(frm, cdt, cdn) {
    calculate_qty(cdt, cdn);
  },
  custom_wastage_percentage(frm, cdt, cdn) {
    calculate_qty(cdt, cdn);
  }
});

function calculate_qty(cdt, cdn) {
  const row = locals[cdt][cdn];

  const net = flt(row.custom_net_qty || 0);
  const waste = flt(row.custom_wastage_percentage || 0);
  const qty = net + (net * waste / 100);

  frappe.model.set_value(cdt, cdn, 'qty', qty);
}



function set_item_code_filters(frm) {

    // Need to change the filter from all the child groups of thes
  const table_field_map = {
    'custom_fabrics_items': ['Fabrics'],
    'custom_trims_items': ['Trims'],
    'custom_accessories_items': ['Accessories'],
    'custom_labels_items': ['Labels'],
    'custom_packing_materials_items': ['Packing Materials']
  };

  Object.entries(table_field_map).forEach(([table_fieldname, item_groups]) => {
    const grid = frm.fields_dict[table_fieldname]?.grid;
    if (!grid) return;

    grid.get_field('item_code').get_query = function(doc, cdt, cdn) {
      return {
        
        filters: [
          //["item_group", "in", [item_groups]],
          //["is_stock_item", "=", 1],
          //["disabled", "=", 0]
        ]
      };
    };
  });
}