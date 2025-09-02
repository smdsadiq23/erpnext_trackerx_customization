# Copyright (c) 2025, CognitionX and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PhysicalCell(Document):
	def validate(self):
		self.validate_for_operations_from_supported_operation_group()
		self.validate_for_physical_cell_timings()
		self.validate_for_cell_break_timings()



	def validate_for_operations_from_supported_operation_group(self):
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

	
	def  validate_for_physical_cell_timings(self):
		if not self.start_time or not self.end_time:
			frappe.throw(
				f"Cell timing is mandatory, Please provide valid start and end time"
			)
		
		if self.start_time >= self.end_time:
			frappe.throw(
				f"Cell Start time should be before end time"
			)

	def validate_for_cell_break_timings(self):

		if self.cell_breaks:
			for cell_break in self.cell_breaks:
				if cell_break.break_start >= cell_break.break_end:
					frappe.throw(
						f"Invalid Break Time, Start time should be before the end time at row: {cell_break.idx}"
					)

				if cell_break.break_start < self.start_time:
					frappe.throw(
						f"Invalid break time at row: {cell_break.idx}, Break time should be within the cell timings, Cannot start before cell timing"
					)
				
				if cell_break.break_end > self.end_time:
					frappe.throw(
						f"Invalid break time at row: {cell_break.idx}, Break time should be within the cell timings, Cannot end after cell timing"
					)
				



