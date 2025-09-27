# Copyright (c) 2025, CognitionX and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime

class OperatorAttendance(Document):


	def format_date_time_to_date_hour(self):
		format_string = "%Y-%m-%d %H"
		hour_in_datetime = datetime.strptime(str(self.hour),"%Y-%m-%d %H:%M:%S" )
		hour_in_str = hour_in_datetime.strftime(format_string)
		self.hour = datetime.strptime(hour_in_str, format_string)
		

	def validate(self):
		if frappe.utils.now_datetime() > self.hour:
			frappe.throw(
				f"You cannot update operator attendance for {self.hour}, It's already passed time, contact administrator", frappe.ValidationError
			)
		self.format_date_time_to_date_hour()
		
		

	def before_insert(self):
		self.format_date_time_to_date_hour()
		
		prev_records = frappe.get_all("Operator Attendance", filters={"physical_cell": self.physical_cell, "hour": self.hour}, fields=["name"])
		if prev_records:
			frappe.throw(
				f"Operator attendance already added for the physical cell {self.physical_cell} for {self.hour}"
			)
		self.name = f"{self.physical_cell}-{self.hour}"
