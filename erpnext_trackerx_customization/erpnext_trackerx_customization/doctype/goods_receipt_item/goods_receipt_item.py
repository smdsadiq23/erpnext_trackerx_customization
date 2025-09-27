# Copyright (c) 2025, CognitionX and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class GoodsReceiptItem(Document):
	def validate(self):
		self.validate_roll_no_and_boxes()

	def validate_roll_no_and_boxes(self):
		"""Validate roll_no and no_of_boxespacks interaction"""
		if self.roll_no and self.no_of_boxespacks:
			if self.no_of_boxespacks > 1:
				self.roll_no = ""
				frappe.msgprint(
					"Roll/Box No cleared because No Of Boxes/Rolls is greater than 1",
					alert=True,
					indicator="orange"
				)
		elif self.roll_no and not self.no_of_boxespacks:
			self.no_of_boxespacks = 1
