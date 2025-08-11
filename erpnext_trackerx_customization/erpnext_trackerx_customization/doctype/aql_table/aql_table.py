import frappe
from frappe.model.document import Document

class AQLTable(Document):
	def validate(self):
		self.validate_rejection_acceptance()
		self.validate_sample_size()
	
	def validate_rejection_acceptance(self):
		"""Ensure rejection number is always greater than acceptance number"""
		if self.rejection_number <= self.acceptance_number:
			frappe.throw("Rejection number must be greater than acceptance number")
	
	def validate_sample_size(self):
		"""Validate sample size matches standard code letters"""
		standard_sizes = {
			'A': 2, 'B': 3, 'C': 5, 'D': 8, 'E': 13, 'F': 20, 
			'G': 32, 'H': 50, 'J': 80, 'K': 125, 'L': 200, 
			'M': 315, 'N': 500, 'P': 800, 'Q': 1250, 'R': 2000
		}
		
		expected_size = standard_sizes.get(self.sample_code_letter)
		if expected_size and self.sample_size != expected_size:
			frappe.throw(f"Sample size for code letter {self.sample_code_letter} should be {expected_size}")
	
	@staticmethod
	def get_aql_criteria(sample_code_letter, aql_value, inspection_regime="Normal"):
		"""Get acceptance and rejection numbers for given parameters"""
		criteria = frappe.get_value("AQL Table", 
			{
				"sample_code_letter": sample_code_letter,
				"aql_value": aql_value,
				"inspection_regime": inspection_regime,
				"is_active": 1
			},
			["acceptance_number", "rejection_number", "sample_size"]
		)
		
		if criteria:
			return {
				"acceptance_number": criteria[0],
				"rejection_number": criteria[1],
				"sample_size": criteria[2]
			}
		return None