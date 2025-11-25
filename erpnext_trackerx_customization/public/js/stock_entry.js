// frappe.ui.form.on("Stock Entry", {
//     setup: function(frm) {
//         // Override s_warehouse (source) in items child table
//         frm.set_query("s_warehouse", "items", function(doc, cdt, cdn) {
//             let row = locals[cdt][cdn];
//             return {
//                 filters: {
//                     company: doc.company,
//                     // Remove "is_group = 0" to allow group warehouses
//                     // Or customize as needed (e.g., allow both group & leaf)
//                 }
//             };
//         });

//         // Override t_warehouse (target) in items child table
//         frm.set_query("t_warehouse", "items", function(doc, cdt, cdn) {
//             let row = locals[cdt][cdn];
//             return {
//                 filters: {
//                     company: doc.company,
//                     // Again, omit is_group or set conditionally
//                 }
//             };
//         });
//     }
// });