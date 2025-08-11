import frappe
from frappe.model.document import Document

class AQLStandard(Document):
	def validate(self):
		self.validate_aql_value()
	
	def validate_aql_value(self):
		"""Validate that AQL value follows industry standards"""
		standard_values = [
			'0.065', '0.10', '0.15', '0.25', '0.40', '0.65', '1.0', '1.5', 
			'2.5', '4.0', '6.5', '10', '15', '25', '40', '65', '100', '150'
		]
		
		if self.aql_value not in standard_values:
			frappe.throw(f"AQL value must be one of the standard values: {', '.join(standard_values)}")