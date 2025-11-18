import frappe
from frappe.model.db_query import DatabaseQuery

@frappe.whitelist()
def get_permitted_warehouses():
    """
    Get warehouses based on user permissions and roles.
    Respects company permissions and role-based access.
    """
    try:
        # Use DatabaseQuery which automatically applies user permissions
        query = DatabaseQuery('Warehouse')
        query.fields = [
            'name', 'warehouse_name', 'parent_warehouse', 'is_group',
            'disabled', 'warehouse_type', 'capacity', 'capacity_unit',
            'business_unit', 'strategic_business_unit', 'factory', 'company'
        ]
        query.filters = [['disabled', '!=', 1]]
        query.limit_page_length = 1000

        # This automatically applies user permissions
        warehouses = query.execute()

        # If no warehouses returned and user is not System Manager, explain why
        if not warehouses:
            user_roles = frappe.get_roles(frappe.session.user)
            if 'System Manager' not in user_roles and 'Administrator' not in user_roles:
                frappe.logger().info(f"No warehouses returned for user {frappe.session.user} - check user permissions")

        frappe.logger().info(f"Returned {len(warehouses)} warehouses for user {frappe.session.user}")
        return warehouses

    except Exception as e:
        error_msg = f"Error in get_permitted_warehouses: {str(e)}"
        frappe.log_error(error_msg, "Warehouse Permissions API")
        frappe.throw(f"Error fetching warehouses: {str(e)}")

@frappe.whitelist()
def get_permitted_companies():
    """
    Get companies the current user has access to based on User Permissions.
    """
    try:
        current_user = frappe.session.user
        user_roles = frappe.get_roles(current_user)

        # Check if user is System Manager or Administrator
        if 'System Manager' in user_roles or 'Administrator' in user_roles:
            # Allow all companies for admins
            companies = frappe.get_list('Company',
                fields=['name', 'company_name'],
                order_by='company_name'
            )
            frappe.logger().info(f"System Manager {current_user} accessing all {len(companies)} companies")
            return companies

        # Check user permissions for companies
        user_companies = frappe.get_list('User Permission',
            filters={
                'user': current_user,
                'allow': 'Company'
            },
            fields=['for_value', 'is_default']
        )

        if user_companies:
            # User has specific company permissions
            company_names = [perm.for_value for perm in user_companies]
            companies = frappe.get_list('Company',
                filters={'name': ['in', company_names]},
                fields=['name', 'company_name'],
                order_by='company_name'
            )
            frappe.logger().info(f"User {current_user} has permissions for {len(companies)} companies: {company_names}")
        else:
            # No specific permissions - check default company
            default_company = frappe.db.get_value('User', current_user, 'default_company')
            if default_company:
                companies = frappe.get_list('Company',
                    filters={'name': default_company},
                    fields=['name', 'company_name']
                )
                frappe.logger().info(f"User {current_user} using default company: {default_company}")
            else:
                # No permissions and no default company
                companies = []
                frappe.logger().warning(f"User {current_user} has no company permissions or default company set")

        return companies

    except Exception as e:
        error_msg = f"Error in get_permitted_companies: {str(e)}"
        frappe.log_error(error_msg, "Warehouse Permissions API")
        frappe.throw(f"Error fetching companies: {str(e)}")

@frappe.whitelist()
def get_permitted_business_units():
    """
    Get Strategic Business Units based on user's company permissions.
    """
    try:
        permitted_companies = get_permitted_companies()
        company_names = [comp['name'] for comp in permitted_companies]

        if not company_names:
            return []

        sbus = frappe.get_list('Strategic Business Unit',
            filters={
                'is_active': 1,
                'company': ['in', company_names]
            },
            fields=['name', 'sbu_name', 'company'],
            order_by='sbu_name'
        )

        frappe.logger().info(f"Returned {len(sbus)} Strategic Business Units for user {frappe.session.user}")
        return sbus

    except Exception as e:
        error_msg = f"Error in get_permitted_business_units: {str(e)}"
        frappe.log_error(error_msg, "Warehouse Permissions API")
        return []

@frappe.whitelist()
def get_permitted_factories():
    """
    Get Factory Business Units based on user's company permissions.
    """
    try:
        permitted_companies = get_permitted_companies()
        company_names = [comp['name'] for comp in permitted_companies]

        if not company_names:
            return []

        factories = frappe.get_list('Factory Business Unit',
            filters={
                'is_active': 1,
                'company': ['in', company_names]
            },
            fields=['name', 'factory_name', 'company', 'sbu'],
            order_by='factory_name'
        )

        frappe.logger().info(f"Returned {len(factories)} Factory Business Units for user {frappe.session.user}")
        return factories

    except Exception as e:
        error_msg = f"Error in get_permitted_factories: {str(e)}"
        frappe.log_error(error_msg, "Warehouse Permissions API")
        return []

@frappe.whitelist()
def get_warehouse_types():
    """
    Get warehouse types (no permission restrictions needed).
    """
    try:
        warehouse_types = frappe.get_list('Warehouse Type',
            fields=['name'],
            order_by='name'
        )
        return warehouse_types

    except Exception as e:
        error_msg = f"Error in get_warehouse_types: {str(e)}"
        frappe.log_error(error_msg, "Warehouse Permissions API")
        return []

@frappe.whitelist()
def validate_warehouse_permission(warehouse_name):
    """
    Validate if current user has permission to access/modify a specific warehouse.
    """
    try:
        current_user = frappe.session.user
        user_roles = frappe.get_roles(current_user)

        # System Managers can access everything
        if 'System Manager' in user_roles or 'Administrator' in user_roles:
            return {'allowed': True, 'reason': 'System Manager privileges'}

        # Get warehouse company
        warehouse_company = frappe.db.get_value('Warehouse', warehouse_name, 'company')
        if not warehouse_company:
            return {'allowed': False, 'reason': 'Warehouse not found or no company assigned'}

        # Check if user has permission for this company
        permitted_companies = get_permitted_companies()
        company_names = [comp['name'] for comp in permitted_companies]

        if warehouse_company in company_names:
            return {'allowed': True, 'reason': f'User has permission for company {warehouse_company}'}
        else:
            return {'allowed': False, 'reason': f'User does not have permission for company {warehouse_company}'}

    except Exception as e:
        error_msg = f"Error in validate_warehouse_permission: {str(e)}"
        frappe.log_error(error_msg, "Warehouse Permissions API")
        return {'allowed': False, 'reason': f'Permission check failed: {str(e)}'}

@frappe.whitelist()
def get_user_permission_info():
    """
    Get detailed information about current user's permissions and roles.
    Useful for UI to show permission context.
    """
    try:
        current_user = frappe.session.user
        user_roles = frappe.get_roles(current_user)

        # Get user permissions
        try:
            user_permissions = frappe.get_list('User Permission',
                filters={'user': current_user},
                fields=['allow', 'for_value', 'is_default', 'applicable_for']
            )
        except:
            user_permissions = []

        # Get default company
        try:
            default_company = frappe.db.get_value('User', current_user, 'default_company')
        except:
            default_company = None

        # Get permitted companies count
        try:
            permitted_companies = get_permitted_companies()
            permitted_companies_list = [comp['name'] for comp in permitted_companies] if permitted_companies else []
            permitted_companies_count = len(permitted_companies) if permitted_companies else 0
        except:
            permitted_companies_list = []
            permitted_companies_count = 0

        permission_info = {
            'user': current_user,
            'roles': user_roles,
            'is_system_manager': 'System Manager' in user_roles or 'Administrator' in user_roles,
            'default_company': default_company,
            'user_permissions': user_permissions,
            'permitted_companies_count': permitted_companies_count,
            'permitted_companies': permitted_companies_list
        }

        return permission_info

    except Exception as e:
        error_msg = f"Error in get_user_permission_info: {str(e)}"
        frappe.log_error(error_msg, "Warehouse Permissions API")
        return {
            'user': 'Unknown User',
            'roles': [],
            'is_system_manager': False,
            'default_company': None,
            'user_permissions': [],
            'permitted_companies_count': 0,
            'permitted_companies': []
        }

@frappe.whitelist()
def validate_warehouse_dashboard_access():
    """
    Validate if current user can access the Warehouse Capacity Dashboard.
    Checks for warehouse module permissions and appropriate roles.
    """
    try:
        current_user = frappe.session.user
        user_roles = frappe.get_roles(current_user)

        # Check if user is System Manager or Administrator (always allowed)
        if 'System Manager' in user_roles or 'Administrator' in user_roles:
            return {
                'allowed': True,
                'reason': 'System Manager privileges',
                'access_level': 'full'
            }

        # Check if user has Stock User or Stock Manager role (required for warehouse access)
        warehouse_roles = ['Stock User', 'Stock Manager', 'Material Manager', 'Warehouse Manager']
        has_warehouse_role = any(role in user_roles for role in warehouse_roles)

        if not has_warehouse_role:
            return {
                'allowed': False,
                'reason': f'Missing required warehouse role. Required: {", ".join(warehouse_roles)}',
                'access_level': 'none'
            }

        # Check if user has any company permissions or default company
        permitted_companies = get_permitted_companies()
        if not permitted_companies:
            return {
                'allowed': False,
                'reason': 'No company permissions found. Please contact your administrator to set up company access.',
                'access_level': 'none'
            }

        # User has appropriate permissions
        return {
            'allowed': True,
            'reason': f'Warehouse role access with {len(permitted_companies)} company permissions',
            'access_level': 'limited',
            'permitted_companies_count': len(permitted_companies),
            'user_roles': user_roles
        }

    except Exception as e:
        error_msg = f"Error validating warehouse dashboard access: {str(e)}"
        frappe.log_error(error_msg, "Warehouse Dashboard Access Validation")
        return {
            'allowed': False,
            'reason': f'Permission validation failed: {str(e)}',
            'access_level': 'none'
        }

@frappe.whitelist()
def log_warehouse_activity(activity_type, warehouse_name, details=None):
    """
    Log warehouse builder activities for audit trail.
    """
    try:
        # Create activity log
        activity_log = frappe.get_doc({
            'doctype': 'Activity Log',
            'subject': f'Warehouse Builder: {activity_type}',
            'content': f'User {frappe.session.user} performed {activity_type} on warehouse {warehouse_name}. Details: {details or "None"}',
            'reference_doctype': 'Warehouse',
            'reference_name': warehouse_name,
            'user': frappe.session.user
        })
        activity_log.insert(ignore_permissions=True)

        # Also log to system log
        frappe.logger().info(f"Warehouse Activity: {frappe.session.user} - {activity_type} - {warehouse_name}")

        return True

    except Exception as e:
        # Don't fail the main operation if logging fails
        frappe.log_error(f"Error logging warehouse activity: {str(e)}", "Warehouse Activity Logging")
        return False