# Copyright (c) 2025, CognitionX and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_time

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
		if frappe.flags.in_migrate or frappe.flags.in_install or frappe.flags.in_fixtures:
			return
		
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
		# Skip during install/migrate/fixture import to avoid race condition
		if frappe.flags.in_install or frappe.flags.in_migrate or frappe.flags.in_fixtures:
			return

		if not self.supported_operation_group:
			return
		
		for row in self.operation_workstations:
			if row.operation:
				operation_group = frappe.db.get_value('Operation', row.operation, 'custom_operation_group')
				if operation_group != self.supported_operation_group:
					frappe.throw(
						_("Operation '{0}' in row {1} does not belong to the selected Operation Group '{2}'").format(
							row.operation, row.idx, self.supported_operation_group
						)
					)
	
	def validate_for_physical_cell_timings(self):
		"""Ensure cell start/end times are present and logically ordered.

		We normalise using get_time because DB can store Time as timedelta/time/str.
		"""
		start = get_time(self.start_time) if self.start_time else None
		end = get_time(self.end_time) if self.end_time else None

		if not start or not end:
			frappe.throw(
				"Cell timing is mandatory, Please provide valid start and end time"
			)

		# Non-overnight shift: start must be strictly before end
		if start >= end:
			frappe.throw("Cell Start time should be before end time")

	def validate_for_cell_break_timings(self):
		if not self.cell_breaks:
			return

		# Normalise cell timings once
		cell_start = get_time(self.start_time) if self.start_time else None
		cell_end = get_time(self.end_time) if self.end_time else None

		for cell_break in self.cell_breaks:
			b_start = (
				get_time(cell_break.break_start) if cell_break.break_start else None
			)
			b_end = get_time(cell_break.break_end) if cell_break.break_end else None

			if not b_start or not b_end:
				frappe.throw(
					f"Invalid Break Time, both start and end time are required at row: {cell_break.idx}"
				)

			if b_start >= b_end:
				frappe.throw(
					f"Invalid Break Time, Start time should be before the end time at row: {cell_break.idx}"
				)

			if cell_start and b_start < cell_start:
				frappe.throw(
					f"Invalid break time at row: {cell_break.idx}, "
					f"Break time should be within the cell timings, "
					f"Cannot start before cell timing"
				)

			if cell_end and b_end > cell_end:
				frappe.throw(
					f"Invalid break time at row: {cell_break.idx}, "
					f"Break time should be within the cell timings, "
					f"Cannot end after cell timing"
				)