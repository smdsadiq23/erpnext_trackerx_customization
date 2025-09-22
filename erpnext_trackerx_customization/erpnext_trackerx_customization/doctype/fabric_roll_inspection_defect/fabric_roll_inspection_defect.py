# Copyright (c) 2025, TrackerX and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class FabricRollInspectionDefect(Document):
	def validate(self):
		"""Validate and calculate points automatically"""
		self.calculate_points()

	def calculate_points(self):
		"""Calculate points based on defect and size"""
		if self.defect and self.size:
			try:
				# Get defect type from Defect Master
				defect_doc = frappe.get_doc("Defect Master", self.defect)

				# Calculate points based on defect type and size
				size = float(self.size)

				if defect_doc.defect_type == "Critical":
					# Critical defects typically get 4 points regardless of size
					points = 4.0
				elif defect_doc.defect_type == "Major":
					# Major defects: 2-3 points based on size
					if size <= 1:
						points = 2.0
					else:
						points = 3.0
				elif defect_doc.defect_type == "Minor":
					# Minor defects: 1-2 points based on size
					if size <= 3:
						points = 1.0
					else:
						points = 2.0
				else:
					# Default to 1 point if defect type is not specified
					points = 1.0

				self.points_auto = points

			except Exception as e:
				frappe.log_error(f"Error calculating defect points: {str(e)}")
				self.points_auto = 1.0  # Default to 1 point on error
		else:
			self.points_auto = 0.0