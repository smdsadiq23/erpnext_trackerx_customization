// Enhanced Sales Order List View Client Script
frappe.listview_settings['Pick List'] = {
    onload: function(listview) {
        
        listview.page.add_inner_button(__("Trims Order"), function() {
            frappe.set_route("List", "Trims Order");
        }, "Go To");

        listview.page.add_inner_button(__("Cut Docket"), function() {
            frappe.set_route("List", "Cut Docket");
        }, "Go To");

    },
};