# -*- coding: utf-8 -*-
"""
Fabric Roll Inspection Item - Child Table

Individual fabric roll inspection details with defect tracking.
"""

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class FabricRollInspectionItem(Document):
	def validate(self):
		"""Validate and calculate fields automatically"""
		self.calculate_total_size()
		self.calculate_total_points()
		self.calculate_points_per_100_sqm()

	def calculate_total_size(self):
		"""Calculate total size by summing all defect sizes"""
		total_size = 0.0

		# Force reload defects from database to handle mobile API timing issues
		if self.name:
			defects = frappe.get_all(
				"Fabric Roll Inspection Defect",
				filters={"parent": self.name},
				fields=["size"]
			)
			for defect in defects:
				if defect.size:
					total_size += float(defect.size)
		else:
			# Fallback to child table for new documents
			if hasattr(self, 'defects') and self.defects:
				for defect_row in self.defects:
					if defect_row.size:
						total_size += float(defect_row.size)

		self.total_size_inches = total_size

	def calculate_total_points(self):
		"""Calculate total points from defects table"""
		total_points = 0.0

		# Force reload defects from database to handle mobile API timing issues
		if self.name:
			defects = frappe.get_all(
				"Fabric Roll Inspection Defect",
				filters={"parent": self.name},
				fields=["points_auto"]
			)
			for defect in defects:
				if defect.points_auto:
					total_points += float(defect.points_auto)
		else:
			# Fallback to child table for new documents
			if hasattr(self, 'defects') and self.defects:
				for defect_row in self.defects:
					if defect_row.points_auto:
						total_points += float(defect_row.points_auto)

		self.total_points_auto = total_points
		self.total_defect_points = total_points

	def calculate_points_per_100_sqm(self):
		"""Calculate points per 100 square meters"""
		if self.actual_length_m and self.actual_width_m and self.total_points_auto:
			# Calculate area in square meters
			area_sqm = float(self.actual_length_m) * float(self.actual_width_m)
			if area_sqm > 0:
				# Calculate points per 100 sqm
				self.points_per_100_sqm = (float(self.total_points_auto) / area_sqm) * 100
			else:
				self.points_per_100_sqm = 0.0
		else:
			self.points_per_100_sqm = 0.0

	def on_update(self):
		"""Trigger calculations when defects are updated"""
		self.calculate_total_size()
		self.calculate_total_points()
		self.calculate_points_per_100_sqm()