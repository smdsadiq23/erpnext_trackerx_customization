# Copyright (c) 2025, TrackerX and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class FabricRollInspectionDefect(Document):
	def validate(self):
		"""Validate and calculate points automatically"""
		self.calculate_points()

	def calculate_points(self):
		"""Calculate points based on defect size only"""
		if self.size:
			try:
				# Calculate points based on size ranges only
				size = float(self.size)

				# Simple size-based point calculation
				if size <= 3:
					points = 1.0          # Up to 3 inches = 1 Point
				elif size <= 6:
					points = 2.0          # Over 3 to 6 inches = 2 Points
				elif size <= 9:
					points = 3.0          # Over 6 to 9 inches = 3 Points
				else:
					points = 4.0          # Over 9 inches = 4 Points

				self.points_auto = points

			except Exception as e:
				frappe.log_error(f"Error calculating defect points for {self.defect}: {str(e)}")
				# Use existing points_auto if available, otherwise default to 1.0
				if not self.points_auto:
					self.points_auto = 1.0
		else:
			self.points_auto = 0.0