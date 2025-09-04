# Copyright (c) 2025, CognitionX and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class DigitalDevice(Document):
	def validate(self):

		if self.imei:
			self.identifier = self.imei
			self.identifier_type = 'IMEI'
		elif self.mac:
			self.identifier = self.mac
			self.identifier_type = 'Mac'
		elif self.ipv4:
			self.identifier = self.ipv4
			self.identifier_type = 'IPv4'
		else:
			self.identifier = self.id
			self.identifier_type = 'ID'
		


	def before_save(self):
		pass
