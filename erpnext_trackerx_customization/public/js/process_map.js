frappe.listview_settings['Process Map'] = {
    onload: function(listview) {
        // Add button to list view
        listview.page.add_inner_button(__('Create Process Map'), function() {
            const baseUrl = window.location.origin + "/app/process-map-builder/";
            // Open process map builder page in a new tab
            window.open(baseUrl, '_blank');
        });
    }
};