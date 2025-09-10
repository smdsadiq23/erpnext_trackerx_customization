# Copyright (c) 2025, Administrator and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class BundleInspectionDefectItem(Document):
    def validate(self):
        # Ensure defect count is at least 1
        if self.defect_count < 1:
            self.defect_count = 1