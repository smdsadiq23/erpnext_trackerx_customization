import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, cint, getdate, now, get_datetime
import json
# Removed Vue.js API imports - using inline functions


class FabricInspection(Document):
    def before_insert(self):
        """Set default values before inserting new document"""
        # AQL population moved to after_insert with error handling
        pass

    def after_insert(self):
        """Auto-populate checklist items from master checklist after document creation"""
        # Try to populate AQL fields first, but don't let it block checklist population
        try:
            self.populate_aql_fields_from_grn()
        except Exception as e:
            frappe.logger().warning(f"AQL population failed for {self.name}: {str(e)} - Continuing with checklist population")
            # Continue execution regardless of AQL errors

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
        
        # Set final status - use Submitted as per mobile API workflow
        if self.inspection_status not in ['Submitted', 'Conditional Accept']:
            self.inspection_status = 'Submitted'
        
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
    
    def validate_aql_configuration(self):
        """Validate AQL configuration and calculate sample requirements"""
        if self.inspection_type == 'AQL Based':
            # Validate required AQL fields
            if not self.aql_level:
                frappe.throw(_("AQL Level is required for AQL Based inspection"))
            if not self.aql_value:
                frappe.throw(_("AQL Value is required for AQL Based inspection"))
            if not self.inspection_regime:
                frappe.throw(_("Inspection Regime is required for AQL Based inspection"))

            if self.total_rolls:
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
            # Auto-set to 100% inspection values
            self.required_sample_size = 100
            self.required_sample_rolls = self.total_rolls or 0
            # Calculate total meters
            total_meters = sum(flt(roll.roll_length or 0) for roll in self.fabric_rolls_tab)
            self.required_sample_meters = total_meters
            # Clear AQL fields as they're not needed
            self.aql_level = None
            self.aql_value = None
            self.inspection_regime = None

        elif self.inspection_type == 'Custom Sampling':
            # Validate sampling percentage
            if not self.sampling_percentage or self.sampling_percentage <= 0 or self.sampling_percentage > 100:
                frappe.throw(_("Sampling Percentage must be between 0.1 and 100 for Custom Sampling"))

            # Calculate custom sampling requirements
            self.calculate_custom_sampling()
            # Clear AQL fields as they're not needed
            self.aql_level = None
            self.aql_value = None
            self.inspection_regime = None

    def calculate_custom_sampling(self):
        """Calculate sample requirements based on custom sampling percentage"""
        import math

        if not self.sampling_percentage or not self.total_rolls:
            return

        # Calculate sample rolls (always round up to ensure minimum 1 roll)
        sample_rolls = max(1, math.ceil(self.total_rolls * self.sampling_percentage / 100))
        self.required_sample_rolls = sample_rolls

        # Set the sampling percentage as required sample size
        self.required_sample_size = self.sampling_percentage

        # Calculate sample meters if total quantity is available
        if self.total_quantity:
            sample_meters = self.total_quantity * self.sampling_percentage / 100
            self.required_sample_meters = sample_meters
        else:
            # Calculate from roll lengths if available
            total_meters = sum(flt(roll.roll_length or 0) for roll in self.fabric_rolls_tab)
            if total_meters:
                sample_meters = total_meters * self.sampling_percentage / 100
                self.required_sample_meters = sample_meters
    
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

            # Get defects for this roll from the defects table
            if hasattr(roll, 'defects') and roll.defects:
                for defect_row in roll.defects:
                    # Points already calculated automatically in fabric_roll_inspection_defect.py
                    defect_points = flt(defect_row.points_auto or 0)
                    total_points += defect_points
                    total_defects += 1

                    # Group defects by category for summary
                    category_name = defect_row.category or 'Unknown'
                    if category_name not in defect_groups:
                        defect_groups[category_name] = {
                            'count': 0,
                            'points': 0,
                            'defects': []
                        }
                    defect_groups[category_name]['count'] += 1
                    defect_groups[category_name]['points'] += defect_points
                    defect_groups[category_name]['defects'].append(defect_row.defect or 'Unknown')
            
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
        """Simplified roll grading - Accept/Reject only"""
        # Simple grading based on 25 points threshold
        if points_per_100_sqm <= 25:
            return 'A', 'Accepted'
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
        """Simplified overall inspection result calculation"""
        if not self.fabric_rolls_tab:
            self.inspection_result = 'Pending'
            self.quality_grade = ''
            return

        # Get totals from already-calculated roll data
        total_points = 0
        total_inspected_length = 0
        total_defect_size = 0
        inspected_rolls = 0
        accepted_rolls = 0
        rejected_rolls = 0

        for roll in self.fabric_rolls_tab:
            if roll.inspected:
                inspected_rolls += 1
                total_points += flt(roll.total_defect_points or 0)
                # Use actual_length_m which is set by mobile API, fallback to roll_length
                length = flt(roll.actual_length_m or roll.roll_length or 0)
                total_inspected_length += length

                # Count defect size (for reference)
                if hasattr(roll, 'defects') and roll.defects:
                    total_defect_size += len(roll.defects)

                # Count accepted/rejected rolls for summary
                if roll.roll_result in ['Accept', 'Accepted']:
                    accepted_rolls += 1
                elif roll.roll_result in ['Reject', 'Rejected']:
                    rejected_rolls += 1

        if inspected_rolls == 0 or total_inspected_length == 0:
            self.inspection_result = 'Pending'
            self.quality_grade = ''
            return

        # Calculate overall points per 100 sqm based on inspected length
        overall_points_per_100_sqm = (total_points * 100) / total_inspected_length

        # Simple Accept/Reject logic (25 points threshold)
        if overall_points_per_100_sqm <= 25:
            self.inspection_result = 'Accepted'
            self.quality_grade = 'A'
        else:
            self.inspection_result = 'Rejected'
            self.quality_grade = 'D'

        # Store totals for reference
        self.total_defect_points = total_points
        self.overall_points_per_100_sqm = overall_points_per_100_sqm
        self.total_inspected_length = total_inspected_length
        self.total_defect_size = total_defect_size

        # Generate inspection summary using real data
        self.generate_inspection_summary(inspected_rolls, accepted_rolls, rejected_rolls, overall_points_per_100_sqm)
    
    def generate_inspection_summary(self, inspected_rolls, accepted_rolls, rejected_rolls, overall_points_per_100_sqm):
        """Generate HTML inspection summary using real fabric_roll_inspection_item data"""
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
                        <tr><td><strong>Points per 100 sqm:</strong></td><td>{overall_points_per_100_sqm:.2f}</td></tr>
                        <tr><td><strong>Total Length:</strong></td><td>{getattr(self, 'total_inspected_length', 0):.2f}m</td></tr>
                        <tr><td><strong>Overall Grade:</strong></td><td>{self.quality_grade}</td></tr>
                        <tr><td><strong>Final Result:</strong></td><td><span class="indicator {self.get_result_indicator()}">{self.inspection_result}</span></td></tr>
                    </table>
                </div>
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
        # Don't auto-update status if manually set to Hold, Submitted, Accepted, Rejected, Conditional Accept, or In Progress
        if self.inspection_status in ['Hold', 'Submitted', 'Accepted', 'Rejected', 'Conditional Accept', 'In Progress']:
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
                # When all rolls are inspected, status should be ready for submission
                # Use 'In Progress' instead of non-existent 'Completed'
                self.inspection_status = 'In Progress'
    
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
    
    def calculate_roll_grades_only(self):
        """Calculate roll grades based on existing defect data without overwriting defects"""
        if not self.fabric_rolls_tab:
            return

        for roll in self.fabric_rolls_tab:
            if not roll.inspected:
                continue

            # Get points from existing roll calculations
            points_per_100_sqm = flt(roll.points_per_100_sqm or 0)
            total_points = flt(roll.total_defect_points or 0)

            # Determine grade and result
            grade, result = self.determine_roll_grade(points_per_100_sqm, total_points)

            # Update roll fields
            roll.roll_grade = grade
            roll.roll_result = result

            # Save directly to database to avoid triggering child table overwrites
            frappe.db.set_value("Fabric Roll Inspection Item", roll.name, {
                "roll_grade": grade,
                "roll_result": result
            })

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
        elif self.inspection_type == '100% Inspection' and inspected_rolls < total_rolls:
            errors.append(f"100% inspection requires all rolls to be inspected: {inspected_rolls}/{total_rolls}")

        # For Custom Sampling, check if minimum sample size is met
        elif self.inspection_type == 'Custom Sampling':
            required_sample = cint(self.required_sample_rolls or 0)
            if inspected_rolls < required_sample:
                sampling_percent = flt(self.sampling_percentage or 0)
                errors.append(f"Custom sampling requires {required_sample} rolls to be inspected ({sampling_percent}% of {total_rolls}): {inspected_rolls}/{required_sample} inspected")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def calculate_aql_sample_size_inline(self, lot_size, aql_level, aql_value, inspection_regime='Normal'):
        """Dynamic AQL sample size calculation using AQL Table doctype"""
        try:
            # Step 1: Find the appropriate sample code letter based on lot size and inspection level
            sample_code_letter = self.get_sample_code_for_lot_size_inline(lot_size, aql_level, inspection_regime)

            if not sample_code_letter:
                frappe.log_error(f"No sample code found for lot size {lot_size}, level {aql_level}")
                return {
                    'sample_size': 100.0,
                    'sample_rolls': lot_size,
                    'sample_meters': lot_size * 50,
                    'accept_number': 0,
                    'reject_number': 1,
                    'sample_code': 'A'
                }

            # Step 2: Get AQL criteria from AQL Table doctype using the static method
            from erpnext_trackerx_customization.erpnext_trackerx_customization.doctype.aql_table.aql_table import AQLTable
            aql_criteria = AQLTable.get_aql_criteria(sample_code_letter, aql_value, inspection_regime)

            if not aql_criteria:
                frappe.log_error(f"No AQL criteria found for code {sample_code_letter}, AQL {aql_value}, regime {inspection_regime}")
                return {
                    'sample_size': 100.0,
                    'sample_rolls': lot_size,
                    'sample_meters': lot_size * 50,
                    'accept_number': 0,
                    'reject_number': 1,
                    'sample_code': sample_code_letter
                }

            sample_rolls = aql_criteria['sample_size']

            # Ensure we don't exceed lot size
            if sample_rolls > lot_size:
                sample_rolls = lot_size

            sample_size_percent = (sample_rolls / lot_size) * 100

            # Estimate sample meters (assuming average roll length)
            avg_roll_length = 50  # Default 50 meters per roll
            sample_meters = sample_rolls * avg_roll_length

            return {
                'sample_size': round(sample_size_percent, 2),
                'sample_rolls': sample_rolls,
                'sample_meters': sample_meters,
                'accept_number': aql_criteria['acceptance_number'],
                'reject_number': aql_criteria['rejection_number'],
                'sample_code': sample_code_letter
            }

        except Exception as e:
            frappe.log_error(f"Error in AQL calculation: {str(e)}")
            return {
                'sample_size': 25.0,
                'sample_rolls': 1,
                'sample_meters': 50,
                'accept_number': 0,
                'reject_number': 1,
                'sample_code': 'A'
            }

    def get_sample_code_for_lot_size_inline(self, lot_size, inspection_level, inspection_regime='Normal'):
        """Find appropriate sample code letter for given lot size from AQL Table"""
        try:
            # Query AQL Table to find matching lot size range
            aql_records = frappe.get_all("AQL Table",
                filters={
                    "inspection_level": inspection_level,
                    "inspection_regime": inspection_regime,
                    "is_active": 1
                },
                fields=["sample_code_letter", "lot_size_range"],
                order_by="sample_code_letter"
            )

            for record in aql_records:
                lot_range = record.get('lot_size_range', '')
                if self.is_lot_size_in_range_inline(lot_size, lot_range):
                    return record.get('sample_code_letter')

            # Fallback: if no range found, use smallest code for small lots
            return 'A' if lot_size <= 8 else 'B'

        except Exception as e:
            frappe.log_error(f"Error finding sample code for lot size {lot_size}: {str(e)}")
            return 'A'

    def is_lot_size_in_range_inline(self, lot_size, lot_range):
        """Check if lot size falls within the given range (e.g., '9-15', '2-8')"""
        try:
            if '-' not in lot_range:
                return False

            range_parts = lot_range.split('-')
            if len(range_parts) != 2:
                return False

            min_size = int(range_parts[0].strip())
            max_size = int(range_parts[1].strip())

            return min_size <= lot_size <= max_size

        except (ValueError, IndexError):
            return False
    

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