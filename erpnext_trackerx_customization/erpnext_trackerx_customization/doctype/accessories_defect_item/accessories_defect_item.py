# -*- coding: utf-8 -*-
"""
Accessories Defect Item - Child Table

Individual defect details for accessories inspection.
"""

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class AccessoriesDefectItem(Document):
    def validate(self):
        """Validate and auto-populate defect details"""
        if self.defect_code:
            # Get defect details from defect master
            defect_master = frappe.get_doc("Defect Master", self.defect_code)
            self.defect_description = defect_master.defect_description
            self.defect_category = defect_master.defect_category
            
            # Set default severity based on defect master
            if not self.defect_severity:
                self.defect_severity = defect_master.severity or "Major"