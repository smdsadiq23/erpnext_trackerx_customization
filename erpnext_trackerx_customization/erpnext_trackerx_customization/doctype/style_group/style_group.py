# Copyright (c) 2025, CognitionX and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import get_link_to_form

class StyleGroup(Document):
	"""Style Group doctype for managing style groups with components"""

	def validate(self):
		"""Validate the style group data"""
		self.validate_style_group_name()
		self.validate_components()
		self.set_default_company()

	def validate_style_group_name(self):
		"""Ensure style group name is not empty and properly formatted"""
		if not self.name:
			frappe.throw("Style Group Name is required")

		# Remove extra spaces and format properly
		self.name = self.name.strip()

		if len(self.name) < 2:
			frappe.throw("Style Group Name must be at least 2 characters long")

	def validate_components(self):
		"""Validate components table"""
		if self.components:
			component_names = []
			main_components = []

			for component in self.components:
				# Check for duplicate component names
				if component.component_name in component_names:
					frappe.throw(f"Duplicate component name '{component.component_name}' found")
				component_names.append(component.component_name)

				# Check for multiple main components
				if component.is_main:
					main_components.append(component.component_name)

			# Ensure only one component is marked as main
			if len(main_components) > 1:
				frappe.throw(f"Only one component can be marked as 'is main'. Found multiple: {', '.join(main_components)}")

	def set_default_company(self):
		"""Set default company if not already set"""
		if not self.company:
			# Get user's default company
			default_company = frappe.defaults.get_user_default("Company")
			if not default_company:
				# Get system default company
				default_company = frappe.db.get_single_value("Global Defaults", "default_company")

			if default_company:
				self.company = default_company

	def before_save(self):
		"""Actions to perform before saving"""
		self.set_title_case()

	def set_title_case(self):
		"""Set proper title case for name and components"""
		if self.name:
			self.name = self.name.title()

		if self.components:
			for component in self.components:
				if component.component_name:
					component.component_name = component.component_name.title()

	def on_update(self):
		"""Actions to perform after update"""
		pass