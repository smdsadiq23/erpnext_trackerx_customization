import frappe
from frappe.model.document import Document

class AQLLevel(Document):
	def validate(self):
		self.validate_level_code()
	
	def validate_level_code(self):
		"""Validate that level code follows standard AQL format"""
		valid_general = ['1', '2', '3']
		valid_special = ['S1', 'S2', 'S3', 'S4']
		
		if self.level_type == 'General' and self.level_code not in valid_general:
			frappe.throw(f"For General inspection, level code must be one of: {', '.join(valid_general)}")
		elif self.level_type == 'Special' and self.level_code not in valid_special:
			frappe.throw(f"For Special inspection, level code must be one of: {', '.join(valid_special)}")