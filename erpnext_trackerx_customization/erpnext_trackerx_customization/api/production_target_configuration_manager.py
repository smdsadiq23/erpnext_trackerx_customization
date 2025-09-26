# api.py - Backend API endpoints for Production Target Manager
import frappe
from frappe import _
from frappe.utils import now
import json

@frappe.whitelist()
def get_production_data():
    """Get all required data for production target configuration"""
    try:
        # Get Physical Cells
        physical_cells = frappe.get_all('Physical Cell', 
            fields=['name', 'operator_count', 'supported_operation_group'],
            order_by='name'
        )
        
        # Get Styles (Items with custom_select_master == "Finished Goods")
        styles = frappe.get_all('Item',
            filters={'custom_select_master': 'Finished Goods'},
            fields=['name', 'item_code'],
            order_by='name'
        )
        
        # Get existing active configurations (only current active versions)
        existing_configs = frappe.get_all('Production Target Configuration',
            filters={'is_active': 1},
            fields=['name', 'physical_cell', 'style', 'sam', 'operator', 'efficiency', 'hour_target', 'is_active', 'start', 'end'],
            order_by='physical_cell, style'
        )

        sams = {}

        for cell in physical_cells:
            for style in styles:
                sam = calculate_sam(cell, style)
                sams[f"{cell.name}###{style.name}"] = sam
                
        
        return {
            'physical_cells': physical_cells,
            'styles': styles,
            'existing_configs': existing_configs,
            'sams': sams
        }
    except Exception as e:
        frappe.log_error(f"Error in get_production_data: {str(e)}")
        frappe.throw(_("Error fetching production data: {0}").format(str(e)))

@frappe.whitelist()
def calculate_sam(physical_cell, style):
    """Calculate SAM for given physical cell and style combination"""
    try:
        # Get supported operation group from physical cell
        cell_doc = frappe.get_doc('Physical Cell', physical_cell)
        supported_operation_group = cell_doc.supported_operation_group
        
        if not supported_operation_group:
            return 0
        
        # Get operations matching the operation group
        operations = frappe.get_all('Operation',
            filters={'custom_operation_group': supported_operation_group},
            fields=['name']
        )
        
        if not operations:
            return 0
        
        operation_names = [op.name for op in operations]
        
        # Get item document and check BOM operations
        item_doc = frappe.get_doc('Item', style)
        if not hasattr(item_doc, 'custom_bom_operations'):
            return 0
        
        total_sam = 0
        for bom_op in item_doc.custom_bom_operations:
            if bom_op.operation in operation_names:
                total_sam += bom_op.time_in_mins or 0
        
        return round(total_sam, 2)
        
    except Exception as e:
        frappe.log_error(f"Error calculating SAM for {physical_cell}-{style}: {str(e)}")
        return 0

@frappe.whitelist()
def calculate_target_from_efficiency(efficiency, operator, sam):
    """Calculate target from efficiency"""
    try:
        efficiency = float(efficiency)
        operator = float(operator)
        sam = float(sam)
        
        if sam == 0:
            return 0
        
        target = (efficiency * 60 * operator) / sam
        return round(target, 2)
        
    except Exception as e:
        frappe.log_error(f"Error calculating target: {str(e)}")
        return 0

@frappe.whitelist()
def calculate_efficiency_from_target(target, operator, sam):
    """Calculate efficiency from target"""
    try:
        target = float(target)
        operator = float(operator)
        sam = float(sam)
        
        if operator == 0 or sam == 0:
            return 0
        
        efficiency = (target * sam) / (60 * operator)
        return round(efficiency * 100, 2)  # Convert to percentage
        
    except Exception as e:
        frappe.log_error(f"Error calculating efficiency: {str(e)}")
        return 0

@frappe.whitelist()
def save_configuration(data):
    """Save or update production target configuration with versioning"""
    try:
        data = json.loads(data) if isinstance(data, str) else data
        current_time = now()
        
        # Check if active configuration exists for this combination
        existing_active = frappe.db.get_value('Production Target Configuration',
            {
                'physical_cell': data['physical_cell'], 
                'style': data['style'], 
                'is_active': 1
            }, 
            ['name', 'sam', 'efficiency', 'hour_target']
        )
        
        if existing_active:
            existing_name, existing_sam, existing_efficiency, existing_target = existing_active
            
            # Check if values have actually changed
            values_changed = (
                float(data.get('sam', 0)) != float(existing_sam or 0) or
                float(data.get('efficiency', 0)) != float(existing_efficiency or 0) or
                float(data.get('hour_target', 0)) != float(existing_target or 0)
            )
            
            if values_changed:
                # Mark existing record as inactive and set end time
                existing_doc = frappe.get_doc('Production Target Configuration', existing_name)
                existing_doc.is_active = 0
                existing_doc.end = current_time
                existing_doc.save()
                
                # Create new active record
                new_doc = frappe.new_doc('Production Target Configuration')
                new_doc.physical_cell = data['physical_cell']
                new_doc.style = data['style']
                new_doc.sam = data.get('sam', 0)
                new_doc.operator = data.get('operator', 0)
                new_doc.efficiency = data.get('efficiency', 0)
                new_doc.hour_target = data.get('hour_target', 0)
                new_doc.start = current_time
                new_doc.end = None
                new_doc.is_active = 1
                new_doc.save()
                
                return {
                    'status': 'updated',
                    'message': 'Configuration updated with new version',
                    'name': new_doc.name
                }
            else:
                return {
                    'status': 'unchanged',
                    'message': 'No changes detected',
                    'name': existing_name
                }
        else:
            # Create new configuration (first time)
            new_doc = frappe.new_doc('Production Target Configuration')
            new_doc.physical_cell = data['physical_cell']
            new_doc.style = data['style']
            new_doc.sam = data.get('sam', 0)
            new_doc.operator = data.get('operator', 0)
            new_doc.efficiency = data.get('efficiency', 0)
            new_doc.hour_target = data.get('hour_target', 0)
            new_doc.start = current_time
            new_doc.end = None
            new_doc.is_active = 1
            new_doc.save()
            
            return {
                'status': 'created',
                'message': 'New configuration created',
                'name': new_doc.name
            }
        
    except Exception as e:
        frappe.log_error(f"Error saving configuration: {str(e)}")
        frappe.throw(_("Error saving configuration: {0}").format(str(e)))

@frappe.whitelist()
def bulk_update_configurations(configurations):
    """Bulk update multiple configurations"""
    try:
        configurations = json.loads(configurations) if isinstance(configurations, str) else configurations
        results = []
        
        for config in configurations:
            result = save_configuration(config)
            results.append(result)
        
        frappe.db.commit()
        
        return {
            'status': 'success',
            'message': f'Updated {len(results)} configurations',
            'results': results
        }
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Error in bulk update: {str(e)}")
        frappe.throw(_("Error in bulk update: {0}").format(str(e)))

@frappe.whitelist()
def get_configuration_history(physical_cell, style):
    """Get version history for a specific physical cell and style combination"""
    try:
        history = frappe.get_all('Production Target Configuration',
            filters={
                'physical_cell': physical_cell,
                'style': style
            },
            fields=['name', 'sam', 'operator', 'efficiency', 'hour_target', 'start', 'end', 'is_active', 'creation', 'modified'],
            order_by='start desc'
        )
        
        return history
        
    except Exception as e:
        frappe.log_error(f"Error getting configuration history: {str(e)}")
        frappe.throw(_("Error getting configuration history: {0}").format(str(e)))

@frappe.whitelist()
def cleanup_old_configurations():
    """Clean up configuration versions older than 1 year"""
    try:
        from frappe.utils import add_days
        
        cutoff_date = add_days(now(), -365)
        
        old_configs = frappe.get_all('Production Target Configuration',
            filters={
                'is_active': 0,
                'end': ['<', cutoff_date]
            },
            pluck='name'
        )
        
        count = 0
        for config_name in old_configs:
            frappe.delete_doc('Production Target Configuration', config_name)
            count += 1
        
        frappe.db.commit()
        
        return {
            'status': 'success',
            'message': f'Cleaned up {count} old configuration versions',
            'count': count
        }
        
    except Exception as e:
        frappe.log_error(f"Error in cleanup: {str(e)}")
        frappe.throw(_("Error in cleanup: {0}").format(str(e)))

@frappe.whitelist()
def calculate_sam(physical_cell, style):
    """Calculate SAM for given physical cell and style combination"""
    try:
        # Get supported operation group from physical cell
        cell_doc = frappe.get_doc('Physical Cell', physical_cell)
        supported_operation_group = cell_doc.supported_operation_group
        
        if not supported_operation_group:
            return 0
        
        # Get operations matching the operation group
        operations = frappe.get_all('Operation',
            filters={'custom_operation_group': supported_operation_group},
            fields=['name']
        )
        
        if not operations:
            return 0
        
        operation_names = [op.name for op in operations]
        
        # Get item document and check BOM operations
        item_doc = frappe.get_doc('Item', style)
        if not hasattr(item_doc, 'custom_bom_operations'):
            return 0
        
        total_sam = 0
        for bom_op in item_doc.custom_bom_operations:
            if bom_op.operation in operation_names:
                total_sam += bom_op.time_in_mins or 0
        
        return round(total_sam, 2)
        
    except Exception as e:
        frappe.log_error(f"Error calculating SAM for {physical_cell}-{style}: {str(e)}")
        return 0

@frappe.whitelist()
def calculate_target_from_efficiency(efficiency, operator, sam):
    """Calculate target from efficiency"""
    try:
        efficiency = float(efficiency)
        operator = float(operator)
        sam = float(sam)
        
        if sam == 0:
            return 0
        
        target = (efficiency * 60 * operator) / sam
        return round(target, 2)
        
    except Exception as e:
        frappe.log_error(f"Error calculating target: {str(e)}")
        return 0

@frappe.whitelist()
def calculate_efficiency_from_target(target, operator, sam):
    """Calculate efficiency from target"""
    try:
        target = float(target)
        operator = float(operator)
        sam = float(sam)
        
        if operator == 0 or sam == 0:
            return 0
        
        efficiency = (target * sam) / (60 * operator)
        return round(efficiency * 100, 2)  # Convert to percentage
        
    except Exception as e:
        frappe.log_error(f"Error calculating efficiency: {str(e)}")
        return 0

@frappe.whitelist()
def save_configuration(data):
    """Save or update production target configuration with versioning"""
    try:
        data = json.loads(data) if isinstance(data, str) else data
        current_time = now()
        
        # Check if active configuration exists for this combination
        existing_active = frappe.db.get_value('Production Target Configuration',
            {
                'physical_cell': data['physical_cell'], 
                'style': data['style'], 
                'is_active': 1
            }, 
            ['name', 'sam', 'efficiency', 'hour_target']
        )
        
        if existing_active:
            existing_name, existing_sam, existing_efficiency, existing_target = existing_active
            
            # Check if values have actually changed
            values_changed = (
                float(data.get('sam', 0)) != float(existing_sam or 0) or
                float(data.get('efficiency', 0)) != float(existing_efficiency or 0) or
                float(data.get('hour_target', 0)) != float(existing_target or 0)
            )
            
            if values_changed:
                # Mark existing record as inactive and set end time
                existing_doc = frappe.get_doc('Production Target Configuration', existing_name)
                existing_doc.is_active = 0
                existing_doc.end = current_time
                existing_doc.save()
                
                # Create new active record
                new_doc = frappe.new_doc('Production Target Configuration')
                new_doc.physical_cell = data['physical_cell']
                new_doc.style = data['style']
                new_doc.sam = data.get('sam', 0)
                new_doc.operator = data.get('operator', 0)
                new_doc.efficiency = data.get('efficiency', 0)
                new_doc.hour_target = data.get('hour_target', 0)
                new_doc.start = current_time
                new_doc.end = None
                new_doc.is_active = 1
                new_doc.save()
                
                return {
                    'status': 'updated',
                    'message': 'Configuration updated with new version',
                    'name': new_doc.name
                }
            else:
                return {
                    'status': 'unchanged',
                    'message': 'No changes detected',
                    'name': existing_name
                }
        else:
            # Create new configuration (first time)
            new_doc = frappe.new_doc('Production Target Configuration')
            new_doc.physical_cell = data['physical_cell']
            new_doc.style = data['style']
            new_doc.sam = data.get('sam', 0)
            new_doc.operator = data.get('operator', 0)
            new_doc.efficiency = data.get('efficiency', 0)
            new_doc.hour_target = data.get('hour_target', 0)
            new_doc.start = current_time
            new_doc.end = None
            new_doc.is_active = 1
            new_doc.save()
            
            return {
                'status': 'created',
                'message': 'New configuration created',
                'name': new_doc.name
            }
        
    except Exception as e:
        frappe.log_error(f"Error saving configuration: {str(e)}")
        frappe.throw(_("Error saving configuration: {0}").format(str(e)))

@frappe.whitelist()
def bulk_update_configurations(configurations):
    """Bulk update multiple configurations"""
    try:
        configurations = json.loads(configurations) if isinstance(configurations, str) else configurations
        results = []
        
        for config in configurations:
            result = save_configuration(config)
            results.append(result)
        
        frappe.db.commit()
        
        return {
            'status': 'success',
            'message': f'Updated {len(results)} configurations',
            'results': results
        }
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Error in bulk update: {str(e)}")
        frappe.throw(_("Error in bulk update: {0}").format(str(e)))

@frappe.whitelist()
def get_configuration_history(physical_cell, style):
    """Get version history for a specific physical cell and style combination"""
    try:
        history = frappe.get_all('Production Target Configuration',
            filters={
                'physical_cell': physical_cell,
                'style': style
            },
            fields=['name', 'sam', 'operator', 'efficiency', 'hour_target', 'start', 'end', 'is_active', 'creation', 'modified'],
            order_by='start desc'
        )
        
        return history
        
    except Exception as e:
        frappe.log_error(f"Error getting configuration history: {str(e)}")
        frappe.throw(_("Error getting configuration history: {0}").format(str(e)))