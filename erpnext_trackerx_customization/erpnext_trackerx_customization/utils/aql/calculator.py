import frappe
from frappe.model.document import Document
from .constants import LOT_SIZE_RANGES, SAMPLE_SIZE_MAPPING, DEFAULT_INSPECTION_LEVEL


class AQLCalculator:
	"""Utility class for AQL calculations based on industry standards"""
	
	@staticmethod
	def get_sample_size_code_and_range(quantity, inspection_level=DEFAULT_INSPECTION_LEVEL):
		"""
		Get sample size code letter and lot size range based on lot quantity and inspection level
		According to ISO 2859-1 (MIL-STD-105E) standard
		
		Args:
			quantity (int): Lot quantity
			inspection_level (str): Inspection level (1, 2, 3, S1, S2, S3, S4)
			
		Returns:
			tuple: (sample_code_letter, lot_size_range)
		"""
		level_ranges = LOT_SIZE_RANGES.get(inspection_level, LOT_SIZE_RANGES.get(DEFAULT_INSPECTION_LEVEL, {}))
		
		for (min_qty, max_qty), code in level_ranges.items():
			if min_qty <= quantity <= max_qty:
				# Format the range string
				if max_qty >= 999999999:  # Open-ended range
					lot_range = f"{min_qty}-"
				else:
					lot_range = f"{min_qty}-{max_qty}"
				return code, lot_range
		
		return "A", "2-8"  # Fallback for edge cases

	@staticmethod 
	def get_sample_size_code(quantity, inspection_level=DEFAULT_INSPECTION_LEVEL):
		"""
		Get sample size code letter based on lot quantity and inspection level
		(Legacy method for backward compatibility)
		
		Args:
			quantity (int): Lot quantity
			inspection_level (str): Inspection level (1, 2, 3, S1, S2, S3, S4)
			
		Returns:
			str: Sample size code letter (A-R)
		"""
		code, _ = AQLCalculator.get_sample_size_code_and_range(quantity, inspection_level)
		return code
	
	@staticmethod
	def get_sample_size(code_letter):
		"""
		Get actual sample size from code letter
		
		Args:
			code_letter (str): Sample size code letter (A-R)
			
		Returns:
			int: Sample size
		"""
		return SAMPLE_SIZE_MAPPING.get(code_letter, 2)
	
	@staticmethod
	def calculate_aql_criteria(item_code, quantity):
		"""
		Calculate AQL criteria for an item based on its configuration
		
		Args:
			item_code (str): Item code
			quantity (int): Received quantity
			
		Returns:
			dict: AQL criteria with sample_size, acceptance_number, rejection_number, etc.
			
		Raises:
			frappe.ValidationError: If item AQL configuration is incomplete
		"""
		# Get item AQL configuration
		item = frappe.get_doc("Item", item_code)
		
		if not item.get("custom_aql_inspection_level") or not item.get("custom_accepted_quality_level"):
			frappe.throw(f"Item {item_code} does not have complete AQL configuration")
		
		# Get inspection level details
		aql_level = frappe.get_doc("AQL Level", item.custom_aql_inspection_level)
		inspection_regime = item.get("custom_inspection_regime", "Normal")
		aql_value = item.custom_accepted_quality_level
		
		# Get sample size code and lot range based on quantity and inspection level
		sample_code, lot_size_range = AQLCalculator.get_sample_size_code_and_range(quantity, aql_level.level_code)
		sample_size = AQLCalculator.get_sample_size(sample_code)
		
		# Get AQL criteria from table using the new structure
		aql_criteria = frappe.db.get_value(
			"AQL Table",
			{
				"inspection_level": aql_level.level_code,
				"inspection_regime": inspection_regime,
				"lot_size_range": lot_size_range,
				"sample_code_letter": sample_code,
				"aql_value": aql_value,
				"is_active": 1
			},
			["acceptance_number", "rejection_number"]
		)
		
		if not aql_criteria:
			# If exact criteria not found, try with Normal regime
			aql_criteria = frappe.db.get_value(
				"AQL Table",
				{
					"inspection_level": aql_level.level_code,
					"inspection_regime": "Normal",
					"lot_size_range": lot_size_range,
					"sample_code_letter": sample_code,
					"aql_value": aql_value,
					"is_active": 1
				},
				["acceptance_number", "rejection_number"]
			)
			
			if not aql_criteria:
				frappe.throw(f"No AQL table entry found for Level: {aql_level.level_code}, Range: {lot_size_range}, Sample Code: {sample_code}, AQL: {aql_value}")
		
		return {
			"sample_code_letter": sample_code,
			"sample_size": sample_size,
			"lot_size_range": lot_size_range,
			"acceptance_number": aql_criteria[0],
			"rejection_number": aql_criteria[1],
			"inspection_level": aql_level.level_code,
			"aql_value": aql_value,
			"inspection_regime": inspection_regime
		}
	
	@staticmethod
	def determine_inspection_result(defects_found, acceptance_number, rejection_number):
		"""
		Determine inspection result based on defects found and AQL criteria
		
		Args:
			defects_found (int): Number of defects found in sample
			acceptance_number (int): Maximum acceptable defects
			rejection_number (int): Minimum defects for rejection
			
		Returns:
			str: Inspection result ("Accepted", "Rejected", or "Re-inspect")
		"""
		if defects_found <= acceptance_number:
			return "Accepted"
		elif defects_found >= rejection_number:
			return "Rejected"
		else:
			return "Re-inspect"  # Edge case handling


@frappe.whitelist()
def calculate_aql_criteria(item_code, quantity):
	"""
	Whitelisted API method for AQL criteria calculation
	
	Args:
		item_code (str): Item code
		quantity (int): Received quantity
		
	Returns:
		dict: AQL criteria with sample_size, acceptance_number, rejection_number, etc.
	"""
	try:
		quantity = int(quantity)
		return AQLCalculator.calculate_aql_criteria(item_code, quantity)
	except Exception as e:
		frappe.log_error(f"AQL calculation error for {item_code}: {str(e)}")
		frappe.throw(f"AQL calculation failed: {str(e)}")