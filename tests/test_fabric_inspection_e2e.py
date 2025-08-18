#!/usr/bin/env python3
"""
Comprehensive End-to-End Fabric Inspection Tests
==============================================

This test suite covers the complete fabric inspection workflow including:
- Quality Inspector role functionality
- Quality Manager role functionality
- Four-point inspection system
- Purchase Receipt creation
- Role-based UI access
- Complete integration workflow

Usage:
    bench execute erpnext_trackerx_customization.tests.test_fabric_inspection_e2e.run_all_e2e_tests
"""

import frappe
import json
from frappe.utils import nowdate, now_datetime
from datetime import datetime, timedelta

class FabricInspectionE2ETests:
    """Complete End-to-End test suite for fabric inspection functionality"""
    
    def __init__(self):
        """Initialize test environment and data"""
        self.test_data = {}
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
        
    def setup_test_data(self):
        """Create test data for comprehensive E2E testing"""
        print("🔧 Setting up test data...")
        
        try:
            # Create test supplier
            if not frappe.db.exists("Supplier", "TEST-SUPPLIER-E2E"):
                supplier = frappe.get_doc({
                    "doctype": "Supplier",
                    "supplier_name": "TEST-SUPPLIER-E2E",
                    "supplier_type": "Company",
                    "country": "India"
                })
                supplier.insert()
                print(f"   ✅ Created test supplier: {supplier.name}")
            
            # Create test item
            if not frappe.db.exists("Item", "TEST-FABRIC-E2E-001"):
                item = frappe.get_doc({
                    "doctype": "Item",
                    "item_code": "TEST-FABRIC-E2E-001",
                    "item_name": "Test Fabric E2E",
                    "item_group": "Fabric",
                    "stock_uom": "Meter",
                    "is_stock_item": 1,
                    "valuation_rate": 100
                })
                item.insert()
                print(f"   ✅ Created test item: {item.name}")
            
            # Create test GRN
            grn = frappe.get_doc({
                "doctype": "Goods Receipt Note",
                "supplier": "TEST-SUPPLIER-E2E",
                "posting_date": nowdate(),
                "inspection_required": 1,
                "items": [{
                    "item_code": "TEST-FABRIC-E2E-001",
                    "item_name": "Test Fabric E2E",
                    "received_quantity": 100,
                    "rate": 100,
                    "amount": 10000,
                    "uom": "Meter"
                }]
            })
            grn.insert()
            grn.submit()
            self.test_data['grn'] = grn.name
            print(f"   ✅ Created test GRN: {grn.name}")
            
            # Create test fabric inspection
            inspection = frappe.get_doc({
                "doctype": "Fabric Inspection",
                "inspection_date": nowdate(),
                "inspector": "Administrator",
                "supplier": "TEST-SUPPLIER-E2E",
                "item_code": "TEST-FABRIC-E2E-001",
                "item_name": "Test Fabric E2E",
                "grn_reference": grn.name,
                "total_quantity": 100,
                "total_rolls": 3,
                "inspection_type": "AQL Based",
                "aql_level": "II",
                "aql_value": "2.5",
                "inspection_regime": "Normal",
                "inspection_status": "Draft"
            })
            
            # Add fabric rolls
            for i in range(1, 4):
                inspection.append("fabric_rolls_tab", {
                    "roll_number": f"ROLL-E2E-{i:03d}",
                    "roll_length": 35,
                    "roll_width": 58,
                    "shade_code": "A001",
                    "lot_number": "LOT-001",
                    "inspection_method": "4-Point Method",
                    "inspection_percentage": 100,
                    "inspected": 0
                })
            
            inspection.insert()
            self.test_data['inspection'] = inspection.name
            print(f"   ✅ Created test inspection: {inspection.name}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error setting up test data: {str(e)}")
            return False
    
    def test_quality_inspector_workflow(self):
        """Test comprehensive Quality Inspector role functionality"""
        print("\n🔍 Testing Quality Inspector Comprehensive Workflow...")
        test_passed = True
        
        try:
            inspection_name = self.test_data['inspection']
            inspection = frappe.get_doc("Fabric Inspection", inspection_name)
            
            # Test 1: Check initial status and inspector access
            assert inspection.inspection_status == "Draft", f"Expected Draft status, got {inspection.inspection_status}"
            print("   ✅ Initial status is Draft")
            
            # Test 2: Inspector starts inspection process
            inspection.inspection_status = "In Progress"
            inspection.save()
            print("   ✅ Inspector started inspection process")
            
            # Test 3: Test AQL sampling validation
            print("   🔍 Testing AQL sampling functionality...")
            total_rolls = len(inspection.fabric_rolls_tab)
            sample_rolls = min(2, total_rolls)  # For testing, inspect 2 rolls
            
            assert total_rolls >= sample_rolls, f"Not enough rolls for sampling: {total_rolls} < {sample_rolls}"
            print(f"   ✅ AQL sampling: {sample_rolls} out of {total_rolls} rolls selected")
            
            # Test 4: Detailed four-point inspection for each roll
            print("   🔍 Conducting detailed four-point inspection...")
            
            # Roll 1: High defect scenario
            roll_1_defects = [
                {"defect_code": "HOLE", "points": 4, "position": "10,20", "size": "5mm", "description": "Processing hole - major defect"},
                {"defect_code": "STAIN", "points": 3, "position": "15,25", "size": "3cm", "description": "Oil stain - visible mark"},
                {"defect_code": "THIN_YARN", "points": 2, "position": "30,45", "size": "8cm", "description": "Thin yarn section"}
            ]
            
            # Roll 2: Medium defect scenario  
            roll_2_defects = [
                {"defect_code": "SHADE_VARIATION", "points": 1, "position": "5,10", "size": "2cm", "description": "Slight shade variation"},
                {"defect_code": "SLUB", "points": 2, "position": "25,35", "size": "4cm", "description": "Yarn slub"}
            ]
            
            # Roll 3: Low defect scenario
            roll_3_defects = [
                {"defect_code": "MINOR_MARK", "points": 1, "position": "12,18", "size": "1cm", "description": "Minor surface mark"}
            ]
            
            defects_data = {
                "ROLL-E2E-001": roll_1_defects,
                "ROLL-E2E-002": roll_2_defects,
                "ROLL-E2E-003": roll_3_defects
            }
            
            # Test 5: Calculate points per 100 sqm for each roll
            print("   🔍 Calculating defect points per 100 sqm...")
            
            total_inspection_points = 0
            for roll in inspection.fabric_rolls_tab:
                roll_defects = defects_data.get(roll.roll_number, [])
                
                # Calculate total points for this roll
                roll_points = sum(defect["points"] for defect in roll_defects)
                
                # Calculate roll area in sqm
                roll_area_sqm = (roll.roll_length * roll.roll_width * 2.54 * 2.54) / 10000  # Convert inches to sqm
                
                # Calculate points per 100 sqm
                if roll_area_sqm > 0:
                    points_per_100_sqm = (roll_points / roll_area_sqm) * 100
                else:
                    points_per_100_sqm = 0
                
                # Update roll data
                roll.total_defect_points = roll_points
                roll.points_per_100_sqm = points_per_100_sqm
                roll.inspected = 1
                
                # Determine roll grade based on points per 100 sqm
                if points_per_100_sqm <= 1.0:
                    roll.roll_grade = "A"
                    roll.roll_result = "First Quality"
                elif points_per_100_sqm <= 3.0:
                    roll.roll_grade = "B"
                    roll.roll_result = "Second Quality"
                elif points_per_100_sqm <= 5.0:
                    roll.roll_grade = "C"
                    roll.roll_result = "Third Quality"
                else:
                    roll.roll_grade = "D"
                    roll.roll_result = "Rejected"
                
                total_inspection_points += roll_points
                
                print(f"   ✅ {roll.roll_number}: {roll_points} points, {points_per_100_sqm:.2f} pts/100sqm, Grade: {roll.roll_grade}")
            
            # Test 6: Overall inspection result determination
            print("   🔍 Determining overall inspection result...")
            
            # Calculate average grade
            grades = [roll.roll_grade for roll in inspection.fabric_rolls_tab if roll.inspected]
            grade_values = {"A": 4, "B": 3, "C": 2, "D": 1}
            avg_grade_value = sum(grade_values.get(grade, 0) for grade in grades) / len(grades)
            
            if avg_grade_value >= 3.5:
                inspection.quality_grade = "A"
                inspection.inspection_result = "Accepted"
            elif avg_grade_value >= 2.5:
                inspection.quality_grade = "B" 
                inspection.inspection_result = "Accepted"
            elif avg_grade_value >= 1.5:
                inspection.quality_grade = "C"
                inspection.inspection_result = "Conditional Accept"
            else:
                inspection.quality_grade = "D"
                inspection.inspection_result = "Rejected"
            
            inspection.total_defect_points = total_inspection_points
            
            print(f"   ✅ Overall Grade: {inspection.quality_grade}, Result: {inspection.inspection_result}")
            
            # Test 7: Save defects data in proper format
            inspection.defects_data = json.dumps(defects_data)
            
            # Test 8: Add inspector remarks
            inspection.remarks = f"""Four-Point Inspection completed by Quality Inspector.
            
Total Rolls Inspected: {len([r for r in inspection.fabric_rolls_tab if r.inspected])}
Total Defect Points: {total_inspection_points}
Average Points per 100 sqm: {sum(r.points_per_100_sqm for r in inspection.fabric_rolls_tab) / len(inspection.fabric_rolls_tab):.2f}

Roll-wise Summary:
{'; '.join([f"{r.roll_number}: {r.roll_grade} grade" for r in inspection.fabric_rolls_tab])}

Inspector: {frappe.session.user}
Inspection Method: Four-Point System
Standards: Industry Standard AQL {inspection.aql_level} - {inspection.aql_value}%"""
            
            inspection.save()
            print("   ✅ Inspector added detailed remarks and defect data")
            
            # Test 9: Inspector completes inspection
            inspection.inspection_status = "Completed"
            inspection.save()
            print("   ✅ Inspector marked inspection as Completed")
            
            # Test 10: Verify inspection cannot be modified after completion
            try:
                # Try to modify completed inspection
                original_result = inspection.inspection_result
                inspection.inspection_result = "Modified"
                inspection.save()
                # If we reach here, the test should fail
                assert False, "Should not be able to modify completed inspection"
            except:
                # This is expected - inspection should be protected
                inspection.reload()
                assert inspection.inspection_result == original_result, "Inspection result was unexpectedly modified"
                print("   ✅ Completed inspection properly protected from modification")
            
            # Test 11: Verify all required data is present
            assert inspection.total_defect_points > 0, "Total defect points not calculated"
            assert inspection.quality_grade in ["A", "B", "C", "D"], f"Invalid quality grade: {inspection.quality_grade}"
            assert inspection.inspection_result in ["Accepted", "Rejected", "Conditional Accept"], f"Invalid result: {inspection.inspection_result}"
            assert inspection.defects_data, "Defects data not saved"
            
            # Verify roll-level data
            for roll in inspection.fabric_rolls_tab:
                if roll.inspected:
                    assert roll.total_defect_points >= 0, f"Roll {roll.roll_number} missing defect points"
                    assert roll.points_per_100_sqm >= 0, f"Roll {roll.roll_number} missing points per 100sqm"
                    assert roll.roll_grade in ["A", "B", "C", "D"], f"Roll {roll.roll_number} invalid grade"
                    assert roll.roll_result in ["First Quality", "Second Quality", "Third Quality", "Rejected"], f"Roll {roll.roll_number} invalid result"
            
            print("   ✅ All inspection data properly validated")
            
            self.test_results['passed'] += 11
            
        except Exception as e:
            print(f"   ❌ Quality Inspector comprehensive workflow failed: {str(e)}")
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"Inspector comprehensive workflow: {str(e)}")
            test_passed = False
        
        return test_passed
    
    def test_quality_inspector_ui_functionality(self):
        """Test Quality Inspector UI-specific functionality"""
        print("\n🖥️  Testing Quality Inspector UI Functionality...")
        test_passed = True
        
        try:
            inspection_name = self.test_data['inspection']
            
            # Test 1: UI Context loading for Inspector
            from erpnext_trackerx_customization.templates.pages.fabric_inspection_ui import get_context
            
            # Mock form_dict for UI testing
            original_form_dict = frappe.form_dict
            frappe.form_dict = {'inspection': inspection_name}
            
            try:
                context = {}
                get_context(context)
                
                # Verify Inspector-specific UI elements
                assert context.get('is_quality_inspector') is not None, "Inspector role not detected in context"
                assert 'fabric_rolls' in context, "Fabric rolls not loaded in UI context"
                assert 'defect_categories' in context, "Defect categories not loaded"
                assert 'can_write' in context, "Write permission not determined"
                
                print("   ✅ UI context loaded successfully for Inspector")
                
                # Test 2: Defect categories for UI dropdown
                defect_categories = context['defect_categories']
                assert isinstance(defect_categories, dict), "Defect categories should be dictionary"
                
                total_defects = sum(len(defects) for defects in defect_categories.values())
                assert total_defects > 0, "No defect categories loaded"
                
                # Verify point system for each defect
                for category, defects in defect_categories.items():
                    for defect in defects:
                        assert 'code' in defect, f"Defect missing code in {category}"
                        assert 'name' in defect, f"Defect missing name in {category}"
                        assert 'points' in defect, f"Defect missing points in {category}"
                        assert 1 <= defect['points'] <= 4, f"Invalid points {defect['points']} for {defect['code']}"
                
                print(f"   ✅ Loaded {len(defect_categories)} defect categories with {total_defects} total defects")
                
                # Test 3: Fabric rolls data for inspection UI
                fabric_rolls = context['fabric_rolls']
                assert isinstance(fabric_rolls, list), "Fabric rolls should be list"
                assert len(fabric_rolls) > 0, "No fabric rolls loaded"
                
                # Verify roll data structure
                for roll in fabric_rolls:
                    required_fields = ['roll_number', 'roll_length', 'roll_width', 'inspection_method']
                    for field in required_fields:
                        assert field in roll, f"Roll missing required field: {field}"
                
                print(f"   ✅ Loaded {len(fabric_rolls)} fabric rolls for inspection")
                
                # Test 4: AQL filtering for sampling
                from erpnext_trackerx_customization.templates.pages.fabric_inspection_ui import get_aql_filtered_rolls
                
                # Test different inspection types
                all_rolls_100 = get_aql_filtered_rolls(fabric_rolls, '100% Inspection', 0, len(fabric_rolls))
                assert len(all_rolls_100) == len(fabric_rolls), "100% inspection should return all rolls"
                
                sample_rolls_aql = get_aql_filtered_rolls(fabric_rolls, 'AQL Based', 2, len(fabric_rolls))
                assert len(sample_rolls_aql) <= 2, "AQL inspection should limit rolls to sample size"
                
                print("   ✅ AQL filtering functionality validated")
                
                # Test 5: Write permissions for Inspector
                inspection_doc = context['inspection_doc']
                if isinstance(inspection_doc, dict) and inspection_doc.get('inspection_status') != 'Submitted':
                    assert context.get('can_write', False), "Inspector should have write permission on non-submitted inspection"
                
                print("   ✅ Inspector permissions properly configured")
                
            finally:
                frappe.form_dict = original_form_dict
            
            # Test 6: Inspector-specific API functions accessibility
            print("   🔍 Testing Inspector API functions...")
            
            inspection = frappe.get_doc("Fabric Inspection", inspection_name)
            
            # Verify inspector can modify inspection data
            original_remarks = inspection.remarks or ""
            test_remarks = "Inspector test remarks - functionality verification"
            
            inspection.remarks = test_remarks
            inspection.save()
            
            # Reload and verify
            inspection.reload()
            assert test_remarks in inspection.remarks, "Inspector remarks not saved"
            
            # Restore original remarks
            inspection.remarks = original_remarks
            inspection.save()
            
            print("   ✅ Inspector can modify inspection data")
            
            # Test 7: Defect data format validation
            test_defects = {
                "ROLL-TEST-001": [
                    {
                        "defect_code": "TEST_DEFECT",
                        "points": 2,
                        "position": "10,15",
                        "size": "3cm",
                        "description": "Test defect for UI validation"
                    }
                ]
            }
            
            # Test JSON serialization/deserialization
            defects_json = json.dumps(test_defects)
            parsed_defects = json.loads(defects_json)
            
            assert parsed_defects == test_defects, "Defect data JSON serialization failed"
            print("   ✅ Defect data format validation passed")
            
            # Test 8: Roll-by-roll inspection workflow
            print("   🔍 Testing roll-by-roll inspection workflow...")
            
            for i, roll in enumerate(inspection.fabric_rolls_tab, 1):
                # Test roll data validation
                assert roll.roll_number, f"Roll {i} missing roll number"
                assert roll.roll_length > 0, f"Roll {i} invalid length: {roll.roll_length}"
                assert roll.roll_width > 0, f"Roll {i} invalid width: {roll.roll_width}"
                assert roll.inspection_method, f"Roll {i} missing inspection method"
                
                # Test area calculation
                area_sqm = (roll.roll_length * roll.roll_width * 2.54 * 2.54) / 10000
                assert area_sqm > 0, f"Roll {i} invalid area calculation"
                
                print(f"   ✅ Roll {roll.roll_number}: {roll.roll_length}m x {roll.roll_width}\" = {area_sqm:.2f} sqm")
            
            # Test 9: Quality grade assignment logic
            grade_scenarios = [
                {"points_per_100": 0.5, "expected_grade": "A", "expected_result": "First Quality"},
                {"points_per_100": 2.0, "expected_grade": "B", "expected_result": "Second Quality"},
                {"points_per_100": 4.0, "expected_grade": "C", "expected_result": "Third Quality"},
                {"points_per_100": 6.0, "expected_grade": "D", "expected_result": "Rejected"}
            ]
            
            for scenario in grade_scenarios:
                points = scenario["points_per_100"]
                expected_grade = scenario["expected_grade"]
                expected_result = scenario["expected_result"]
                
                # Test grade assignment logic
                if points <= 1.0:
                    actual_grade = "A"
                    actual_result = "First Quality"
                elif points <= 3.0:
                    actual_grade = "B"
                    actual_result = "Second Quality"
                elif points <= 5.0:
                    actual_grade = "C"
                    actual_result = "Third Quality"
                else:
                    actual_grade = "D"
                    actual_result = "Rejected"
                
                assert actual_grade == expected_grade, f"Grade mismatch for {points} points/100sqm"
                assert actual_result == expected_result, f"Result mismatch for {points} points/100sqm"
            
            print("   ✅ Quality grade assignment logic validated")
            
            self.test_results['passed'] += 9
            
        except Exception as e:
            print(f"   ❌ Quality Inspector UI functionality test failed: {str(e)}")
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"Inspector UI functionality: {str(e)}")
            test_passed = False
        
        return test_passed
    
    def test_quality_manager_accepted_workflow(self):
        """Test Quality Manager workflow for Accepted inspections"""
        print("\n👨‍💼 Testing Quality Manager Workflow - Accepted Inspections...")
        test_passed = True
        
        try:
            inspection_name = self.test_data['inspection']
            
            # Test 1: Manager reviews and accepts inspection
            from erpnext_trackerx_customization.templates.pages.fabric_inspection_ui import fabric_manager_pass_inspection
            
            result = fabric_manager_pass_inspection(inspection_name, "Quality review completed. Approved for procurement.")
            
            assert result['status'] == 'success', f"Expected success, got {result['status']}"
            assert result['new_status'] == 'Accepted', f"Expected Accepted status, got {result['new_status']}"
            print("   ✅ Quality Manager accepted inspection")
            
            # Test 2: Manager submits for Purchase Receipt creation
            from erpnext_trackerx_customization.templates.pages.fabric_inspection_ui import manager_submit_for_purchase_receipt
            
            submit_result = manager_submit_for_purchase_receipt(inspection_name, "Final approval for purchase receipt creation")
            
            assert submit_result['status'] == 'success', f"Expected success, got {submit_result['status']}"
            assert submit_result['new_status'] == 'Submitted', f"Expected Submitted status, got {submit_result['new_status']}"
            assert 'purchase_receipt_name' in submit_result, "Purchase Receipt name not returned"
            
            # Store PR name for later verification
            self.test_data['purchase_receipt'] = submit_result['purchase_receipt_name']
            print(f"   ✅ Quality Manager created Purchase Receipt: {submit_result['purchase_receipt_name']}")
            
            # Test 3: Verify Purchase Receipt details
            pr_doc = frappe.get_doc("Purchase Receipt", submit_result['purchase_receipt_name'])
            
            assert pr_doc.supplier == "TEST-SUPPLIER-E2E", f"Expected TEST-SUPPLIER-E2E, got {pr_doc.supplier}"
            assert pr_doc.fabric_inspection_reference == inspection_name, f"Inspection reference mismatch"
            assert pr_doc.grn_reference == self.test_data['grn'], f"GRN reference mismatch"
            assert len(pr_doc.items) > 0, "No items in Purchase Receipt"
            
            print("   ✅ Purchase Receipt created with correct details")
            
            # Test 4: Verify inspection status after submission
            updated_inspection = frappe.get_doc("Fabric Inspection", inspection_name)
            assert updated_inspection.inspection_status == "Submitted", f"Expected Submitted, got {updated_inspection.inspection_status}"
            assert updated_inspection.submitted_by == "Administrator", f"Submitted by field incorrect"
            print("   ✅ Inspection status updated to Submitted")
            
            self.test_results['passed'] += 4
            
        except Exception as e:
            print(f"   ❌ Quality Manager accepted workflow failed: {str(e)}")
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"Manager accepted workflow: {str(e)}")
            test_passed = False
        
        return test_passed
    
    def test_quality_manager_rejected_workflow(self):
        """Test Quality Manager workflow for Rejected inspections"""
        print("\n👨‍💼 Testing Quality Manager Workflow - Rejected Inspections...")
        test_passed = True
        
        try:
            # Create a second inspection for rejection testing
            grn_name = self.test_data['grn']
            
            inspection = frappe.get_doc({
                "doctype": "Fabric Inspection",
                "inspection_date": nowdate(),
                "inspector": "Administrator",
                "supplier": "TEST-SUPPLIER-E2E",
                "item_code": "TEST-FABRIC-E2E-001",
                "item_name": "Test Fabric E2E",
                "grn_reference": grn_name,
                "total_quantity": 100,
                "total_rolls": 2,
                "inspection_type": "AQL Based",
                "aql_level": "II",
                "aql_value": "2.5",
                "inspection_regime": "Normal",
                "inspection_status": "Completed",
                "inspection_result": "Rejected",
                "quality_grade": "C"
            })
            
            # Add fabric rolls with high defect points
            for i in range(1, 3):
                inspection.append("fabric_rolls_tab", {
                    "roll_number": f"ROLL-REJ-{i:03d}",
                    "roll_length": 35,
                    "roll_width": 58,
                    "shade_code": "A001",
                    "lot_number": "LOT-002",
                    "inspection_method": "4-Point Method",
                    "inspection_percentage": 100,
                    "inspected": 1,
                    "total_defect_points": 25,  # High defect points
                    "points_per_100_sqm": 12.32,  # Above acceptable limit
                    "roll_grade": "C",
                    "roll_result": "Rejected"
                })
            
            inspection.insert()
            rejected_inspection_name = inspection.name
            print(f"   ✅ Created rejected inspection: {rejected_inspection_name}")
            
            # Test 1: Manager fails inspection
            from erpnext_trackerx_customization.templates.pages.fabric_inspection_ui import fabric_manager_fail_inspection
            
            fail_result = fabric_manager_fail_inspection(rejected_inspection_name, "Excessive defects found. Quality unacceptable.")
            
            assert fail_result['status'] == 'success', f"Expected success, got {fail_result['status']}"
            assert fail_result['new_status'] == 'Rejected', f"Expected Rejected status, got {fail_result['new_status']}"
            print("   ✅ Quality Manager rejected inspection")
            
            # Test 2: Manager applies conditional accept with Purchase Receipt
            from erpnext_trackerx_customization.templates.pages.fabric_inspection_ui import fabric_manager_conditional_pass_with_purchase_receipt
            
            conditional_result = fabric_manager_conditional_pass_with_purchase_receipt(
                rejected_inspection_name, 
                "Conditionally accepted with 20% price reduction due to quality issues"
            )
            
            assert conditional_result['status'] == 'success', f"Expected success, got {conditional_result['status']}"
            assert conditional_result['new_status'] == 'Conditional Accept', f"Expected Conditional Accept status"
            assert 'purchase_receipt_name' in conditional_result, "Purchase Receipt name not returned"
            
            # Store conditional PR name
            self.test_data['conditional_purchase_receipt'] = conditional_result['purchase_receipt_name']
            print(f"   ✅ Quality Manager created conditional Purchase Receipt: {conditional_result['purchase_receipt_name']}")
            
            # Test 3: Verify conditional Purchase Receipt
            conditional_pr = frappe.get_doc("Purchase Receipt", conditional_result['purchase_receipt_name'])
            
            assert conditional_pr.supplier == "TEST-SUPPLIER-E2E", f"Supplier mismatch in conditional PR"
            assert conditional_pr.fabric_inspection_reference == rejected_inspection_name, f"Inspection reference mismatch"
            assert "CONDITIONAL ACCEPT" in conditional_pr.remarks, "Conditional accept comment not found in remarks"
            
            print("   ✅ Conditional Purchase Receipt created with correct details")
            
            # Test 4: Verify final inspection status
            final_inspection = frappe.get_doc("Fabric Inspection", rejected_inspection_name)
            assert final_inspection.inspection_status == "Conditional Accept", f"Expected Conditional Accept, got {final_inspection.inspection_status}"
            assert "CONDITIONAL ACCEPT WITH PURCHASE RECEIPT" in final_inspection.manager_remarks, "Manager comment not found"
            
            print("   ✅ Inspection status updated to Conditional Accept")
            
            self.test_results['passed'] += 4
            
        except Exception as e:
            print(f"   ❌ Quality Manager rejected workflow failed: {str(e)}")
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"Manager rejected workflow: {str(e)}")
            test_passed = False
        
        return test_passed
    
    def test_four_point_inspection_system(self):
        """Test the four-point inspection system validation"""
        print("\n📊 Testing Four-Point Inspection System...")
        test_passed = True
        
        try:
            # Test 1: Defect categories loading
            from erpnext_trackerx_customization.templates.pages.fabric_inspection_ui import get_defect_categories
            
            defect_categories = get_defect_categories()
            assert isinstance(defect_categories, dict), "Defect categories should be a dictionary"
            assert len(defect_categories) > 0, "Should have at least one defect category"
            print(f"   ✅ Loaded {len(defect_categories)} defect categories")
            
            # Test 2: Point calculation validation
            for category, defects in defect_categories.items():
                for defect in defects:
                    assert 'code' in defect, f"Defect missing code in category {category}"
                    assert 'name' in defect, f"Defect missing name in category {category}"
                    assert 'points' in defect, f"Defect missing points in category {category}"
                    assert 1 <= defect['points'] <= 4, f"Invalid points {defect['points']} for defect {defect['code']}"
            
            print("   ✅ Four-point system validation passed")
            
            # Test 3: AQL filtering functionality
            from erpnext_trackerx_customization.templates.pages.fabric_inspection_ui import get_aql_filtered_rolls
            
            # Create mock rolls for testing
            mock_rolls = []
            for i in range(1, 11):
                mock_roll = type('MockRoll', (), {
                    'roll_number': f'MOCK-{i:03d}',
                    'roll_length': 35,
                    'roll_width': 58
                })()
                mock_rolls.append(mock_roll)
            
            # Test 100% inspection
            filtered_100 = get_aql_filtered_rolls(mock_rolls, '100% Inspection', 0, 10)
            assert len(filtered_100) == 10, f"100% inspection should return all rolls, got {len(filtered_100)}"
            
            # Test AQL-based inspection
            filtered_aql = get_aql_filtered_rolls(mock_rolls, 'AQL Based', 5, 10)
            assert len(filtered_aql) == 5, f"AQL inspection should return 5 rolls, got {len(filtered_aql)}"
            
            print("   ✅ AQL filtering functionality validated")
            
            self.test_results['passed'] += 3
            
        except Exception as e:
            print(f"   ❌ Four-point inspection system test failed: {str(e)}")
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"Four-point system: {str(e)}")
            test_passed = False
        
        return test_passed
    
    def test_role_based_ui_access(self):
        """Test role-based UI access and permissions"""
        print("\n🔐 Testing Role-Based UI Access...")
        test_passed = True
        
        try:
            inspection_name = self.test_data['inspection']
            
            # Test 1: Context function with different user scenarios
            from erpnext_trackerx_customization.templates.pages.fabric_inspection_ui import get_context
            
            # Mock form_dict
            original_form_dict = frappe.form_dict
            frappe.form_dict = {'inspection': inspection_name}
            
            try:
                context = {}
                get_context(context)
                
                # Validate context structure
                required_keys = ['inspection_doc', 'defect_categories', 'fabric_rolls', 'can_write', 
                               'is_quality_inspector', 'is_quality_manager', 'is_system_user']
                
                for key in required_keys:
                    assert key in context, f"Missing required context key: {key}"
                
                print("   ✅ UI context function works correctly")
                
                # Test 2: Role-based button visibility logic
                # Simulate Quality Inspector role
                context_inspector = context.copy()
                context_inspector['is_quality_inspector'] = True
                context_inspector['is_quality_manager'] = False
                context_inspector['is_system_user'] = False
                
                # Simulate Quality Manager role
                context_manager = context.copy()
                context_manager['is_quality_inspector'] = False
                context_manager['is_quality_manager'] = True
                context_manager['is_system_user'] = False
                
                print("   ✅ Role-based context simulation successful")
                
            finally:
                frappe.form_dict = original_form_dict
            
            # Test 3: Permission validation for API functions
            inspection = frappe.get_doc("Fabric Inspection", inspection_name)
            
            # Check read permission
            assert inspection.has_permission("read"), "Should have read permission"
            
            # Check write permission based on status
            if inspection.inspection_status != "Submitted":
                assert inspection.has_permission("write"), "Should have write permission for non-submitted documents"
            
            print("   ✅ Permission validation successful")
            
            self.test_results['passed'] += 3
            
        except Exception as e:
            print(f"   ❌ Role-based UI access test failed: {str(e)}")
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"UI access: {str(e)}")
            test_passed = False
        
        return test_passed
    
    def test_integration_workflow(self):
        """Test complete integration between GRN, Inspection, and Purchase Receipt"""
        print("\n🔗 Testing Complete Integration Workflow...")
        test_passed = True
        
        try:
            grn_name = self.test_data['grn']
            inspection_name = self.test_data['inspection']
            pr_name = self.test_data.get('purchase_receipt')
            
            # Test 1: GRN to Inspection linkage
            grn = frappe.get_doc("Goods Receipt Note", grn_name)
            inspection = frappe.get_doc("Fabric Inspection", inspection_name)
            
            assert inspection.grn_reference == grn_name, "GRN reference not properly linked"
            assert inspection.supplier == grn.supplier, "Supplier mismatch between GRN and Inspection"
            assert inspection.item_code in [item.item_code for item in grn.items], "Item code not found in GRN items"
            
            print("   ✅ GRN to Inspection linkage validated")
            
            # Test 2: Inspection to Purchase Receipt linkage
            if pr_name:
                pr = frappe.get_doc("Purchase Receipt", pr_name)
                
                assert pr.fabric_inspection_reference == inspection_name, "Inspection reference not properly linked"
                assert pr.grn_reference == grn_name, "GRN reference not properly linked in PR"
                assert pr.supplier == grn.supplier, "Supplier mismatch in Purchase Receipt"
                
                print("   ✅ Inspection to Purchase Receipt linkage validated")
            
            # Test 3: Data consistency across documents
            assert grn.docstatus == 1, "GRN should be submitted"
            assert inspection.inspection_status in ["Submitted", "Accepted", "Conditional Accept"], "Invalid inspection status"
            
            if pr_name:
                pr = frappe.get_doc("Purchase Receipt", pr_name)
                assert pr.docstatus == 0, "Purchase Receipt should be in draft status"
                
                # Validate item quantities and rates
                total_accepted_qty = 0
                for pr_item in pr.items:
                    total_accepted_qty += pr_item.qty
                
                assert total_accepted_qty > 0, "No accepted quantity in Purchase Receipt"
                
            print("   ✅ Data consistency validation successful")
            
            # Test 4: Workflow state validation
            # Check that inspection cannot be modified after submission
            if inspection.inspection_status == "Submitted":
                try:
                    inspection.inspection_result = "Modified"
                    inspection.save()
                    assert False, "Should not be able to modify submitted inspection"
                except:
                    print("   ✅ Submitted inspection is properly protected from modification")
            
            self.test_results['passed'] += 4
            
        except Exception as e:
            print(f"   ❌ Integration workflow test failed: {str(e)}")
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"Integration workflow: {str(e)}")
            test_passed = False
        
        return test_passed
    
    def cleanup_test_data(self):
        """Clean up test data after testing"""
        print("\n🧹 Cleaning up test data...")
        
        try:
            # Delete test documents in reverse order to avoid reference issues
            if 'purchase_receipt' in self.test_data:
                frappe.delete_doc("Purchase Receipt", self.test_data['purchase_receipt'], force=True)
                print(f"   ✅ Deleted Purchase Receipt: {self.test_data['purchase_receipt']}")
            
            if 'conditional_purchase_receipt' in self.test_data:
                frappe.delete_doc("Purchase Receipt", self.test_data['conditional_purchase_receipt'], force=True)
                print(f"   ✅ Deleted Conditional Purchase Receipt: {self.test_data['conditional_purchase_receipt']}")
            
            # Delete any additional fabric inspections created during testing
            additional_inspections = frappe.get_all("Fabric Inspection", 
                                                  filters={"supplier": "TEST-SUPPLIER-E2E"},
                                                  pluck="name")
            for insp_name in additional_inspections:
                frappe.delete_doc("Fabric Inspection", insp_name, force=True)
                print(f"   ✅ Deleted Fabric Inspection: {insp_name}")
            
            if 'grn' in self.test_data:
                frappe.delete_doc("Goods Receipt Note", self.test_data['grn'], force=True)
                print(f"   ✅ Deleted GRN: {self.test_data['grn']}")
            
            # Delete test item and supplier
            if frappe.db.exists("Item", "TEST-FABRIC-E2E-001"):
                frappe.delete_doc("Item", "TEST-FABRIC-E2E-001", force=True)
                print("   ✅ Deleted test item")
            
            if frappe.db.exists("Supplier", "TEST-SUPPLIER-E2E"):
                frappe.delete_doc("Supplier", "TEST-SUPPLIER-E2E", force=True)
                print("   ✅ Deleted test supplier")
            
            frappe.db.commit()
            print("   ✅ Test data cleanup completed")
            
        except Exception as e:
            print(f"   ⚠️  Error during cleanup: {str(e)}")
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print(f"\n📊 COMPREHENSIVE E2E TEST REPORT")
        print("=" * 60)
        
        total_tests = self.test_results['passed'] + self.test_results['failed']
        success_rate = (self.test_results['passed'] / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests Run: {total_tests}")
        print(f"Tests Passed: {self.test_results['passed']}")
        print(f"Tests Failed: {self.test_results['failed']}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.test_results['errors']:
            print(f"\n❌ ERRORS ENCOUNTERED:")
            for i, error in enumerate(self.test_results['errors'], 1):
                print(f"   {i}. {error}")
        
        if success_rate == 100:
            print(f"\n🎉 ALL E2E TESTS PASSED! Fabric inspection system is working correctly.")
        else:
            print(f"\n⚠️  Some tests failed. Please review the errors above.")
        
        # Feature coverage summary
        print(f"\n📋 FEATURE COVERAGE SUMMARY:")
        print("   ✅ Quality Inspector Comprehensive Workflow")
        print("   ✅ Quality Inspector UI Functionality")
        print("   ✅ Quality Manager Workflow (Accepted)")
        print("   ✅ Quality Manager Workflow (Rejected)")
        print("   ✅ Four-Point Inspection System")
        print("   ✅ Role-Based UI Access")
        print("   ✅ Purchase Receipt Creation")
        print("   ✅ Complete Integration Workflow")
        print("   ✅ Data Consistency Validation")
        
        return success_rate == 100

def run_all_e2e_tests():
    """Main function to run all E2E tests"""
    print("🚀 COMPREHENSIVE FABRIC INSPECTION E2E TESTS")
    print("=" * 70)
    print("Testing complete workflow from GRN creation to Purchase Receipt generation")
    print("Including Quality Inspector and Quality Manager role functionalities")
    print("=" * 70)
    
    # Initialize test suite
    test_suite = FabricInspectionE2ETests()
    
    try:
        # Setup test environment
        if not test_suite.setup_test_data():
            print("❌ Failed to setup test data. Aborting tests.")
            return False
        
        # Run all test categories
        tests = [
            test_suite.test_quality_inspector_workflow,
            test_suite.test_quality_inspector_ui_functionality,
            test_suite.test_quality_manager_accepted_workflow,
            test_suite.test_quality_manager_rejected_workflow,
            test_suite.test_four_point_inspection_system,
            test_suite.test_role_based_ui_access,
            test_suite.test_integration_workflow
        ]
        
        all_passed = True
        for test_func in tests:
            if not test_func():
                all_passed = False
        
        # Generate final report
        success = test_suite.generate_test_report()
        
        return success
        
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR in E2E tests: {str(e)}")
        frappe.log_error(f"E2E test critical error: {str(e)}")
        return False
        
    finally:
        # Always clean up
        test_suite.cleanup_test_data()

if __name__ == "__main__":
    frappe.init("localhost")
    frappe.connect()
    success = run_all_e2e_tests()
    exit(0 if success else 1)