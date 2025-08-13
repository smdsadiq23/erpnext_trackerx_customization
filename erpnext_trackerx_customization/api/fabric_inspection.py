import frappe
import json
import math
from frappe import _
from frappe.utils import flt, cint, getdate


@frappe.whitelist()
def get_grn_rolls(grn_reference):
    """
    Fetch all rolls associated with a GRN
    """
    if not grn_reference:
        return []
    
    try:
        # Get GRN document
        grn_doc = frappe.get_doc("Goods Receipt Note", grn_reference)
        
        rolls_data = []
        
        # Check if GRN has direct roll references
        if hasattr(grn_doc, 'fabric_rolls') and grn_doc.fabric_rolls:
            for roll_item in grn_doc.fabric_rolls:
                if roll_item.roll_number:
                    # Fetch roll details from Fabric Roll doctype
                    roll_doc = frappe.get_doc("Fabric Roll", roll_item.roll_number)
                    rolls_data.append({
                        'roll_number': roll_doc.roll_id,
                        'shade_code': roll_doc.shade_code,
                        'lot_number': roll_doc.lot_no,
                        'length': flt(roll_doc.length),
                        'width': flt(roll_doc.width),
                        'gsm': flt(roll_doc.gsm)
                    })
        
        # Alternative: Get rolls from items table if roll numbers are stored there
        if not rolls_data and grn_doc.items:
            processed_rolls = set()
            for item in grn_doc.items:
                if hasattr(item, 'roll_number') and item.roll_number and item.roll_number not in processed_rolls:
                    try:
                        roll_doc = frappe.get_doc("Fabric Roll", item.roll_number)
                        rolls_data.append({
                            'roll_number': roll_doc.roll_id,
                            'shade_code': roll_doc.shade_code,
                            'lot_number': roll_doc.lot_no,
                            'length': flt(roll_doc.length),
                            'width': flt(roll_doc.width),
                            'gsm': flt(roll_doc.gsm)
                        })
                        processed_rolls.add(item.roll_number)
                    except frappe.DoesNotExistError:
                        continue
        
        # Fallback: Create dummy roll entries based on quantity
        if not rolls_data and grn_doc.items:
            for idx, item in enumerate(grn_doc.items):
                # Estimate number of rolls based on quantity (assuming standard roll lengths)
                estimated_rolls = max(1, int(flt(item.qty) / 100))  # Assuming 100m per roll average
                
                for roll_idx in range(estimated_rolls):
                    rolls_data.append({
                        'roll_number': f"{grn_reference}-R{idx+1}-{roll_idx+1}",
                        'shade_code': item.get('shade_code', ''),
                        'lot_number': item.get('lot_no', ''),
                        'length': flt(item.qty) / estimated_rolls if estimated_rolls > 0 else 0,
                        'width': 60,  # Default width in inches
                        'gsm': 0
                    })
        
        return rolls_data
        
    except Exception as e:
        frappe.log_error(f"Error fetching GRN rolls: {str(e)}")
        return []


@frappe.whitelist()
def calculate_aql_sample_size(lot_size, aql_level, aql_value, inspection_regime="Normal"):
    """
    Calculate AQL sample size based on industry standards (MIL-STD-105E / ASQ Z1.4)
    """
    lot_size = cint(lot_size)
    
    if lot_size <= 0:
        return {'sample_size': 0, 'sample_rolls': 0, 'sample_meters': 0}
    
    # AQL Sample Size Table based on MIL-STD-105E
    # Lot size ranges and corresponding sample size code letters
    lot_size_ranges = [
        (2, 8, 'A'),
        (9, 15, 'B'), 
        (16, 25, 'C'),
        (26, 50, 'D'),
        (51, 90, 'E'),
        (91, 150, 'F'),
        (151, 280, 'G'),
        (281, 500, 'H'),
        (501, 1200, 'J'),
        (1201, 3200, 'K'),
        (3201, 10000, 'L'),
        (10001, 35000, 'M'),
        (35001, 150000, 'N'),
        (150001, 500000, 'P'),
        (500001, float('inf'), 'Q')
    ]
    
    # Get sample size code letter
    code_letter = 'A'
    for min_size, max_size, letter in lot_size_ranges:
        if min_size <= lot_size <= max_size:
            code_letter = letter
            break
    
    # Sample sizes for each code letter and inspection level
    sample_size_table = {
        'Normal': {
            'A': 2, 'B': 3, 'C': 5, 'D': 8, 'E': 13, 'F': 20, 'G': 32, 'H': 50,
            'J': 80, 'K': 125, 'L': 200, 'M': 315, 'N': 500, 'P': 800, 'Q': 1250
        },
        'Tightened': {
            'A': 2, 'B': 3, 'C': 5, 'D': 8, 'E': 13, 'F': 20, 'G': 32, 'H': 50,
            'J': 80, 'K': 125, 'L': 200, 'M': 315, 'N': 500, 'P': 800, 'Q': 1250
        },
        'Reduced': {
            'A': 2, 'B': 2, 'C': 2, 'D': 3, 'E': 5, 'F': 8, 'G': 13, 'H': 20,
            'J': 32, 'K': 50, 'L': 80, 'M': 125, 'N': 200, 'P': 315, 'Q': 500
        }
    }
    
    # Get sample size
    sample_size = sample_size_table.get(inspection_regime, sample_size_table['Normal']).get(code_letter, 2)
    
    # Calculate sample rolls (minimum 1, maximum equal to lot size)
    sample_rolls = min(max(1, sample_size), lot_size)
    
    # Calculate sample percentage
    sample_percentage = (sample_rolls / lot_size) * 100
    
    # Estimate sample meters (assuming average 100m per roll)
    estimated_meters_per_roll = 100
    sample_meters = sample_rolls * estimated_meters_per_roll
    
    return {
        'sample_size': sample_percentage,
        'sample_rolls': sample_rolls,
        'sample_meters': sample_meters,
        'aql_code_letter': code_letter,
        'inspection_regime': inspection_regime
    }


@frappe.whitelist()
def calculate_defect_points(defect_code, defect_size):
    """
    Calculate defect points based on 4-point inspection system
    """
    if not defect_code or not defect_size:
        return {'points': 0, 'severity': 'Minor'}
    
    try:
        # Get defect master details
        defect_master = frappe.get_doc("Defect Master", defect_code)
        
        # Parse defect size (handle fractions and decimals)
        size_inches = parse_defect_size(defect_size)
        
        # Calculate points based on 4-point system
        points = 0
        severity = 'Minor'
        
        # Standard 4-Point System Rules:
        # 1 Point: Defects 3" or less in any direction
        # 2 Points: Defects over 3" to 6" in any direction  
        # 3 Points: Defects over 6" to 9" in any direction
        # 4 Points: Defects over 9" in any direction OR any hole
        
        if defect_master.defect_category in ['Physical Defects'] and 'hole' in defect_master.defect_name.lower():
            # Any hole is automatically 4 points
            points = 4
            severity = 'Critical'
        elif size_inches <= 3:
            points = 1
            severity = 'Minor'
        elif size_inches <= 6:
            points = 2
            severity = 'Minor'
        elif size_inches <= 9:
            points = 3
            severity = 'Major'
        else:
            points = 4
            severity = 'Critical'
        
        # Apply defect type modifiers
        if defect_master.defect_type == 'Critical':
            points = max(points, 3)
            severity = 'Critical'
        elif defect_master.defect_type == 'Major':
            points = max(points, 2)
            severity = 'Major' if severity != 'Critical' else 'Critical'
        
        # Check for specific defect criteria from master
        if defect_master.point_4_criteria and size_inches >= flt(defect_master.point_4_criteria or 9):
            points = 4
            severity = 'Critical'
        elif defect_master.point_3_criteria and size_inches >= flt(defect_master.point_3_criteria or 6):
            points = max(points, 3)
            severity = 'Major'
        elif defect_master.point_2_criteria and size_inches >= flt(defect_master.point_2_criteria or 3):
            points = max(points, 2)
        elif defect_master.point_1_criteria:
            points = max(points, 1)
        
        return {
            'points': points,
            'severity': severity,
            'defect_type': defect_master.defect_type,
            'category': defect_master.defect_category
        }
        
    except Exception as e:
        frappe.log_error(f"Error calculating defect points: {str(e)}")
        return {'points': 1, 'severity': 'Minor'}


def parse_defect_size(size_str):
    """
    Parse defect size string to numeric value in inches
    Handles formats like: "2.5", "1/4", "3 1/2", "2.25"
    """
    if not size_str:
        return 0
    
    size_str = str(size_str).strip()
    
    try:
        # Handle pure decimal
        if '/' not in size_str:
            return flt(size_str)
        
        # Handle fractions (e.g., "1/4", "3 1/2")
        if ' ' in size_str:
            # Mixed number (e.g., "3 1/2")
            parts = size_str.split(' ')
            whole = flt(parts[0])
            fraction = parts[1] if len(parts) > 1 else "0"
        else:
            # Pure fraction (e.g., "1/4")
            whole = 0
            fraction = size_str
        
        # Parse fraction
        if '/' in fraction:
            num, den = fraction.split('/')
            fraction_value = flt(num) / flt(den) if flt(den) != 0 else 0
        else:
            fraction_value = flt(fraction)
        
        return whole + fraction_value
        
    except:
        # Fallback to 0 if parsing fails
        return 0


@frappe.whitelist()
def generate_inspection_report(inspection_doc):
    """
    Generate comprehensive inspection report
    """
    try:
        inspection = frappe.get_doc("Fabric Inspection", inspection_doc)
        
        # Calculate comprehensive statistics
        stats = calculate_inspection_statistics(inspection)
        
        # Generate report content
        report_content = generate_report_html(inspection, stats)
        
        # Save as PDF or return URL
        # This would integrate with Frappe's print framework
        print_format = "Fabric Inspection Report"  # Create a custom print format
        
        return {
            'report_url': f'/api/method/frappe.utils.print_format.download_pdf?doctype=Fabric%20Inspection&name={inspection_doc}&format={print_format}',
            'report_html': report_content,
            'statistics': stats
        }
        
    except Exception as e:
        frappe.log_error(f"Error generating inspection report: {str(e)}")
        frappe.throw(_("Error generating inspection report: {0}").format(str(e)))


def calculate_inspection_statistics(inspection):
    """
    Calculate comprehensive inspection statistics
    """
    stats = {
        'total_rolls': len(inspection.fabric_rolls_tab or []),
        'inspected_rolls': 0,
        'accepted_rolls': 0,
        'rejected_rolls': 0,
        'conditional_rolls': 0,
        'total_defects': 0,
        'total_points': 0,
        'average_points_per_roll': 0,
        'defect_categories': {},
        'grade_distribution': {'A': 0, 'B': 0, 'C': 0},
        'inspection_efficiency': 0,
        'aql_compliance': True
    }
    
    if not inspection.fabric_rolls_tab:
        return stats
    
    total_area = 0
    
    for roll in inspection.fabric_rolls_tab:
        if roll.inspected:
            stats['inspected_rolls'] += 1
            
            # Count results
            if roll.roll_result in ['Accepted', 'First Quality']:
                stats['accepted_rolls'] += 1
            elif roll.roll_result == 'Rejected':
                stats['rejected_rolls'] += 1
            elif roll.roll_result in ['Conditional Accept', 'Second Quality']:
                stats['conditional_rolls'] += 1
            
            # Points and defects
            stats['total_points'] += flt(roll.total_defect_points or 0)
            
            if roll.defects:
                roll_defects = len(roll.defects)
                stats['total_defects'] += roll_defects
                
                # Categorize defects
                for defect in roll.defects:
                    category = defect.defect_category or 'Other'
                    if category not in stats['defect_categories']:
                        stats['defect_categories'][category] = {'count': 0, 'points': 0}
                    
                    stats['defect_categories'][category]['count'] += 1
                    stats['defect_categories'][category]['points'] += flt(defect.defect_points or 0)
            
            # Grade distribution
            if roll.roll_grade in stats['grade_distribution']:
                stats['grade_distribution'][roll.roll_grade] += 1
            
            # Calculate area
            roll_area = (flt(roll.roll_length or 0) * flt(roll.roll_width or 0)) / 1550  # Convert to sqm
            total_area += roll_area
    
    # Calculate averages and percentages
    if stats['inspected_rolls'] > 0:
        stats['average_points_per_roll'] = stats['total_points'] / stats['inspected_rolls']
        stats['acceptance_rate'] = (stats['accepted_rolls'] / stats['inspected_rolls']) * 100
        stats['rejection_rate'] = (stats['rejected_rolls'] / stats['inspected_rolls']) * 100
    
    # Inspection efficiency
    if stats['total_rolls'] > 0:
        stats['inspection_efficiency'] = (stats['inspected_rolls'] / stats['total_rolls']) * 100
    
    # AQL compliance check
    if inspection.inspection_type == 'AQL Based':
        required_sample = flt(inspection.required_sample_rolls or 0)
        stats['aql_compliance'] = stats['inspected_rolls'] >= required_sample
    
    stats['total_area_inspected'] = total_area
    if total_area > 0:
        stats['defect_density_per_sqm'] = stats['total_defects'] / total_area
        stats['points_per_100_sqm'] = (stats['total_points'] / total_area) * 100
    
    return stats


def generate_report_html(inspection, stats):
    """
    Generate HTML report content
    """
    html = f"""
    <div class="inspection-report">
        <h2>Fabric Inspection Report</h2>
        <div class="report-header">
            <table>
                <tr>
                    <td><strong>Inspection ID:</strong> {inspection.name}</td>
                    <td><strong>Date:</strong> {inspection.inspection_date}</td>
                </tr>
                <tr>
                    <td><strong>GRN Reference:</strong> {inspection.grn_reference}</td>
                    <td><strong>Inspector:</strong> {inspection.inspector}</td>
                </tr>
                <tr>
                    <td><strong>Supplier:</strong> {inspection.supplier}</td>
                    <td><strong>Inspection Type:</strong> {inspection.inspection_type}</td>
                </tr>
            </table>
        </div>
        
        <div class="statistics-summary">
            <h3>Inspection Summary</h3>
            <table class="table table-bordered">
                <tr>
                    <td>Total Rolls</td><td>{stats['total_rolls']}</td>
                    <td>Inspected Rolls</td><td>{stats['inspected_rolls']}</td>
                </tr>
                <tr>
                    <td>Accepted</td><td>{stats['accepted_rolls']}</td>
                    <td>Rejected</td><td>{stats['rejected_rolls']}</td>
                </tr>
                <tr>
                    <td>Total Defects</td><td>{stats['total_defects']}</td>
                    <td>Total Points</td><td>{stats['total_points']:.2f}</td>
                </tr>
                <tr>
                    <td>Acceptance Rate</td><td>{stats.get('acceptance_rate', 0):.1f}%</td>
                    <td>Overall Result</td><td>{inspection.inspection_result}</td>
                </tr>
            </table>
        </div>
        
        <div class="roll-details">
            <h3>Roll-wise Results</h3>
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>Roll Number</th>
                        <th>Length (m)</th>
                        <th>Grade</th>
                        <th>Points</th>
                        <th>Result</th>
                        <th>Defects</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    # Add roll details
    for roll in (inspection.fabric_rolls_tab or []):
        if roll.inspected:
            defect_count = len(roll.defects) if roll.defects else 0
            html += f"""
                <tr>
                    <td>{roll.roll_number}</td>
                    <td>{roll.roll_length:.2f}</td>
                    <td>{roll.roll_grade}</td>
                    <td>{roll.total_defect_points:.2f}</td>
                    <td>{roll.roll_result}</td>
                    <td>{defect_count}</td>
                </tr>
            """
    
    html += """
                </tbody>
            </table>
        </div>
    </div>
    """
    
    return html


@frappe.whitelist()
def get_defect_categories():
    """
    Get defect categories organized by category with points from Defect Master
    """
    try:
        defects = frappe.get_all(
            "Defect Master",
            fields=["defect_code", "defect_name", "defect_category", "point_1_criteria", "point_2_criteria", "point_3_criteria", "point_4_criteria"],
            filters={"is_active": 1, "inspection_type": "Fabric Inspection"},
            order_by="defect_category, defect_name"
        )
        
        categories = {}
        
        for defect in defects:
            category = defect.defect_category or "Other"
            
            if category not in categories:
                categories[category] = []
            
            # Determine points based on criteria (simplified - you can enhance this)
            points = 2  # Default
            if defect.point_4_criteria:
                points = 4
            elif defect.point_3_criteria:
                points = 3
            elif defect.point_2_criteria:
                points = 2
            elif defect.point_1_criteria:
                points = 1
                
            categories[category].append({
                "code": defect.defect_code,
                "name": defect.defect_name,
                "points": points
            })
        
        # If no defects found, return default categories
        if not categories:
            return get_default_defect_categories()
            
        return categories
        
    except Exception as e:
        frappe.log_error(f"Error fetching defect categories: {str(e)}")
        return get_default_defect_categories()


def get_default_defect_categories():
    """
    Default defect categories as fallback
    """
    return {
        'Holes & Yarn': [
            { 'code': 'HOLE', 'name': 'Holes', 'points': 4 },
            { 'code': 'PROC_HOLE', 'name': 'Processing Holes', 'points': 4 },
            { 'code': 'THIN_YARN', 'name': 'Thin Yarn', 'points': 2 },
            { 'code': 'THICK_YARN', 'name': 'Thick Yarn', 'points': 2 }
        ],
        'Stains & Marks': [
            { 'code': 'BLACK_DOT', 'name': 'Black Dot Oil Stain', 'points': 3 },
            { 'code': 'GREASE', 'name': 'Grease Mark', 'points': 3 },
            { 'code': 'RUST', 'name': 'Rust Stain', 'points': 3 }
        ],
        'Surface Defects': [
            { 'code': 'LOOP_PULL', 'name': 'Loop Pull', 'points': 2 },
            { 'code': 'COMPACT', 'name': 'Compact Mark', 'points': 2 },
            { 'code': 'SLUBS', 'name': 'Slubs', 'points': 1 },
            { 'code': 'WHITE_PATCH', 'name': 'White Patches', 'points': 2 },
            { 'code': 'YELLOW_PATCH', 'name': 'Yellow Patches', 'points': 2 }
        ]
    }


@frappe.whitelist()
def get_aql_standards():
    """
    Get available AQL standards and levels
    """
    return {
        'aql_levels': ['I', 'II', 'III', 'S-1', 'S-2', 'S-3', 'S-4'],
        'aql_values': ['0.010', '0.015', '0.025', '0.040', '0.065', '0.10', '0.15', '0.25', '0.40', '0.65', '1.0', '1.5', '2.5', '4.0', '6.5', '10', '15', '25', '40', '65', '100'],
        'inspection_regimes': ['Normal', 'Tightened', 'Reduced'],
        'inspection_methods': ['Full Roll', '4-Point Method', 'Random Sampling', '10-Point Method', 'ASQ Z1.4', 'MIL-STD-105E']
    }


@frappe.whitelist()
def validate_inspection_completion(inspection_doc):
    """
    Validate if inspection meets AQL requirements
    """
    try:
        inspection = frappe.get_doc("Fabric Inspection", inspection_doc)
        
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'aql_compliance': True
        }
        
        # Check if required rolls are inspected
        if inspection.inspection_type == 'AQL Based':
            required_rolls = cint(inspection.required_sample_rolls or 0)
            inspected_count = sum(1 for roll in (inspection.fabric_rolls_tab or []) if roll.inspected)
            
            if inspected_count < required_rolls:
                validation_result['errors'].append(
                    f"AQL sampling requires {required_rolls} rolls to be inspected, but only {inspected_count} are marked as inspected"
                )
                validation_result['aql_compliance'] = False
        
        elif inspection.inspection_type == '100% Inspection':
            total_rolls = len(inspection.fabric_rolls_tab or [])
            inspected_count = sum(1 for roll in (inspection.fabric_rolls_tab or []) if roll.inspected)
            
            if inspected_count < total_rolls:
                validation_result['errors'].append(
                    f"100% Inspection requires all {total_rolls} rolls to be inspected, but only {inspected_count} are completed"
                )
        
        # Check for incomplete defect entries
        incomplete_defects = 0
        for roll in (inspection.fabric_rolls_tab or []):
            if roll.inspected and roll.defects:
                for defect in roll.defects:
                    if not defect.defect_code or not defect.defect_size:
                        incomplete_defects += 1
        
        if incomplete_defects > 0:
            validation_result['warnings'].append(
                f"{incomplete_defects} defect entries are missing required information (defect code or size)"
            )
        
        validation_result['valid'] = len(validation_result['errors']) == 0
        
        return validation_result
        
    except Exception as e:
        frappe.log_error(f"Error validating inspection: {str(e)}")
        return {
            'valid': False,
            'errors': [f"Validation error: {str(e)}"],
            'warnings': [],
            'aql_compliance': False
        }


@frappe.whitelist()
def save_inspection_data(inspection_name, defects_data, rolls_data):
    """
    Save fabric inspection defects data and roll information
    """
    try:
        # Get the document
        doc = frappe.get_doc("Fabric Inspection", inspection_name)
        
        # Check permissions
        if not doc.has_permission("write"):
            frappe.throw(_("You don't have permission to modify this document"))
        
        # Update defects data
        if defects_data:
            if isinstance(defects_data, str):
                doc.defects_data = defects_data
            else:
                doc.defects_data = json.dumps(defects_data)
        
        # Update rolls data if provided
        if rolls_data:
            for roll_number, roll_data in rolls_data.items():
                # Find the matching roll in fabric_rolls_tab
                for roll in doc.fabric_rolls_tab:
                    if roll.roll_number == roll_number:
                        # Update roll fields - handle all important fields
                        updatable_fields = [
                            'compact_roll_no', 'roll_length', 'roll_width', 'gsm',
                            'shade_code', 'lot_number', 'sample_length', 
                            'inspection_method', 'inspection_percentage',
                            'total_defect_points', 'points_per_100_sqm', 
                            'roll_grade', 'roll_result'
                        ]
                        
                        for field in updatable_fields:
                            if field in roll_data:
                                value = roll_data[field]
                                # Convert to appropriate type
                                if field in ['roll_length', 'roll_width', 'gsm', 'sample_length', 
                                           'inspection_percentage', 'total_defect_points', 'points_per_100_sqm']:
                                    value = flt(value) if value is not None else 0
                                elif field in ['compact_roll_no', 'shade_code', 'lot_number', 
                                             'inspection_method', 'roll_grade', 'roll_result']:
                                    value = str(value) if value is not None else ''
                                
                                setattr(roll, field, value)
                        break
        
        # Calculate and update inspection results
        calculate_four_point_inspection_results(doc, defects_data)
        
        # Save the document
        doc.save()
        
        frappe.db.commit()
        
        return {
            "status": "success",
            "message": _("Inspection data saved successfully"),
            "doc_name": doc.name
        }
        
    except Exception as e:
        frappe.log_error(f"Error saving inspection data: {str(e)}")
        frappe.throw(_("Error saving inspection data: {0}").format(str(e)))


def calculate_four_point_inspection_results(doc, defects_data):
    """
    Calculate inspection results based on four-point defects data
    """
    try:
        if not defects_data:
            return
        
        if isinstance(defects_data, str):
            defects_data = json.loads(defects_data)
        
        total_points = 0
        total_area = 0
        inspected_rolls = 0
        
        # Calculate for each roll
        for roll in doc.fabric_rolls_tab:
            if not roll.roll_number:
                continue
                
            roll_defects = defects_data.get(roll.roll_number, {})
            if not roll_defects:
                continue
            
            # Calculate roll totals
            roll_total_points = 0
            roll_total_size = 0
            
            for defect_key, size in roll_defects.items():
                size = float(size) if size else 0
                if size > 0:
                    points = get_four_point_defect_points(defect_key)
                    roll_total_points += size * points
                    roll_total_size += size
            
            # Update roll fields
            roll.total_defect_points = roll_total_points
            
            # Calculate points per 100 sqm using four-point formula
            roll_length = float(roll.roll_length) if roll.roll_length else 0
            roll_width = float(roll.roll_width) if roll.roll_width else 0
            
            if roll_length > 0 and roll_width > 0:
                # Four-point system formula: (Total Points × 39 × 100) ÷ (Length × Width)
                roll_area = roll_length * roll_width
                roll.points_per_100_sqm = (roll_total_points * 39 * 100) / roll_area if roll_area > 0 else 0
                
                # Determine roll grade and result based on four-point thresholds
                if roll.points_per_100_sqm <= 25:
                    roll.roll_grade = 'A'
                    roll.roll_result = 'Accepted'
                elif roll.points_per_100_sqm <= 50:
                    roll.roll_grade = 'B'
                    roll.roll_result = 'Conditional Accept'
                else:
                    roll.roll_grade = 'C'
                    roll.roll_result = 'Rejected'
                
                total_points += roll_total_points
                total_area += roll_area
                inspected_rolls += 1
        
        # Update document totals
        doc.total_defect_points = total_points
        
        # Calculate overall inspection result using four-point system
        overall_penalty_per_100 = (total_points * 39 * 100) / total_area if total_area > 0 else 0
        
        if overall_penalty_per_100 <= 25:
            doc.inspection_result = 'Accepted'
            doc.quality_grade = 'A'
        elif overall_penalty_per_100 <= 50:
            doc.inspection_result = 'Conditional Accept'
            doc.quality_grade = 'B'
        else:
            doc.inspection_result = 'Rejected'
            doc.quality_grade = 'C'
        
        # Update inspection status
        if inspected_rolls > 0:
            doc.inspection_status = 'Completed'
        
        # Generate four-point inspection summary
        generate_four_point_summary(doc, {
            'total_points': total_points,
            'total_area': total_area,
            'inspected_rolls': inspected_rolls,
            'overall_penalty_per_100': overall_penalty_per_100
        })
        
    except Exception as e:
        frappe.log_error(f"Error calculating four-point inspection results: {str(e)}")


def get_four_point_defect_points(defect_key):
    """
    Get points for a defect based on its key in four-point system
    """
    points_map = {
        'HOLE': 4,
        'PROC_HOLE': 4,
        'THIN_YARN': 2,
        'THICK_YARN': 2,
        'BLACK_DOT': 3,
        'GREASE': 3,
        'RUST': 3
    }
    
    # Extract defect code from key
    parts = defect_key.split('_')
    defect_code = parts[-1] if parts else defect_key
    
    return points_map.get(defect_code, 2)  # Default to 2 points


def generate_four_point_summary(doc, stats):
    """
    Generate four-point inspection summary HTML
    """
    try:
        summary = f"""
        <div class="four-point-inspection-summary">
            <h4>Four-Point Fabric Inspection Summary</h4>
            <table class="table table-bordered">
                <tr>
                    <td><strong>Total Defect Points:</strong></td>
                    <td>{stats['total_points']:.2f}</td>
                </tr>
                <tr>
                    <td><strong>Total Inspected Area:</strong></td>
                    <td>{stats['total_area']:.2f} sq inches</td>
                </tr>
                <tr>
                    <td><strong>Inspected Rolls:</strong></td>
                    <td>{stats['inspected_rolls']}</td>
                </tr>
                <tr>
                    <td><strong>Penalty Points per 100 sqm:</strong></td>
                    <td>{stats['overall_penalty_per_100']:.2f}</td>
                </tr>
                <tr>
                    <td><strong>Four-Point Threshold:</strong></td>
                    <td>≤ 25 points per 100 sqm for acceptance</td>
                </tr>
                <tr>
                    <td><strong>Final Decision:</strong></td>
                    <td><strong>{doc.inspection_result}</strong></td>
                </tr>
            </table>
            <p><small>Generated using Four-Point Inspection System on {frappe.utils.now()}</small></p>
        </div>
        """
        
        doc.inspection_summary = summary
        
    except Exception as e:
        frappe.log_error(f"Error generating four-point summary: {str(e)}")


@frappe.whitelist()
def get_inspection_data_for_ui(inspection_name):
    """
    Get fabric inspection data formatted for the UI page
    """
    try:
        doc = frappe.get_doc("Fabric Inspection", inspection_name)
        
        if not doc.has_permission("read"):
            frappe.throw(_("You don't have permission to view this document"))
        
        # Get defects data
        defects_data = {}
        if doc.defects_data:
            try:
                defects_data = json.loads(doc.defects_data) if isinstance(doc.defects_data, str) else doc.defects_data
            except json.JSONDecodeError:
                defects_data = {}
        
        # Get fabric rolls
        fabric_rolls = []
        for roll in doc.fabric_rolls_tab:
            fabric_rolls.append({
                'roll_number': roll.roll_number,
                'roll_length': roll.roll_length,
                'roll_width': roll.roll_width,
                'gsm': roll.gsm,
                'compact_roll_no': roll.compact_roll_no,
                'shade_code': roll.shade_code,
                'lot_number': roll.lot_number,
                'total_defect_points': roll.total_defect_points,
                'points_per_100_sqm': roll.points_per_100_sqm,
                'roll_grade': roll.roll_grade,
                'roll_result': roll.roll_result
            })
        
        return {
            'inspection_doc': {
                'name': doc.name,
                'inspection_date': str(doc.inspection_date),
                'inspector': doc.inspector,
                'supplier': doc.supplier,
                'item_name': doc.item_name,
                'item_code': doc.item_code,
                'grn_reference': doc.grn_reference,
                'total_quantity': doc.total_quantity,
                'total_rolls': doc.total_rolls,
                'inspection_status': doc.inspection_status,
                'inspection_result': doc.inspection_result,
                'total_defect_points': doc.total_defect_points,
                'quality_grade': doc.quality_grade
            },
            'defects_data': defects_data,
            'fabric_rolls': fabric_rolls,
            'can_write': doc.has_permission("write")
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting inspection data for UI: {str(e)}")
        frappe.throw(_("Error loading inspection data: {0}").format(str(e)))