frappe.listview_settings['Operator Attendance'] = {
    add_fields: ["physical_cell", "hour", "value"],
    get_indicator: function(doc) {
        return [__(doc.value), doc.value > 0 ? "green" : "red", "value,=," + doc.value];
    },
    onload: function(listview) {
        // Add button to switch to grid view
        listview.page.add_menu_item(__("Grid View"), function() {
            frappe.set_route('Form', 'Operator Attendance Grid');
        });
    }
};