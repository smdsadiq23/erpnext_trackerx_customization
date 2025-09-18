# Copyright (c) 2025, CognitionX and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
DEFAULT_NAME = 'QR/Barcode Cut Bundle Activation'

class OperationGroup(Document):

	def on_trash(self):
		if self.name == DEFAULT_NAME:
			frappe.throw(
				f"You cannot delete system opeation group {DEFAULT_NAME}"
			)

	def before_save(self):
		if self.name == DEFAULT_NAME:
			frappe.throw(
				f"You cannot update system operation group {DEFAULT_NAME}"
			)

	def before_rename(self, old_name, new_name, merge=False):
		if self.name == DEFAULT_NAME:
			frappe.throw(
				f"You cannot rename system operation group {DEFAULT_NAME}"
			)

