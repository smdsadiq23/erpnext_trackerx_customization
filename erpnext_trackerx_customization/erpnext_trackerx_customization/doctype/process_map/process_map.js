frappe.ui.form.on("Process Map", {
    edit_map_button: function(frm) {
        const mapName = frm.doc.map_name;
        const mapNumber = frm.doc.process_map_number;

        if (!mapName || !mapNumber) {
            frappe.msgprint("❌ map_name or process_map_number is missing!");
            return;
        }

        // Construct dynamic URL
        const baseUrl = window.location.origin + "/app/process-map-builder/";
        const url = `${baseUrl}${encodeURIComponent(mapName)}-${encodeURIComponent(mapNumber)}`;

        // Redirect to the builder page
        window.open(url, "_blank"); // open in new tab
        // OR: window.location.href = url; // open in same tab
    }
});
