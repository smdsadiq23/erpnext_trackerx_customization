# Copyright (c) 2025, Administrator and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class BundleInspectionChecklistItem(Document):
    def before_save(self):
        # Auto-set checked by and date when status changes from Pending
        if self.status != "Pending" and not self.checked_by:
            self.checked_by = frappe.session.user
            self.checked_date = frappe.utils.now_datetime()