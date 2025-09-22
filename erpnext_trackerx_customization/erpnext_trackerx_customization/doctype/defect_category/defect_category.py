# Copyright (c) 2025, TrackerX and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class DefectCategory(Document):
	def validate(self):
		"""Validate defect category before saving"""
		self.validate_unique_name_per_material_type()

	def validate_unique_name_per_material_type(self):
		"""Ensure category name is unique within each material type"""
		existing = frappe.db.get_value(
			'Defect Category',
			{
				'category_name': self.category_name,
				'material_type': self.material_type,
				'name': ['!=', self.name]
			},
			'name'
		)

		if existing:
			frappe.throw(
				f"Defect Category '{self.category_name}' already exists for Material Type '{self.material_type}'"
			)