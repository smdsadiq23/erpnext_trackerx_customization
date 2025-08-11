# Copyright (c) 2025, CognitionX and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from erpnext_trackerx_customization.erpnext_trackerx_customization.utils.aql import AQLCalculator


class MaterialInspectionItem(Document):
	def validate(self):
		if self.item_code and self.received_quantity:
			self.calculate_aql_values()
			self.determine_inspection_result()
	
	def calculate_aql_values(self):
		"""Calculate AQL sample size and acceptance/rejection numbers"""
		try:
			aql_data = AQLCalculator.calculate_aql_criteria(
				self.item_code, 
				self.received_quantity or 0
			)
			
			self.sample_size = aql_data.get("sample_size", 0)
			self.acceptance_number = aql_data.get("acceptance_number", 0)
			self.rejection_number = aql_data.get("rejection_number", 1)
			
		except Exception as e:
			# If AQL calculation fails, set default values
			frappe.log_error(f"AQL calculation failed for item {self.item_code}: {str(e)}")
			self.sample_size = 0
			self.acceptance_number = 0
			self.rejection_number = 1
	
	def determine_inspection_result(self):
		"""Determine inspection result based on defects found"""
		if self.defects_found is not None and self.acceptance_number is not None and self.rejection_number is not None:
			self.inspection_result = AQLCalculator.determine_inspection_result(
				self.defects_found or 0,
				self.acceptance_number or 0, 
				self.rejection_number or 1
			)
			
			# Auto-populate accepted/rejected quantities based on inspection result
			if self.inspection_result == "Accepted":
				self.accepted_qty = self.received_quantity or 0
				self.rejected_qty = 0
			elif self.inspection_result == "Rejected":
				self.accepted_qty = 0
				self.rejected_qty = self.received_quantity or 0
			else:  # Re-inspect
				# Keep quantities as entered manually
				pass
