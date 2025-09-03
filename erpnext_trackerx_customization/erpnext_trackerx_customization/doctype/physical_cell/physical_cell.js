// Client Script for Physical Cell DocType
frappe.ui.form.on('Physical Cell', {
    operation_group: function(frm) {
        
    }
});

frappe.ui.form.on('Operation Workstations', {
    before_operation_workstations_remove: function(frm) {
        console.log(" row added");
        // Refresh filter when row is removed
        setTimeout(() => {
            set_operation_filter(frm);
        }, 100);
    },
    
    operation_workstations_add: function(frm, cdt, cdn) {
        console.log("new row added");
        // Set filter for newly added row
        set_operation_filter(frm, cdt, cdn);
    }
});

function set_operation_filter(frm, cdt, cdn) {
    let operation_group = frm.doc.operation_group;
    
    if (operation_group) {
        let filters = {
            'custom_operation_group': operation_group
        };
        
        if (cdt && cdn) {
            // Set filter for specific row
            frm.set_query('operation', cdt, function() {
                return {
                    filters: filters
                };
            });
        } else {
            // Set filter for all rows in the child table
            frm.set_query('operation', 'operation_workstations', function() {
                return {
                    filters: filters
                };
            });
        }
    } else {
        // If no operation group selected, show all operations
        frm.set_query('operation', 'operation_workstations', function() {
            return {};
        });
    }
}