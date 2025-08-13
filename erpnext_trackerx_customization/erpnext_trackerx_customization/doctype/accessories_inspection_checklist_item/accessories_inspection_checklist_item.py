# -*- coding: utf-8 -*-
"""
Accessories Inspection Checklist Item - Child Table

Individual checklist item for accessories inspection parameters.
"""

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class AccessoriesInspectionChecklistItem(Document):
    def validate(self):
        """Validate checklist item"""
        # Auto-set defect found based on result
        if self.result == "Fail":
            self.defect_found = 1
            if not self.defect_severity:
                self.defect_severity = "Major"
        elif self.result == "Pass":
            self.defect_found = 0
            self.defect_severity = None