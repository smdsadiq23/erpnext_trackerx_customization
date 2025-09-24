import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, cint, getdate, now, get_datetime
import json
# Removed Vue.js API imports - using inline functions


class FabricInspection(Document):
    def before_insert(self):
        """Set default values before inserting new document"""
        self.populate_aql_fields_from_grn()

    def after_insert(self):
        """Auto-populate checklist items from master checklist after document creation"""
        # Always try to populate checklist if no items exist
        if not self.fabric_checklist_items:
            # Set default material_type if not set
            if not self.material_type:
                self.material_type = "Fabrics"  # Default material type

            try:
                self.populate_checklist_from_master()
                if self.fabric_checklist_items:  # Only save if items were added
                    self.save()
                    frappe.logger().info(f"Auto-populated {len(self.fabric_checklist_items)} checklist items for {self.name}")
            except Exception as e:
                frappe.logger().error(f"Error auto-populating checklist for {self.name}: {str(e)}")
                # Don't fail the document creation, just log the error
    
    def validate(self):
        """Validate fabric inspection before saving"""
        self.validate_inspection_setup()
        self.validate_aql_configuration()
        self.calculate_roll_results()
        self.calculate_overall_results()
        self.update_inspection_status()
    
    def before_submit(self):
        """Validate before submission"""
        validation_result = self.validate_inspection_completion_inline()
        
        if not validation_result.get('valid', False):
            errors = validation_result.get('errors', [])
            frappe.throw(_("Cannot submit inspection: {0}").format('; '.join(errors)))
        
        # Set final status
        self.inspection_status = 'Completed'
        
        # Update linked GRN if exists
        self.update_grn_inspection_status()
    
    def on_submit(self):
        """Actions after successful submission"""
        # Update fabric roll statuses
        self.update_fabric_roll_statuses()
        
        # Create quality certificates if needed
        self.create_quality_certificates()
    
    def validate_inspection_setup(self):
        """Validate basic inspection setup"""
        if not self.grn_reference:
            frappe.throw(_("GRN Reference is required"))
        
        if not self.fabric_rolls_tab:
            frappe.throw(_("At least one fabric roll must be added for inspection"))
        
        if self.inspection_type == 'AQL Based':
            if not self.aql_level:
                frappe.throw(_("AQL Level is required for AQL Based inspection"))
            if not self.aql_value:
                frappe.throw(_("AQL Value is required for AQL Based inspection"))
    
    def validate_aql_configuration(self):
        """Validate AQL configuration and calculate sample requirements"""
        if self.inspection_type == 'AQL Based' and self.total_rolls:
            # Simple AQL sample size calculation
            sample_data = self.calculate_aql_sample_size_inline(
                lot_size=self.total_rolls,
                aql_level=self.aql_level,
                aql_value=self.aql_value,
                inspection_regime=self.inspection_regime or 'Normal'
            )
            
            if sample_data:
                self.required_sample_size = sample_data.get('sample_size', 0)
                self.required_sample_rolls = sample_data.get('sample_rolls', 0)
                self.required_sample_meters = sample_data.get('sample_meters', 0)
        
        elif self.inspection_type == '100% Inspection':
            self.required_sample_size = 100
            self.required_sample_rolls = self.total_rolls or 0
            # Calculate total meters
            total_meters = sum(flt(roll.roll_length or 0) for roll in self.fabric_rolls_tab)
            self.required_sample_meters = total_meters
    
    def calculate_roll_results(self):
        """Calculate results for each inspected roll"""
        if not self.fabric_rolls_tab:
            return

        # Check if we should preserve mobile API defects
        if hasattr(self, '_preserve_mobile_defects') and self._preserve_mobile_defects:
            # Skip overwriting defects when called from mobile API
            return
        
        for roll in self.fabric_rolls_tab:
            if not roll.inspected:
                continue
            
            # Calculate defect points for each defect
            total_points = 0
            total_defects = 0
            defect_groups = {}
            
            # Get defects for this roll from the JSON defects data
            roll_defects_data = {}
            if self.defects_data:
                try:
                    defects_data = json.loads(self.defects_data) if isinstance(self.defects_data, str) else self.defects_data
                    roll_defects_data = defects_data.get(roll.roll_number, {})
                except:
                    pass
            
            if roll_defects_data:
                # Get defect master data for point calculation
                defect_master = self.get_default_defect_categories_inline()
                
                # Calculate points from the structured defects data
                for defect_key, size in roll_defects_data.items():
                    if size > 0:
                        # Parse defect_key to get category and code
                        if '_' in defect_key:
                            category_name = '_'.join(defect_key.split('_')[:-1])
                            defect_code = defect_key.split('_')[-1]
                            
                            # Find the defect in master data
                            points_per_meter = 2  # Default
                            for category, defects in defect_master.items():
                                if category == category_name:
                                    for defect in defects:
                                        if defect['code'] == defect_code:
                                            points_per_meter = defect['points']
                                            break
                            
                            # Calculate total points for this defect
                            defect_points = flt(size) * points_per_meter
                            total_points += defect_points
                            total_defects += 1
                            
                            # Group defects by category
                            if category_name not in defect_groups:
                                defect_groups[category_name] = {
                                    'count': 0,
                                    'points': 0,
                                    'defects': []
                                }
                            defect_groups[category_name]['count'] += 1
                            defect_groups[category_name]['points'] += defect_points
                            defect_groups[category_name]['defects'].append(defect_code)
            
            # Calculate roll metrics
            roll_area = self.calculate_roll_area(roll)
            points_per_100_sqm = (total_points * 100) / roll_area if roll_area > 0 else 0
            defect_density = total_defects / roll_area if roll_area > 0 else 0
            
            # Determine grade and result based on 4-point system
            grade, result = self.determine_roll_grade(points_per_100_sqm, total_points)
            
            # Update roll fields
            roll.total_defect_points = total_points
            roll.points_per_100_sqm = points_per_100_sqm
            roll.defect_density = defect_density
            roll.roll_grade = grade
            roll.roll_result = result
            roll.defect_summary_by_group = json.dumps(defect_groups)
            
            # Set accept/reject reason if needed
            if result == 'Rejected':
                roll.accept_reject_reason = self.get_rejection_reason(points_per_100_sqm, total_points)
            elif result == 'Conditional Accept':
                roll.accept_reject_reason = "Conditional acceptance based on defect points and customer requirements"
    
    def calculate_roll_area(self, roll):
        """Calculate roll area in square meters"""
        length_m = flt(roll.roll_length or 0)
        width_inches = flt(roll.roll_width or 60)  # Default 60 inches
        width_m = width_inches * 0.0254  # Convert inches to meters
        return length_m * width_m
    
    def determine_roll_grade(self, points_per_100_sqm, total_points):
        """Determine roll grade and result based on industry standards"""
        # Standard grading based on 4-point system
        if points_per_100_sqm <= 20:
            return 'A', 'First Quality'
        elif points_per_100_sqm <= 40:
            return 'B', 'Second Quality'
        elif points_per_100_sqm <= 60:
            return 'C', 'Conditional Accept'
        else:
            return 'D', 'Rejected'
    
    def get_rejection_reason(self, points_per_100_sqm, total_points):
        """Get specific rejection reason"""
        reasons = []
        
        if points_per_100_sqm > 60:
            reasons.append(f"Excessive defect points per 100 sqm ({points_per_100_sqm:.2f})")
        
        if total_points > 40:  # Arbitrary threshold
            reasons.append(f"High total defect points ({total_points:.2f})")
        
        return '; '.join(reasons) if reasons else "Quality standards not met"
    
    def calculate_overall_results(self):
        """Calculate overall inspection results"""
        if not self.fabric_rolls_tab:
            return
        
        total_points = 0
        total_defects = 0
        inspected_rolls = 0
        accepted_rolls = 0
        rejected_rolls = 0
        grade_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
        
        for roll in self.fabric_rolls_tab:
            if roll.inspected:
                inspected_rolls += 1
                total_points += flt(roll.total_defect_points or 0)
                
                # Count defects from the roll's defects table
                if hasattr(roll, 'defects') and roll.defects:
                    total_defects += len(roll.defects)
                
                # Count results
                if roll.roll_result in ['First Quality', 'Accepted']:
                    accepted_rolls += 1
                elif roll.roll_result == 'Rejected':
                    rejected_rolls += 1
                
                # Count grades
                grade = roll.roll_grade or 'D'
                if grade in grade_counts:
                    grade_counts[grade] += 1
        
        # Update overall fields
        self.total_defect_points = total_points
        
        # Determine overall result
        if inspected_rolls == 0:
            overall_result = 'Pending'
            overall_grade = ''
        else:
            acceptance_rate = (accepted_rolls / inspected_rolls) * 100
            
            if acceptance_rate >= 95:
                overall_result = 'Accepted'
                overall_grade = 'A'
            elif acceptance_rate >= 85:
                overall_result = 'Conditional Accept'
                overall_grade = 'B'
            else:
                overall_result = 'Rejected'
                overall_grade = 'C'
        
        self.inspection_result = overall_result
        self.quality_grade = overall_grade
        
        # Generate inspection summary
        self.generate_inspection_summary(inspected_rolls, accepted_rolls, rejected_rolls, grade_counts)
    
    def generate_inspection_summary(self, inspected_rolls, accepted_rolls, rejected_rolls, grade_counts):
        """Generate HTML inspection summary"""
        total_rolls = len(self.fabric_rolls_tab)
        acceptance_rate = (accepted_rolls / inspected_rolls * 100) if inspected_rolls > 0 else 0
        
        summary_html = f"""
        <div class="inspection-summary">
            <h4>Inspection Summary</h4>
            <div class="row">
                <div class="col-sm-6">
                    <table class="table table-condensed">
                        <tr><td><strong>Total Rolls:</strong></td><td>{total_rolls}</td></tr>
                        <tr><td><strong>Inspected:</strong></td><td>{inspected_rolls}</td></tr>
                        <tr><td><strong>Accepted:</strong></td><td>{accepted_rolls}</td></tr>
                        <tr><td><strong>Rejected:</strong></td><td>{rejected_rolls}</td></tr>
                    </table>
                </div>
                <div class="col-sm-6">
                    <table class="table table-condensed">
                        <tr><td><strong>Acceptance Rate:</strong></td><td>{acceptance_rate:.1f}%</td></tr>
                        <tr><td><strong>Total Points:</strong></td><td>{self.total_defect_points:.2f}</td></tr>
                        <tr><td><strong>Overall Grade:</strong></td><td>{self.quality_grade}</td></tr>
                        <tr><td><strong>Final Result:</strong></td><td><span class="indicator {self.get_result_indicator()}">{self.inspection_result}</span></td></tr>
                    </table>
                </div>
            </div>
            <div class="grade-distribution">
                <h5>Grade Distribution:</h5>
                <p>Grade A: {grade_counts['A']} | Grade B: {grade_counts['B']} | Grade C: {grade_counts['C']} | Grade D: {grade_counts['D']}</p>
            </div>
        </div>
        """
        
        self.inspection_summary = summary_html
    
    def get_result_indicator(self):
        """Get indicator class for result display"""
        result_indicators = {
            'Accepted': 'green',
            'Conditional Accept': 'orange', 
            'Rejected': 'red',
            'Pending': 'grey'
        }
        return result_indicators.get(self.inspection_result, 'grey')
    
    def update_inspection_status(self):
        """Update inspection status based on progress"""
        # Don't auto-update status if manually set to Hold, Completed, Accepted, Rejected, Conditional Accept, or In Progress
        if self.inspection_status in ['Hold', 'Completed', 'Accepted', 'Rejected', 'Conditional Accept', 'In Progress']:
            return
            
        if not self.fabric_rolls_tab:
            # Only set to Draft if currently not set or if it was Draft
            if not self.inspection_status or self.inspection_status == 'Draft':
                self.inspection_status = 'Draft'
            return
        
        total_rolls = len(self.fabric_rolls_tab)
        inspected_rolls = sum(1 for roll in self.fabric_rolls_tab if roll.inspected)
        
        # Only auto-update status if it's currently Draft or empty
        if not self.inspection_status or self.inspection_status == 'Draft':
            if inspected_rolls == 0:
                self.inspection_status = 'Draft'
            elif inspected_rolls < total_rolls:
                self.inspection_status = 'In Progress'
            else:
                self.inspection_status = 'Completed'
    
    def update_grn_inspection_status(self):
        """Update inspection status in linked GRN"""
        if not self.grn_reference:
            return
        
        try:
            grn = frappe.get_doc("Goods Receipt Note", self.grn_reference)
            
            # Update GRN status based on inspection result
            if self.inspection_result == 'Accepted':
                grn.quality_inspection_status = 'Passed'
            elif self.inspection_result == 'Rejected':
                grn.quality_inspection_status = 'Failed'
            else:
                grn.quality_inspection_status = 'Partial'
            
            grn.fabric_inspection_reference = self.name
            grn.save()
            
        except Exception as e:
            frappe.log_error(f"Error updating GRN inspection status: {str(e)}")
    
    def update_fabric_roll_statuses(self):
        """Update individual fabric roll inspection statuses"""
        if not self.fabric_rolls_tab:
            return
        
        for roll in self.fabric_rolls_tab:
            if not roll.inspected:
                continue
            
            try:
                # Try to find and update the actual Fabric Roll document
                roll_filters = {'roll_id': roll.roll_number}
                
                if frappe.db.exists("Fabric Roll", roll_filters):
                    fabric_roll = frappe.get_doc("Fabric Roll", roll_filters)
                    
                    # Update inspection details
                    fabric_roll.inspection_status = 'Passed' if roll.roll_result in ['First Quality', 'Accepted'] else 'Rejected'
                    fabric_roll.inspector_name = self.inspector
                    fabric_roll.inspection_date = self.inspection_date
                    fabric_roll.total_defect_points = roll.total_defect_points
                    fabric_roll.points_per_100_sqm = roll.points_per_100_sqm
                    fabric_roll.fabric_grade = roll.roll_grade
                    fabric_roll.final_result = roll.roll_result
                    fabric_roll.inspection_remarks = roll.roll_remarks
                    
                    # Copy defects if the Fabric Roll has a defects table
                    # Check if we should preserve mobile API defects
                    if not (hasattr(self, '_preserve_mobile_defects') and self._preserve_mobile_defects):
                        roll_defects = [d for d in (self.all_defects or []) if d.roll_reference == roll.roll_number]
                        if hasattr(fabric_roll, 'defects') and roll_defects:
                            fabric_roll.defects = []  # Clear existing
                            for defect in roll_defects:
                                fabric_roll.append('defects', {
                                    'defect_code': defect.defect_code,
                                    'defect_name': defect.defect_name,
                                    'defect_category': defect.defect_category,
                                    'location_yard': defect.location_yard,
                                    'location_position': defect.location_position,
                                    'defect_size': defect.defect_size,
                                    'defect_points': defect.defect_points,
                                    'severity': defect.severity,
                                    'defect_image': defect.defect_image,
                                    'remarks': defect.remarks
                                })
                    
                    fabric_roll.save()
                    
            except Exception as e:
                frappe.log_error(f"Error updating fabric roll {roll.roll_number}: {str(e)}")
    
    def create_quality_certificates(self):
        """Create quality certificates for accepted rolls"""
        accepted_rolls = [roll for roll in self.fabric_rolls_tab 
                         if roll.inspected and roll.roll_result in ['First Quality', 'Accepted']]
        
        if not accepted_rolls:
            return
        
        try:
            # Create a Quality Certificate document (if this DocType exists)
            if frappe.db.exists("DocType", "Quality Certificate"):
                quality_cert = frappe.new_doc("Quality Certificate")
                quality_cert.inspection_reference = self.name
                quality_cert.grn_reference = self.grn_reference
                quality_cert.supplier = self.supplier
                quality_cert.item_code = self.item_code
                quality_cert.certificate_date = getdate()
                quality_cert.inspector = self.inspector
                quality_cert.overall_result = self.inspection_result
                quality_cert.quality_grade = self.quality_grade
                
                # Add accepted rolls
                for roll in accepted_rolls:
                    quality_cert.append('certified_rolls', {
                        'roll_number': roll.roll_number,
                        'roll_grade': roll.roll_grade,
                        'roll_length': roll.roll_length,
                        'defect_points': roll.total_defect_points
                    })
                
                quality_cert.save()
                frappe.msgprint(_("Quality Certificate {0} created for {1} accepted rolls").format(
                    quality_cert.name, len(accepted_rolls)
                ))
                
        except Exception as e:
            frappe.log_error(f"Error creating quality certificate: {str(e)}")
    
    def populate_aql_fields_from_grn(self):
        """Populate AQL configuration fields from GRN and Item master when creating fabric inspection"""
        if not self.grn_reference or not self.item_code:
            return
            
        try:
            # Get GRN document to extract roll information
            grn_doc = frappe.get_doc("Goods Receipt Note", self.grn_reference)
            
            # Count total rolls from GRN items
            total_rolls = 0
            if hasattr(grn_doc, 'items'):
                for item in grn_doc.items:
                    if item.item_code == self.item_code and item.material_type == 'Fabrics':
                        total_rolls += 1  # Each item record represents one roll for fabrics
            
            # Set total rolls to inspect (same as total rolls for now)
            self.total_rolls_to_inspect = total_rolls
            
            # Get Item master document for AQL configuration
            item_doc = frappe.get_doc("Item", self.item_code)
            
            # Copy AQL fields from Item master if they exist
            if hasattr(item_doc, 'aql_level') and item_doc.aql_level:
                self.aql_level = item_doc.aql_level
            
            if hasattr(item_doc, 'inspection_regime') and item_doc.inspection_regime:
                self.inspection_regime = item_doc.inspection_regime
            else:
                self.inspection_regime = 'Normal'  # Default value
                
            if hasattr(item_doc, 'aql_value') and item_doc.aql_value:
                self.aql_value = item_doc.aql_value
            
            # Set inspection type based on business logic
            # You can customize this logic based on your requirements
            if hasattr(item_doc, 'inspection_type') and item_doc.inspection_type:
                # Validate and correct inspection type from Item master
                item_inspection_type = item_doc.inspection_type
                
                # Fix common invalid values
                if item_inspection_type == 'AQL':
                    item_inspection_type = 'AQL Based'
                elif item_inspection_type == '100%':
                    item_inspection_type = '100% Inspection'
                elif item_inspection_type == 'Custom':
                    item_inspection_type = 'Custom Sampling'
                
                # Validate against allowed options
                valid_options = ['AQL Based', '100% Inspection', 'Custom Sampling']
                if item_inspection_type in valid_options:
                    self.inspection_type = item_inspection_type
                else:
                    frappe.logger().warning(f"Invalid inspection_type '{item_inspection_type}' from Item {self.item_code}, defaulting to 'AQL Based'")
                    self.inspection_type = 'AQL Based'
            else:
                # Default logic: use AQL Based for most items, 100% for critical items
                if hasattr(item_doc, 'item_group') and item_doc.item_group in ['Critical Fabric', 'High Value Fabric']:
                    self.inspection_type = '100% Inspection'
                else:
                    self.inspection_type = 'AQL Based'
            
            frappe.logger().info(f"Populated AQL fields from GRN {self.grn_reference} and Item {self.item_code}: "
                               f"total_rolls_to_inspect={self.total_rolls_to_inspect}, "
                               f"aql_level={self.aql_level}, "
                               f"inspection_regime={self.inspection_regime}, "
                               f"aql_value={self.aql_value}, "
                               f"inspection_type={self.inspection_type}")
                               
        except Exception as e:
            frappe.logger().error(f"Error populating AQL fields from GRN: {str(e)}")
            # Set default values if there's an error
            if not self.total_rolls_to_inspect:
                self.total_rolls_to_inspect = cint(self.total_rolls or 0)
            if not self.inspection_regime:
                self.inspection_regime = 'Normal'
            if not self.inspection_type:
                self.inspection_type = 'AQL Based'
            
            # Validate inspection_type even in error handling
            valid_options = ['AQL Based', '100% Inspection', 'Custom Sampling']
            if self.inspection_type not in valid_options:
                frappe.logger().warning(f"Invalid inspection_type '{self.inspection_type}' detected, correcting to 'AQL Based'")
                self.inspection_type = 'AQL Based'
    
    @frappe.whitelist()
    def recalculate_all_results(self):
        """Recalculate all roll and overall results"""
        self.calculate_roll_results()
        self.calculate_overall_results()
        self.save()
        return True
    
    @frappe.whitelist()
    def update_aql_fields_from_grn(self):
        """Method to be called from client-side to update AQL fields"""
        self.populate_aql_fields_from_grn()
        return {
            'total_rolls_to_inspect': self.total_rolls_to_inspect,
            'aql_level': self.aql_level,
            'inspection_regime': self.inspection_regime,
            'aql_value': self.aql_value,
            'inspection_type': self.inspection_type
        }
    
    @frappe.whitelist() 
    def get_inspection_statistics(self):
        """Get detailed inspection statistics"""
        stats = {
            'total_rolls': len(self.fabric_rolls_tab or []),
            'inspected_rolls': 0,
            'pending_rolls': 0,
            'accepted_rolls': 0,
            'rejected_rolls': 0,
            'total_defects': 0,
            'total_points': flt(self.total_defect_points or 0),
            'grade_distribution': {'A': 0, 'B': 0, 'C': 0, 'D': 0},
            'defect_categories': {},
            'aql_compliance': True
        }
        
        for roll in (self.fabric_rolls_tab or []):
            if roll.inspected:
                stats['inspected_rolls'] += 1
                
                if roll.roll_result in ['First Quality', 'Accepted']:
                    stats['accepted_rolls'] += 1
                elif roll.roll_result == 'Rejected':
                    stats['rejected_rolls'] += 1
                
                if roll.roll_grade in stats['grade_distribution']:
                    stats['grade_distribution'][roll.roll_grade] += 1
                
                roll_defects = [d for d in (self.all_defects or []) if d.roll_reference == roll.roll_number]
                if roll_defects:
                    stats['total_defects'] += len(roll_defects)
                    
                    for defect in roll_defects:
                        category = defect.defect_category or 'Other'
                        if category not in stats['defect_categories']:
                            stats['defect_categories'][category] = 0
                        stats['defect_categories'][category] += 1
            else:
                stats['pending_rolls'] += 1
        
        # Check AQL compliance
        if self.inspection_type == 'AQL Based':
            required_sample = cint(self.required_sample_rolls or 0)
            stats['aql_compliance'] = stats['inspected_rolls'] >= required_sample
        
        return stats
    
    # Inline helper functions (replacing removed API functions)
    
    def validate_inspection_completion_inline(self):
        """Validate that inspection is complete before submission"""
        errors = []
        
        if not self.fabric_rolls_tab:
            errors.append("No fabric rolls found for inspection")
        
        total_rolls = len(self.fabric_rolls_tab or [])
        inspected_rolls = sum(1 for roll in self.fabric_rolls_tab if roll.inspected)
        
        if inspected_rolls == 0:
            errors.append("No rolls have been inspected")
        
        # For AQL inspection, check if minimum sample size is met
        if self.inspection_type == 'AQL Based':
            required_sample = cint(self.required_sample_rolls or 0)
            if inspected_rolls < required_sample:
                errors.append(f"Minimum sample size not met: {inspected_rolls}/{required_sample} rolls inspected")
        
        # For 100% inspection, all rolls must be inspected
        if self.inspection_type == '100% Inspection' and inspected_rolls < total_rolls:
            errors.append(f"100% inspection requires all rolls to be inspected: {inspected_rolls}/{total_rolls}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def calculate_aql_sample_size_inline(self, lot_size, aql_level, aql_value, inspection_regime='Normal'):
        """Simple AQL sample size calculation"""
        
        # Basic AQL table mapping
        aql_map = {
            'I': {
                '0.4': {'sample': 8, 'accept': 0, 'reject': 1},
                '0.65': {'sample': 13, 'accept': 0, 'reject': 1},
                '1.0': {'sample': 20, 'accept': 0, 'reject': 1},
                '1.5': {'sample': 32, 'accept': 1, 'reject': 2},
                '2.5': {'sample': 50, 'accept': 2, 'reject': 3},
                '4.0': {'sample': 80, 'accept': 3, 'reject': 4},
            },
            'II': {
                '0.4': {'sample': 13, 'accept': 0, 'reject': 1},
                '0.65': {'sample': 20, 'accept': 0, 'reject': 1},
                '1.0': {'sample': 32, 'accept': 1, 'reject': 2},
                '1.5': {'sample': 50, 'accept': 2, 'reject': 3},
                '2.5': {'sample': 80, 'accept': 3, 'reject': 4},
                '4.0': {'sample': 125, 'accept': 5, 'reject': 6},
            },
            'III': {
                '0.4': {'sample': 20, 'accept': 0, 'reject': 1},
                '0.65': {'sample': 32, 'accept': 1, 'reject': 2},
                '1.0': {'sample': 50, 'accept': 2, 'reject': 3},
                '1.5': {'sample': 80, 'accept': 3, 'reject': 4},
                '2.5': {'sample': 125, 'accept': 5, 'reject': 6},
                '4.0': {'sample': 200, 'accept': 7, 'reject': 8},
            }
        }
        
        # Get sample requirements
        level_data = aql_map.get(aql_level, aql_map['II'])  # Default to Level II
        aql_data = level_data.get(str(aql_value), level_data.get('2.5'))  # Default to 2.5
        
        sample_size = aql_data['sample']
        
        # Adjust based on lot size
        if lot_size < sample_size:
            sample_rolls = lot_size
            sample_size_percent = 100
        else:
            sample_rolls = min(sample_size, lot_size)
            sample_size_percent = (sample_rolls / lot_size) * 100
        
        # Estimate sample meters (assuming average roll length)
        avg_roll_length = 50  # Default 50 meters per roll
        sample_meters = sample_rolls * avg_roll_length
        
        return {
            'sample_size': round(sample_size_percent, 2),
            'sample_rolls': sample_rolls,
            'sample_meters': sample_meters,
            'accept_number': aql_data['accept'],
            'reject_number': aql_data['reject']
        }
    
    def get_default_defect_categories_inline(self):
        """Get default defect categories and their point values"""
        
        return {
            'Weaving': [
                {'code': 'BROKEN_END', 'name': 'Broken End', 'points': 1},
                {'code': 'BROKEN_PICK', 'name': 'Broken Pick', 'points': 1},
                {'code': 'FLOAT', 'name': 'Float', 'points': 2},
                {'code': 'SLACK_TENSION', 'name': 'Slack Tension', 'points': 2},
                {'code': 'REED_MARK', 'name': 'Reed Mark', 'points': 3},
                {'code': 'MISPICK', 'name': 'Mispick', 'points': 2}
            ],
            'Yarn': [
                {'code': 'THICK_PLACE', 'name': 'Thick Place', 'points': 1},
                {'code': 'THIN_PLACE', 'name': 'Thin Place', 'points': 1},
                {'code': 'NEPS', 'name': 'Neps', 'points': 1},
                {'code': 'SLUB', 'name': 'Slub', 'points': 2},
                {'code': 'FOREIGN_YARN', 'name': 'Foreign Yarn', 'points': 4},
                {'code': 'HAIRINESS', 'name': 'Hairiness', 'points': 1}
            ],
            'Dyeing': [
                {'code': 'SHADE_VARIATION', 'name': 'Shade Variation', 'points': 4},
                {'code': 'COLOR_BLEEDING', 'name': 'Color Bleeding', 'points': 4},
                {'code': 'UNEVEN_DYEING', 'name': 'Uneven Dyeing', 'points': 3},
                {'code': 'STAINING', 'name': 'Staining', 'points': 3},
                {'code': 'COLOR_SPOT', 'name': 'Color Spot', 'points': 2}
            ],
            'Finishing': [
                {'code': 'CREASE_MARK', 'name': 'Crease Mark', 'points': 2},
                {'code': 'SHINE_MARK', 'name': 'Shine Mark', 'points': 2},
                {'code': 'PILLING', 'name': 'Pilling', 'points': 2},
                {'code': 'HAND_FEEL', 'name': 'Hand Feel', 'points': 1},
                {'code': 'CHEMICAL_SPOT', 'name': 'Chemical Spot', 'points': 4}
            ],
            'Physical': [
                {'code': 'HOLE', 'name': 'Hole', 'points': 4},
                {'code': 'TEAR', 'name': 'Tear', 'points': 4},
                {'code': 'CUT_MARK', 'name': 'Cut Mark', 'points': 3},
                {'code': 'SOIL_MARK', 'name': 'Soil Mark', 'points': 2},
                {'code': 'OIL_STAIN', 'name': 'Oil Stain', 'points': 3}
            ]
        }

    def populate_checklist_from_master(self):
        """Populate checklist items from Master Checklist based on material type"""
        if not self.material_type:
            # Set default material_type
            self.material_type = "Fabrics"
            frappe.logger().info(f"Set default material_type to 'Fabrics' for inspection {self.name}")

        try:
            # First check if Master Checklist doctype exists
            if not frappe.db.exists("DocType", "Master Checklist"):
                frappe.logger().warning("Master Checklist doctype does not exist")
                return

            # Get master checklist items for this material type
            master_items = frappe.get_all(
                'Master Checklist',
                filters={
                    'material_type': self.material_type,
                    'is_active': 1
                },
                fields=[
                    'test_parameter', 'standard_requirement', 'test_method',
                    'test_category', 'is_mandatory', 'display_order',
                    'unit_of_measurement', 'tolerance', 'description'
                ],
                order_by='display_order, test_parameter'
            )

            if not master_items:
                # Try to create default checklist items if none exist
                frappe.logger().info(f"No master checklist items found for material_type: {self.material_type}")
                self.create_default_checklist_items()
                return

            # Clear existing checklist items (if any)
            self.set('fabric_checklist_items', [])

            # Add master checklist items to fabric inspection
            for item in master_items:
                self.append('fabric_checklist_items', {
                    'test_parameter': item.test_parameter,
                    'standard_requirement': item.standard_requirement,
                    'test_method': item.test_method or '',
                    'test_category': item.test_category or '',
                    'is_mandatory': item.is_mandatory or 0,
                    'unit_of_measurement': item.unit_of_measurement or '',
                    'tolerance': item.tolerance or '',
                    'description': item.description or '',
                    'display_order': item.display_order or 999,
                    'status': '',  # To be filled during inspection
                    'actual_result': '',
                    'remarks': ''
                })

            frappe.logger().info(f"Populated {len(master_items)} checklist items for material_type: {self.material_type}")

        except Exception as e:
            frappe.logger().error(f"Error populating checklist from master for {self.name}: {str(e)}")
            frappe.log_error(f"Error populating checklist from master: {str(e)}")

    def create_default_checklist_items(self):
        """Create default checklist items if no Master Checklist exists"""
        try:
            default_items = [
                {
                    'test_parameter': 'GSM Check',
                    'standard_requirement': '150-160',
                    'test_method': 'ASTM D3776',
                    'test_category': 'Physical',
                    'is_mandatory': 1,
                    'unit_of_measurement': 'gsm',
                    'tolerance': '±5',
                    'description': 'Fabric weight per square meter',
                    'display_order': 1
                },
                {
                    'test_parameter': 'Fabric Width',
                    'standard_requirement': '58-60 inches',
                    'test_method': 'Manual Measurement',
                    'test_category': 'Dimensional',
                    'is_mandatory': 1,
                    'unit_of_measurement': 'inches',
                    'tolerance': '±1',
                    'description': 'Fabric width measurement',
                    'display_order': 2
                },
                {
                    'test_parameter': 'Color Fastness',
                    'standard_requirement': 'Grade 4-5',
                    'test_method': 'AATCC 61',
                    'test_category': 'Color',
                    'is_mandatory': 1,
                    'unit_of_measurement': 'Grade',
                    'tolerance': '±0.5',
                    'description': 'Color fastness to laundering',
                    'display_order': 3
                }
            ]

            # Clear existing checklist items
            self.set('fabric_checklist_items', [])

            # Add default items
            for item in default_items:
                self.append('fabric_checklist_items', {
                    'test_parameter': item['test_parameter'],
                    'standard_requirement': item['standard_requirement'],
                    'test_method': item['test_method'],
                    'test_category': item['test_category'],
                    'is_mandatory': item['is_mandatory'],
                    'unit_of_measurement': item['unit_of_measurement'],
                    'tolerance': item['tolerance'],
                    'description': item['description'],
                    'display_order': item['display_order'],
                    'status': '',
                    'actual_result': '',
                    'remarks': ''
                })

            frappe.logger().info(f"Created {len(default_items)} default checklist items for {self.name}")

        except Exception as e:
            frappe.logger().error(f"Error creating default checklist items: {str(e)}")

    @frappe.whitelist()
    def refresh_checklist_from_master(self):
        """Refresh checklist items from Master Checklist (preserving existing results)"""
        if not self.material_type:
            frappe.throw(_("Material Type is required to refresh checklist"))

        try:
            # Store existing results
            existing_results = {}
            for item in self.fabric_checklist_items:
                key = item.test_parameter
                existing_results[key] = {
                    'status': item.status,
                    'actual_result': item.actual_result,
                    'remarks': item.remarks
                }

            # Get fresh master checklist items
            master_items = frappe.get_all(
                'Master Checklist',
                filters={
                    'material_type': self.material_type,
                    'is_active': 1
                },
                fields=[
                    'test_parameter', 'standard_requirement', 'test_method',
                    'test_category', 'is_mandatory', 'display_order',
                    'unit_of_measurement', 'tolerance', 'description'
                ],
                order_by='display_order, test_parameter'
            )

            if not master_items:
                frappe.throw(_("No active master checklist items found for material type: {0}").format(self.material_type))

            # Clear and repopulate checklist
            self.set('fabric_checklist_items', [])
            added_items = 0
            preserved_results = 0

            for item in master_items:
                # Check if we have existing results for this test parameter
                existing_result = existing_results.get(item.test_parameter, {})

                if existing_result.get('status'):
                    preserved_results += 1

                self.append('fabric_checklist_items', {
                    'test_parameter': item.test_parameter,
                    'standard_requirement': item.standard_requirement,
                    'test_method': item.test_method or '',
                    'test_category': item.test_category or '',
                    'is_mandatory': item.is_mandatory or 0,
                    'unit_of_measurement': item.unit_of_measurement or '',
                    'tolerance': item.tolerance or '',
                    'description': item.description or '',
                    'display_order': item.display_order or 999,
                    'status': existing_result.get('status', ''),
                    'actual_result': existing_result.get('actual_result', ''),
                    'remarks': existing_result.get('remarks', '')
                })
                added_items += 1

            self.save()

            return {
                'success': True,
                'message': f'Checklist refreshed from master. Added {added_items} items, preserved {preserved_results} existing results.',
                'data': {
                    'added_items': added_items,
                    'preserved_results': preserved_results,
                    'total_items': len(self.fabric_checklist_items)
                }
            }

        except Exception as e:
            frappe.log_error(f"Error refreshing checklist from master: {str(e)}")
            frappe.throw(_("Error refreshing checklist: {0}").format(str(e)))