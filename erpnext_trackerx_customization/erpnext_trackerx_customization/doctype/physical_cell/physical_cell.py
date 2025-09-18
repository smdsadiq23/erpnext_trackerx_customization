# Copyright (c) 2025, CognitionX and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

DEFAULT_NAME = 'QR/Barcode Cut Bundle Activation'

class PhysicalCell(Document):

	

	def validate(self):
		self.validate_for_operations_from_supported_operation_group()
		self.validate_for_physical_cell_timings()
		self.validate_for_cell_break_timings()
		self.validate_for_workstation_added_to_diff_cell()

	def on_trash(self):
		if self.name == DEFAULT_NAME:
			frappe.throw(
				f"You cannot delete system cell {DEFAULT_NAME}"
			)

	def before_save(self):
		if self.name == DEFAULT_NAME:
			frappe.throw(
				f"You cannot update system cell {DEFAULT_NAME}"
			)

	def before_rename(self, old_name, new_name, merge=False):
		if self.name == DEFAULT_NAME:
			frappe.throw(
				f"You cannot rename system cell {DEFAULT_NAME}"
			)
			
	def validate_for_workstation_added_to_diff_cell(self):
		for row in self.operation_workstations:
			existing_cell_with_same_ws = frappe.db.sql("""
				SELECT DISTINCT parent
				FROM `tabPhysical Cell Operation` 
				WHERE workstation = %s
				AND parent != %s
				AND parenttype = 'Physical Cell'
			""", (row.workstation, self.name), as_dict=True)

			if existing_cell_with_same_ws:
				# Get the first parent name from the result
				conflicting_cell = existing_cell_with_same_ws[0]['parent']
				frappe.throw(
					f"Workstation {row.workstation} cannot be added to this cell, It's already configured in Cell {conflicting_cell}, Please remove it from there first."
				)

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
				



