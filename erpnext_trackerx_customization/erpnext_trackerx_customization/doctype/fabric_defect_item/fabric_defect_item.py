# -*- coding: utf-8 -*-
"""
Fabric Defect Item - Child Table

Individual defect details with automatic point calculation.
"""

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext_trackerx_customization.utils.fabric_inspection import FabricInspectionCalculator

class FabricDefectItem(Document):
    def validate(self):
        """Validate and calculate defect points"""
        if self.defect_code and self.defect_size:
            # Calculate defect points automatically
            self.defect_points = FabricInspectionCalculator.calculate_defect_points(
                self.defect_code, self.defect_size
            )
            
            # Set severity based on points
            if self.defect_points >= 4:
                self.severity = "Critical"
            elif self.defect_points >= 3:
                self.severity = "Major"
            else:
                self.severity = "Minor"