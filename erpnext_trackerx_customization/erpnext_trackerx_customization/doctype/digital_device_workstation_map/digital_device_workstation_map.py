# Copyright (c) 2025, CognitionX and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DigitalDeviceWorkstationMap(Document):
	def validate(self):
		
		existing_map_for_device = frappe.db.get_value("Digital Device Workstation Map", {"digital_device": self.digital_device, "link_status": "Linked"}, ["workstation"])
		if existing_map_for_device and self.is_new() and existing_map_for_device==self.workstation:
			frappe.throw(
				f"This combination already configured, Modify the same record"
			)
		if False and existing_map_for_device and self.is_new():
			frappe.throw(
				f"This device is aleady configrued to use workstation {existing_map_for_device}, Please remove or unlink it first"
			)