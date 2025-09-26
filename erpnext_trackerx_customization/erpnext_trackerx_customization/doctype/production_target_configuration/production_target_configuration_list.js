frappe.listview_settings['Production Target Configuration'] = {
    add_fields: [""],
    
    onload: function(listview) {
        // Add button to switch to grid view
        listview.page.add_menu_item(__("Goto Target Config Manager"), function() {
            frappe.set_route('production-target-ma');
        });
        setTimeout(() => {
            frappe.set_route('production-target-ma');
        }, 300);
        frappe.set_route('production-target-ma');
    }
   
};