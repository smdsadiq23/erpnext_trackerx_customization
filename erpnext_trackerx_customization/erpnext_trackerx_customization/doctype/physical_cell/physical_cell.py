# Copyright (c) 2025, CognitionX and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PhysicalCell(Document):
	def validate(self):
		"""Validate that selected operations belong to the correct operation group"""
		if not self.supported_operation_group:
			return
		
		for row in self.operation_workstations:
			if row.operation:
				# Get the operation's group
				operation_group = frappe.db.get_value('Operation', row.operation, 'custom_operation_group')
				
				if operation_group != self.supported_operation_group:
					frappe.throw(
						f"Operation '{row.operation}' in row {row.idx} does not belong to the selected Operation Group '{self.supported_operation_group}'"
					)



