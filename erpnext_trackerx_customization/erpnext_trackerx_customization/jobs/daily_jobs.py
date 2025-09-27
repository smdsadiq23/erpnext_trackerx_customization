import frappe
from frappe.utils import nowdate, add_days, get_datetime, get_time

def copy_operator_attendance_for_next_day():
    """
    Runs daily at 11:30 PM. For each physical cell with attendance records today,
    it copies those records to tomorrow if no records exist for tomorrow yet.
    """

    today_date_str = nowdate()
    tomorrow_date_str = add_days(today_date_str, 1)

    # Build datetime ranges for today and tomorrow
    start_of_today = get_datetime(f"{today_date_str} 00:00:00")
    end_of_today = get_datetime(f"{today_date_str} 23:59:59")

    start_of_tomorrow = get_datetime(f"{tomorrow_date_str} 00:00:00")
    end_of_tomorrow = get_datetime(f"{tomorrow_date_str} 23:59:59")

    frappe.logger().info(f"Running attendance copy job for tomorrow ({tomorrow_date_str}).")

    # 1. Get all distinct cells with attendance today
    distinct_cells = frappe.db.sql_list("""
        SELECT DISTINCT physical_cell
        FROM `tabOperator Attendance`
        WHERE hour BETWEEN %s AND %s
    """, (start_of_today, end_of_today))

    if not distinct_cells:
        frappe.logger().info("No Operator Attendance records found for today.")
        return

    for cell in distinct_cells:
        # 2. Skip if tomorrow's records already exist for this cell
        tomorrow_exists = frappe.db.exists(
            "Operator Attendance",
            {"physical_cell": cell, "hour": ["between", [start_of_tomorrow, end_of_tomorrow]]}
        )

        if tomorrow_exists:
            frappe.logger().info(f"Skipping Cell {cell}: Records already exist for tomorrow.")
            continue

        # 3. Fetch today's records
        today_records = frappe.db.get_all(
            "Operator Attendance",
            filters={
                "physical_cell": cell,
                "hour": ["between", [start_of_today, end_of_today]]
            },
            fields=["hour", "value"]
        )

        for record in today_records:
            try:
                # Extract only the time from today's record
                time_part = get_time(record.hour)

                # Build tomorrow's datetime
                tomorrow_hour_dt = get_datetime(f"{tomorrow_date_str} {str(time_part)}")

                # Create new doc
                new_doc = frappe.new_doc("Operator Attendance")
                new_doc.physical_cell = cell
                new_doc.hour = tomorrow_hour_dt
                new_doc.value = record.value
                new_doc.insert(ignore_permissions=True, ignore_mandatory=True)

            except Exception as e:
                frappe.log_error(
                    title="Attendance Copy Error",
                    message=f"Failed for Cell {cell} at {record.hour}. Error: {e}"
                )

        frappe.logger().info(
            f"Copied {len(today_records)} records for Cell {cell} "
            f"from {today_date_str} to {tomorrow_date_str}."
        )

    # ✅ Commit once after all inserts
    frappe.db.commit()
