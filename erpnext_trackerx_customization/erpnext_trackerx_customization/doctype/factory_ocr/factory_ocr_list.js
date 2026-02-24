frappe.listview_settings['Factory OCR'] = {
    add_fields: ["status", "docstatus"],
    has_indicator_for_draft: true,

    get_indicator: function(doc) {

        const status = (doc.status || "").trim();

        if (status === "Approved") {
            return ["Approved", "green"];
        }

        if (status === "Rejected") {
            return ["Rejected", "red"];
        }

        if (status === "Pending for Approval") {
            return ["Pending for Approval", "orange"];
        }

        // fallback
        return ["Draft", "gray"];
    }
};
