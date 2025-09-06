# Copyright (c) 2025, Administrator and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class CuttingBundleInspection(Document):
    def on_load(self):
        """Auto-populate from Bundle Configuration when loading"""
        if self.bundle_configuration_reference:
            # Always populate data to ensure latest information
            self.populate_from_bundle_configuration()
            
    def after_insert(self):
        """Populate data immediately after creation"""
        if self.bundle_configuration_reference:
            self.populate_from_bundle_configuration()
            self.save()
            
    def before_save(self):
        """Calculate AQL parameters and defect counts before saving"""
        # Always recalculate lot size from Bundle Configuration Items
        self.calculate_lot_size()
        
        if self.lot_size and self.inspection_level and self.inspection_regime:
            self.calculate_aql_sample_size()
            self.calculate_sampling_distribution()
            self.calculate_aql_limits()
            
        self.count_defects()
        self.compute_inspection_result()
        self.generate_inspection_summary()
        
    def calculate_lot_size(self):
        """Calculate lot size from Bundle Configuration Items -> Cut Quantity"""
        if self.bundle_configuration_items:
            total_qty = sum([item.cut_quantity for item in self.bundle_configuration_items if item.cut_quantity])
            self.lot_size = int(total_qty) if total_qty else 0
        
    def populate_from_bundle_configuration(self):
        """Populate data from Bundle Configuration reference"""
        if not self.bundle_configuration_reference:
            frappe.log_error("No bundle_configuration_reference found")
            return
            
        try:
            bundle_config = frappe.get_doc("Bundle Creation", self.bundle_configuration_reference)
            frappe.log_error(f"Bundle Config loaded: {bundle_config.name}")
            
            # Copy Bundle Configuration Items
            self.bundle_configuration_items = []
            if hasattr(bundle_config, 'table_bundle_creation_item') and bundle_config.table_bundle_creation_item:
                frappe.log_error(f"Found {len(bundle_config.table_bundle_creation_item)} bundle creation items")
                for item in bundle_config.table_bundle_creation_item:
                    self.append("bundle_configuration_items", {
                        "work_order": item.work_order,
                        "sales_order": item.sales_order,
                        "line_item_no": item.line_item_no,
                        "size": item.size,
                        "cut_quantity": item.cut_quantity,
                        "shade": item.shade,
                        "shade_cut_quantity": item.shade_cut_quantity,
                        "unitsbundle": item.unitsbundle,
                        "no_of_bundles": item.no_of_bundles,
                        "ply": item.ply
                    })
            else:
                frappe.log_error("No table_bundle_creation_item found in bundle config")
                
            # Copy Bundle Details
            self.bundle_details = []
            if hasattr(bundle_config, 'table_bundle_details') and bundle_config.table_bundle_details:
                frappe.log_error(f"Found {len(bundle_config.table_bundle_details)} bundle details")
                for detail in bundle_config.table_bundle_details:
                    detail_dict = detail.as_dict()
                    # Remove system fields that might cause issues
                    for key in ['name', 'creation', 'modified', 'modified_by', 'owner', 'parent', 'parentfield', 'parenttype', 'idx']:
                        detail_dict.pop(key, None)
                    self.append("bundle_details", detail_dict)
            else:
                frappe.log_error("No table_bundle_details found in bundle config")
                
            # Copy Shade and Ply Details
            self.shade_and_ply_details = []
            if hasattr(bundle_config, 'table_shade_and_ply') and bundle_config.table_shade_and_ply:
                frappe.log_error(f"Found {len(bundle_config.table_shade_and_ply)} shade and ply details")
                for shade_ply in bundle_config.table_shade_and_ply:
                    shade_ply_dict = shade_ply.as_dict()
                    # Remove system fields that might cause issues
                    for key in ['name', 'creation', 'modified', 'modified_by', 'owner', 'parent', 'parentfield', 'parenttype', 'idx']:
                        shade_ply_dict.pop(key, None)
                    self.append("shade_and_ply_details", shade_ply_dict)
            else:
                frappe.log_error("No table_shade_and_ply found in bundle config")
                
        except Exception as e:
            frappe.log_error(f"Error in populate_from_bundle_configuration: {str(e)}")
            import traceback
            frappe.log_error(f"Full traceback: {traceback.format_exc()}")
            
        # Calculate lot size from Bundle Configuration Items -> Cut Quantity (always recalculate)
        total_qty = sum([item.cut_quantity for item in self.bundle_configuration_items if item.cut_quantity])
        self.lot_size = int(total_qty) if total_qty else 0
            
        # Create default inspection checklist
        if not self.inspection_checklist:
            self.create_default_checklist()
            
    def create_default_checklist(self):
        """Create default inspection checklist items"""
        default_items = [
            {"inspection_point": "Bundle marking is clear and correct", "category": "Bundle Marking", "is_mandatory": 1},
            {"inspection_point": "Fabric grain direction is consistent", "category": "Fabric Quality", "is_mandatory": 1},
            {"inspection_point": "Cut edges are clean and smooth", "category": "Cutting Quality", "is_mandatory": 1},
            {"inspection_point": "Pattern matching (if applicable)", "category": "Pattern Matching", "is_mandatory": 0},
            {"inspection_point": "Component count matches specification", "category": "Component Count", "is_mandatory": 1},
            {"inspection_point": "No fabric defects in cut pieces", "category": "Defect Check", "is_mandatory": 1},
            {"inspection_point": "Notches and drill holes are accurate", "category": "Accuracy Check", "is_mandatory": 1},
            {"inspection_point": "Bundle size is within tolerance", "category": "Size Tolerance", "is_mandatory": 1},
            {"inspection_point": "Trim card verification completed", "category": "Verification", "is_mandatory": 0},
            {"inspection_point": "Color chart approval confirmed", "category": "Approval", "is_mandatory": 0}
        ]
        
        for item in default_items:
            self.append("inspection_checklist", item)
            
    def calculate_aql_sample_size(self):
        """Calculate AQL sample size based on lot size, inspection level and regime"""
        if not all([self.lot_size, self.inspection_level, self.inspection_regime]):
            return
            
        # Find sample code letter based on lot size and inspection level
        sample_code_letter = self.get_sample_code_letter(self.lot_size, self.inspection_level)
        
        if sample_code_letter:
            # Query AQL Table for sample size
            aql_record = frappe.db.get_value("AQL Table", {
                "inspection_level": self.inspection_level,
                "inspection_regime": self.inspection_regime,
                "sample_code_letter": sample_code_letter,
                "is_active": 1
            }, ["sample_size"], order_by="modified desc")
            
            if aql_record:
                self.sample_size = aql_record
            else:
                frappe.msgprint(f"No AQL table entry found for Level: {self.inspection_level}, Regime: {self.inspection_regime}, Letter: {sample_code_letter}")
                
    def get_sample_code_letter(self, lot_size, inspection_level):
        """Get sample code letter based on lot size and inspection level"""
        # This is a simplified mapping - in reality this would be more complex
        # Based on MIL-STD-105E / ISO 2859-1 standard
        
        if inspection_level == "Level I":
            if lot_size <= 8: return "A"
            elif lot_size <= 13: return "A"
            elif lot_size <= 20: return "A"
            elif lot_size <= 32: return "B"
            elif lot_size <= 50: return "B"
            elif lot_size <= 80: return "C"
            elif lot_size <= 125: return "C"
            elif lot_size <= 200: return "D"
            elif lot_size <= 315: return "E"
            elif lot_size <= 500: return "F"
            elif lot_size <= 800: return "G"
            elif lot_size <= 1250: return "H"
            elif lot_size <= 2000: return "J"
            elif lot_size <= 3150: return "K"
            elif lot_size <= 5000: return "L"
            elif lot_size <= 8000: return "M"
            elif lot_size <= 13000: return "N"
            elif lot_size <= 20000: return "P"
            elif lot_size <= 32000: return "Q"
            else: return "R"
        elif inspection_level == "Level II":
            if lot_size <= 8: return "A"
            elif lot_size <= 13: return "B"
            elif lot_size <= 20: return "C"
            elif lot_size <= 32: return "D"
            elif lot_size <= 50: return "E"
            elif lot_size <= 80: return "F"
            elif lot_size <= 125: return "G"
            elif lot_size <= 200: return "H"
            elif lot_size <= 315: return "J"
            elif lot_size <= 500: return "K"
            elif lot_size <= 800: return "L"
            elif lot_size <= 1250: return "M"
            elif lot_size <= 2000: return "N"
            elif lot_size <= 3150: return "P"
            elif lot_size <= 5000: return "Q"
            elif lot_size <= 8000: return "R"
            else: return "R"
        elif inspection_level == "Level III":
            if lot_size <= 8: return "B"
            elif lot_size <= 13: return "C"
            elif lot_size <= 20: return "D"
            elif lot_size <= 32: return "E"
            elif lot_size <= 50: return "F"
            elif lot_size <= 80: return "G"
            elif lot_size <= 125: return "H"
            elif lot_size <= 200: return "J"
            elif lot_size <= 315: return "K"
            elif lot_size <= 500: return "L"
            elif lot_size <= 800: return "M"
            elif lot_size <= 1250: return "N"
            elif lot_size <= 2000: return "P"
            elif lot_size <= 3150: return "Q"
            elif lot_size <= 5000: return "R"
            else: return "R"
        
        return "K"  # Default fallback
        
    def calculate_sampling_distribution(self):
        """Calculate bundles and pieces to sample using Smart Bundle Selection Algorithm"""
        if not self.sample_size:
            return
            
        # Generate intelligent sampling plan
        self.generate_sampling_plan()
        
        # Count total bundles and pieces from the plan
        self.bundles_to_sample = len(set([plan.bundle_id for plan in self.sampling_plan]))
        self.pieces_to_sample = sum([plan.pieces_to_inspect for plan in self.sampling_plan])
            
    def generate_sampling_plan(self):
        """Generate intelligent sampling plan using stratified sampling"""
        if not self.sample_size or not self.bundle_details:
            return
            
        # Clear existing plan
        self.sampling_plan = []
        
        # Group bundles by characteristics for stratified sampling
        bundle_groups = self._group_bundles_for_sampling()
        
        # Calculate target sample per group
        remaining_sample = self.sample_size
        selected_bundles = []
        
        # Use stratified sampling to select bundles from different groups
        for group_key, bundles in bundle_groups.items():
            if remaining_sample <= 0:
                break
                
            # Calculate proportional sample for this group
            group_sample = max(1, int(remaining_sample * len(bundles) / sum(len(g) for g in bundle_groups.values())))
            group_sample = min(group_sample, remaining_sample)
            
            # Select bundles from this group
            selected_from_group = self._select_bundles_from_group(bundles, group_sample)
            selected_bundles.extend(selected_from_group)
            remaining_sample -= sum([b['pieces_assigned'] for b in selected_from_group])
        
        # Create sampling plan items
        for i, bundle_selection in enumerate(selected_bundles, 1):
            self.append("sampling_plan", {
                "bundle_id": bundle_selection['bundle_id'],
                "bundle_index": i,
                "size": bundle_selection['size'],
                "shade": bundle_selection['shade'],
                "ply": bundle_selection['ply'],
                "component": bundle_selection['component'],
                "pieces_to_inspect": bundle_selection['pieces_assigned'],
                "units_per_bundle": bundle_selection['units_per_bundle'],
                "selection_method": "Stratified Sampling",
                "notes": f"Selected from {bundle_selection['group']} group"
            })
            
    def _group_bundles_for_sampling(self):
        """Group bundles by size, shade, and ply for stratified sampling"""
        bundle_groups = {}
        
        for bundle in self.bundle_details:
            # Create grouping key based on characteristics
            group_key = f"{bundle.size or 'Unknown'}_{bundle.shade or 'Unknown'}_{bundle.ply or 'Unknown'}"
            
            if group_key not in bundle_groups:
                bundle_groups[group_key] = []
                
            bundle_groups[group_key].append({
                'bundle_id': bundle.bundle_id,
                'size': bundle.size,
                'shade': bundle.shade,
                'ply': bundle.ply,
                'component': bundle.component,
                'units_per_bundle': int(bundle.unitsbundle or 1),
                'group': group_key
            })
            
        return bundle_groups
        
    def _select_bundles_from_group(self, bundles, target_sample):
        """Select bundles from a group to meet target sample"""
        import random
        import math
        
        selected = []
        remaining_sample = target_sample
        
        # Sort bundles by bundle_id for consistent selection
        bundles_sorted = sorted(bundles, key=lambda x: x['bundle_id'])
        
        # Calculate how many bundles we need from this group
        # Convert to int and handle any non-numeric values
        units_list = []
        for b in bundles_sorted:
            try:
                units = int(b['units_per_bundle']) if b['units_per_bundle'] else 1
            except (ValueError, TypeError):
                units = 1
            units_list.append(units)
        
        avg_units_per_bundle = sum(units_list) / len(units_list) if units_list else 1
        bundles_needed = max(1, math.ceil(remaining_sample / avg_units_per_bundle))
        bundles_needed = min(bundles_needed, len(bundles_sorted))
        
        # Use systematic sampling for even distribution
        if len(bundles_sorted) > bundles_needed:
            step = len(bundles_sorted) // bundles_needed
            selected_bundles = [bundles_sorted[i * step] for i in range(bundles_needed)]
        else:
            selected_bundles = bundles_sorted
            
        # Assign pieces to each selected bundle
        pieces_per_bundle = remaining_sample // len(selected_bundles)
        extra_pieces = remaining_sample % len(selected_bundles)
        
        for i, bundle in enumerate(selected_bundles):
            pieces_assigned = pieces_per_bundle
            if i < extra_pieces:  # Distribute extra pieces evenly
                pieces_assigned += 1
                
            # Don't exceed bundle capacity - ensure it's an integer
            try:
                bundle_capacity = int(bundle['units_per_bundle']) if bundle['units_per_bundle'] else 1
            except (ValueError, TypeError):
                bundle_capacity = 1
            pieces_assigned = min(pieces_assigned, bundle_capacity)
            
            bundle['pieces_assigned'] = pieces_assigned
            selected.append(bundle)
            
        return selected
            
    def calculate_aql_limits(self):
        """Calculate acceptance and rejection limits for each AQL level"""
        sample_code_letter = self.get_sample_code_letter(self.lot_size, self.inspection_level)
        
        # Get limits for Critical AQL
        if self.critical_aql:
            critical_limits = frappe.db.get_value("AQL Table", {
                "inspection_level": self.inspection_level,
                "inspection_regime": self.inspection_regime,
                "sample_code_letter": sample_code_letter,
                "aql_value": self.critical_aql,
                "is_active": 1
            }, ["acceptance_number", "rejection_number"])
            
            if critical_limits:
                self.critical_accept_limit = critical_limits[0]
                self.critical_reject_limit = critical_limits[1]
                
        # Get limits for Major AQL
        if self.major_aql:
            major_limits = frappe.db.get_value("AQL Table", {
                "inspection_level": self.inspection_level,
                "inspection_regime": self.inspection_regime,
                "sample_code_letter": sample_code_letter,
                "aql_value": self.major_aql,
                "is_active": 1
            }, ["acceptance_number", "rejection_number"])
            
            if major_limits:
                self.major_accept_limit = major_limits[0]
                self.major_reject_limit = major_limits[1]
                
        # Get limits for Minor AQL
        if self.minor_aql:
            minor_limits = frappe.db.get_value("AQL Table", {
                "inspection_level": self.inspection_level,
                "inspection_regime": self.inspection_regime,
                "sample_code_letter": sample_code_letter,
                "aql_value": self.minor_aql,
                "is_active": 1
            }, ["acceptance_number", "rejection_number"])
            
            if minor_limits:
                self.minor_accept_limit = minor_limits[0]
                self.minor_reject_limit = minor_limits[1]
                
    def count_defects(self):
        """Count defects by severity"""
        self.critical_defects_found = 0
        self.major_defects_found = 0
        self.minor_defects_found = 0
        
        for defect in self.defect_records:
            if defect.defect_severity == "Critical":
                self.critical_defects_found += defect.defect_count or 0
            elif defect.defect_severity == "Major":
                self.major_defects_found += defect.defect_count or 0
            elif defect.defect_severity == "Minor":
                self.minor_defects_found += defect.defect_count or 0
                
    def compute_inspection_result(self):
        """Compute Pass/Fail result based on AQL limits"""
        # Default to Pass
        result = "Pass"
        
        # Check Critical defects
        if self.critical_reject_limit is not None and self.critical_defects_found >= self.critical_reject_limit:
            result = "Fail"
            
        # Check Major defects
        elif self.major_reject_limit is not None and self.major_defects_found >= self.major_reject_limit:
            result = "Fail"
            
        # Check Minor defects
        elif self.minor_reject_limit is not None and self.minor_defects_found >= self.minor_reject_limit:
            result = "Fail"
            
        self.inspection_result = result
        
    def generate_inspection_summary(self):
        """Generate inspection summary"""
        completed_checklist = len([item for item in self.inspection_checklist if item.status != "Pending"])
        total_checklist = len(self.inspection_checklist)
        photos_captured = len([item for item in self.inspection_checklist if item.photo_evidence])
        
        summary = f"""Inspection Summary:
• Checklist Items Completed: {completed_checklist}/{total_checklist}
• Photos Captured: {photos_captured}
• Defects Recorded: {len(self.defect_records)}
• Sample Size: {self.sample_size or 0} units
• Critical Defects: {self.critical_defects_found} (Limit: {self.critical_accept_limit}/{self.critical_reject_limit})
• Major Defects: {self.major_defects_found} (Limit: {self.major_accept_limit}/{self.major_reject_limit})
• Minor Defects: {self.minor_defects_found} (Limit: {self.minor_accept_limit}/{self.minor_reject_limit})
• Final Result: {self.inspection_result or 'Pending'}"""
        
        self.inspection_summary = summary

@frappe.whitelist()
def calculate_aql_parameters(lot_size, inspection_level, inspection_regime, critical_aql=None, major_aql=None, minor_aql=None):
    """
    Calculate AQL parameters and return all calculated values for JavaScript
    """
    try:
        # Create a temporary instance to use the calculation methods
        temp_doc = frappe.new_doc("Cutting Bundle Inspection")
        temp_doc.lot_size = int(lot_size) if lot_size else 0
        temp_doc.inspection_level = inspection_level
        temp_doc.inspection_regime = inspection_regime
        temp_doc.critical_aql = critical_aql
        temp_doc.major_aql = major_aql
        temp_doc.minor_aql = minor_aql
        
        # Calculate sample size
        temp_doc.calculate_aql_sample_size()
        
        # Calculate sampling distribution
        temp_doc.calculate_sampling_distribution()
        
        # Calculate AQL limits
        temp_doc.calculate_aql_limits()
        
        # Prepare response
        result = {
            'sample_size': temp_doc.sample_size,
            'bundles_to_sample': temp_doc.bundles_to_sample,
            'pieces_to_sample': temp_doc.pieces_to_sample
        }
        
        # Add critical limits if available
        if temp_doc.critical_accept_limit is not None and temp_doc.critical_reject_limit is not None:
            result['critical_limits'] = {
                'accept': temp_doc.critical_accept_limit,
                'reject': temp_doc.critical_reject_limit
            }
        
        # Add major limits if available
        if temp_doc.major_accept_limit is not None and temp_doc.major_reject_limit is not None:
            result['major_limits'] = {
                'accept': temp_doc.major_accept_limit,
                'reject': temp_doc.major_reject_limit
            }
        
        # Add minor limits if available
        if temp_doc.minor_accept_limit is not None and temp_doc.minor_reject_limit is not None:
            result['minor_limits'] = {
                'accept': temp_doc.minor_accept_limit,
                'reject': temp_doc.minor_reject_limit
            }
        
        return result
        
    except Exception as e:
        frappe.log_error(f"Error in calculate_aql_parameters: {str(e)}")
        frappe.throw(f"Failed to calculate AQL parameters: {str(e)}")

@frappe.whitelist()
def create_from_bundle_configuration(bundle_config_name):
    """Create Cutting Bundle Inspection from Bundle Configuration"""
    if frappe.db.exists("Cutting Bundle Inspection", {"bundle_configuration_reference": bundle_config_name}):
        existing_doc = frappe.db.get_value("Cutting Bundle Inspection", 
                                         {"bundle_configuration_reference": bundle_config_name}, "name")
        return {"existing_doc": existing_doc}
    
    bundle_config = frappe.get_doc("Bundle Creation", bundle_config_name)
    
    # Create new Cutting Bundle Inspection
    inspection = frappe.new_doc("Cutting Bundle Inspection")
    inspection.bundle_configuration_reference = bundle_config_name
    inspection.inspector = frappe.session.user
    
    # Populate from bundle configuration
    inspection.populate_from_bundle_configuration()
    
    inspection.insert()
    
    return {"success": True, "inspection_name": inspection.name}