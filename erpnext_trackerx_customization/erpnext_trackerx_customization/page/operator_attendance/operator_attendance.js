// Fix 1: Make sure the page name matches your actual page name
frappe.pages['operator_attendance'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Operator Attendance',
        single_column: true
    });

    // Initialize the page
    new OperatorAttendanceGrid(page);
};

class OperatorAttendanceGrid {
    constructor(page) {
        this.page = page;
        this.currentData = {};
        this.changedCells = new Set();
        this.physicalCells = [];
        
        this.make();
        this.setupEvents();
        this.loadData();
    }

    make() {
        // Create a better styled field area in the page
        let field_area = $(`
            <div class="page-form">
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">Select Date</label>
                        <input type="date" class="form-control date-input" id="selected_date" value="${frappe.datetime.get_today()}" />
                    </div>
                    <div class="form-actions">
                        <button class="btn btn-primary" id="load_data_btn">
                            <i class="fa fa-refresh"></i> Load Data
                        </button>
                        <button class="btn btn-success" id="save_changes_btn">
                            <i class="fa fa-save"></i> Save Changes
                        </button>
                    </div>
                </div>
            </div>
        `);
        
        this.page.main.append(field_area);

        // Create main container
        this.page.main.append(`
            <div class="operator-attendance-container">
                <div class="grid-wrapper">
                    <div class="loading-indicator" style="text-align: center; padding: 40px; display: none;">
                        <i class="fa fa-spinner fa-spin"></i> Loading attendance data...
                    </div>
                    <div class="grid-container">
                        <table class="table table-bordered attendance-grid" style="display: none;">
                            <!-- Dynamic content will be inserted here -->
                        </table>
                    </div>
                </div>
            </div>
        `);
    }

    setupEvents() {
        // Setup global change handler
        this.page.main.on('input', '.attendance-input', (e) => {
            this.handleInputChange(e.target);
        });
        
        // Setup button events
        this.page.main.on('click', '#load_data_btn', () => this.loadData());
        this.page.main.on('click', '#save_changes_btn', () => this.saveChanges());
        this.page.main.on('change', '#selected_date', () => this.loadData());
    }

    generateHourColumns(cells) {
        const hours = new Set();
        
        cells.forEach(cell => {
            const startHour = parseInt(cell.start_time.split(':')[0]);
            const endHour = parseInt(cell.end_time.split(':')[0]);
            
            for (let h = startHour; h < endHour; h++) {
                hours.add(h);
            }
        });
        
        return Array.from(hours).sort((a, b) => a - b);
    }

    formatHour(hour) {
        return `${hour.toString().padStart(2, '0')}:00`;
    }

    getHourRange(hour) {
        const nextHour = (hour + 1) % 24;
        return `${this.formatHour(hour)} - ${this.formatHour(nextHour)}`;
    }

    createGrid(cells, hours, selectedDate) {
        const grid = this.page.main.find('.attendance-grid');
        let html = '<thead><tr><th class="cell-header">Physical Cell</th>';
        
        // Create hour headers
        hours.forEach(hour => {
            html += `<th class="hour-header">${this.getHourRange(hour)}</th>`;
        });
        html += '</tr></thead><tbody>';
        const now = new Date();

        // Create rows for each cell
        cells.forEach((cell, cellIndex) => {
            html += `<tr data-cell="${cell.name}"><td class="cell-name">${cell.cell_name}</td>`;
            hours.forEach((hour, hourIndex) => {
                let is_editable = true;
                let cellDate = new Date(selectedDate);
                cellDate = new Date(cellDate.setHours(hour-1));
            
                console.log("cellDate: ", cellDate, " now: ", now)

                if(cellDate < now)
                {
                    is_editable = false;
                }
                const cellStartHour = parseInt(cell.start_time.split(':')[0]);
                const cellEndHour = parseInt(cell.end_time.split(':')[0]);
                
                if (hour >= cellStartHour && hour < cellEndHour) {
                    const key = `${cell.name}-${selectedDate}-${hour}`;
                    const value = this.currentData[key] || 0;
                    const isFirstCell = (hour === cellStartHour);
                    
                    html += `<td>
                        <input type="number" 
							   class="form-control attendance-input ${isFirstCell ? 'first-cell' : ''}" 
                               data-cell="${cell.name}" 
                               data-hour="${hour}" 
                               data-is-first="${isFirstCell}"
                               data-row-index="${cellIndex}"
                               data-col-index="${hourIndex}"
                               value="${value}" 
                               min="0" ${is_editable ? '' : 'disabled'}/>
                    </td>`;
                } else {
                    html += '<td class="disabled-cell">-</td>';
                }
            });
            html += '</tr>';
        });
        
        html += '</tbody>';
        grid.html(html);
        grid.show();
    }

    handleInputChange(input) {
        const cell = input.dataset.cell;
        const hour = input.dataset.hour;
        const isFirstCell = input.dataset.isFirst === 'true';
        const selectedDate = this.getSelectedDate();
        const key = `${cell}###${selectedDate}###${hour}`;
        const newValue = parseInt(input.value) || 0;
        const oldValue = this.currentData[key] || 0;
        
        // Update the current data
        this.currentData[key] = newValue;
        this.changedCells.add(key);
        
        // Visual feedback for changed cells
        $(input).addClass('changed-input');
        
        // Enhancement 1: Auto-update other cells in the same row if this is the first cell
        // if (isFirstCell && oldValue !== newValue) {
		if (oldValue !== newValue) {
            this.autoUpdateRowCells(cell, selectedDate, oldValue, newValue, input);
        }
        
        // Update page title to show unsaved changes
        this.updatePageTitle();
    }

    autoUpdateRowCells(cellName, selectedDate, oldValue, newValue, inputCell) {
        // Find all inputs in the same row (same cell name)
        const rowInputs = this.page.main.find(`input[data-cell="${cellName}"]`);

        const changedHour = inputCell.dataset.hour;
        rowInputs.each((index, element) => {
            const $input = $(element);
            const isFirst = $input.data('is-first');
            
            // Skip the first cell (the one that was just changed)
            if (isFirst) return;

            const hour = $input.data('hour');
			if(hour < changedHour){
				return;
			}
            const key = `${cellName}###${selectedDate}###${hour}`;
            const currentValue = this.currentData[key] || 0;
            
            // Only update if the current value matches the old value from first cell

            // if (currentValue === oldValue) {
			if(true) {
                // Update the value
                this.currentData[key] = newValue;
                $input.val(newValue);
                
                // Add to changed cells
                this.changedCells.add(key);
                
                // Add visual feedback
                $input.addClass('changed-input');
            }
        });
        
        // Show notification about auto-update
        if (oldValue !== newValue) {
            frappe.show_alert({
                message: __(`Auto-updated other cells in ${cellName} row from ${oldValue} to ${newValue}`),
                indicator: 'blue'
            }, 3);
        }
    }

    // Helper method to get selected date consistently
    getSelectedDate() {
        return this.page.main.find('#selected_date').val() || frappe.datetime.get_today();
    }

    updatePageTitle() {
        const title = this.changedCells.size > 0 
            ? `Operator Attendance (${this.changedCells.size} changes)` 
            : 'Operator Attendance';
        this.page.set_title(title);
    }

    async loadData() {
        const selectedDate = this.getSelectedDate();
        if (!selectedDate) {
            frappe.msgprint(__('Please select a date'));
            return;
        }
        
        this.page.main.find('.loading-indicator').show();
        this.page.main.find('.attendance-grid').hide();
        
        try {
            const response = await frappe.call({
                method: 'erpnext_trackerx_customization.erpnext_trackerx_customization.api.operator_attendance.get_operator_attendance_grid',
                args: { date: selectedDate }
            });
            
            if (response.message.success) {
                this.physicalCells = response.message.physical_cells;
                this.currentData = response.message.attendance_data;
                
                const hours = this.generateHourColumns(this.physicalCells);
                this.createGrid(this.physicalCells, hours, selectedDate);
                
                // Clear changed indicators
                this.changedCells.clear();
                this.updatePageTitle();
                
                frappe.show_alert({
                    message: __('Data loaded successfully'),
                    indicator: 'green'
                }, 2);
            } else {
                frappe.msgprint({
                    title: __('Error'),
                    message: response.message.message,
                    indicator: 'red'
                });
            }
            
        } catch (error) {
            frappe.msgprint({
                title: __('Error'),
                message: __('Error loading data: ') + error.message,
                indicator: 'red'
            });
        } finally {
            this.page.main.find('.loading-indicator').hide();
        }
    }

    async saveChanges() {
        if (this.changedCells.size === 0) {
            frappe.msgprint(__('No changes to save'));
            return;
        }
        
        // Disable save button during save
        const saveBtn = this.page.main.find('#save_changes_btn');
        const originalText = saveBtn.html();
        saveBtn.prop('disabled', true).html('<i class="fa fa-spinner fa-spin"></i> Saving...');
        
        const selectedDate = this.getSelectedDate();
        const changes = [];
        
        this.changedCells.forEach(key => {
            const [cell, date, hour] = key.split('###');
            const formattedHour = `${date} ${hour.padStart(2, '0')}:00:00`;
            changes.push({
                physical_cell: cell,
                hour: formattedHour,
                value: this.currentData[key]
            });
        });
        
        console.log('Saving changes:', changes);
        
        try {
            const response = await frappe.call({
                method: 'erpnext_trackerx_customization.erpnext_trackerx_customization.api.operator_attendance.save_operator_attendance_bulk',
                args: { records: changes }
            });
            
            if (response.message.success) {
                // Clear changed indicators
                this.page.main.find('.attendance-input.changed-input').removeClass('changed-input');
                this.changedCells.clear();
                this.updatePageTitle();
                
                frappe.show_alert({
                    message: __(`Successfully saved ${changes.length} records!`),
                    indicator: 'green'
                });
            } else {
                frappe.msgprint({
                    title: __('Error'),
                    message: response.message.message,
                    indicator: 'red'
                });
            }
            
        } catch (error) {
            frappe.msgprint({
                title: __('Error'),
                message: __('Error saving changes: ') + error.message,
                indicator: 'red'
            });
        } finally {
            // Re-enable save button
            saveBtn.prop('disabled', false).html(originalText);
        }
    }
}