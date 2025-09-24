// Copyright (c) 2025, CognitionX and contributors
// For license information, please see license.txt

frappe.ui.form.on('Operator Attendance', {
    refresh: function(frm) {
        // Add custom button to open grid view
        frm.add_custom_button(__('Open Grid View'), function() {
            window.open('/app/operator_attendance', '_blank');
        });
    }
});