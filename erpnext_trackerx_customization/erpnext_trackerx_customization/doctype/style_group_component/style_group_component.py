# Copyright (c) 2025, CognitionX and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class StyleGroupComponent(Document):
	"""Style Group Component child doctype for managing components within a style group"""

	def validate(self):
		"""Validate the component data"""
		self.validate_component_name()

	def validate_component_name(self):
		"""Ensure component name is not empty and properly formatted"""
		if not self.component_name:
			frappe.throw("Component Name is required")

		# Remove extra spaces and format properly
		self.component_name = self.component_name.strip()

		if len(self.component_name) < 2:
			frappe.throw("Component Name must be at least 2 characters long")