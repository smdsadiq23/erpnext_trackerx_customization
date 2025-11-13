// production_target_2.js - Simple Production Target Manager
frappe.pages['production_target_2'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Production Target Manager',
        single_column: true
    });

    // Add custom CSS
    //frappe.require('/assets/erpnext_trackerx_customization/css/production-target-manager.css');
    
    // Initialize the manager
    new SimpleProductionTargetManager(page);
};

class SimpleProductionTargetManager {
    constructor(page) {
        this.page = page;
        this.data = {
            physical_cells: [],
            styles: [],
            current_configs: [],
			sams: []
        };
        this.selectedCell = null;
        this.selectedStyle = null;
        this.pendingChanges = new Map();
        this.init();
    }

    init() {
        this.setupPage();
        this.bindEvents();
        this.loadInitialData();
    }

    setupPage() {
        const html = `
            <div class="simple-production-target-manager">
                <!-- Header -->
                <div class="page-header">
                    <div class="row">
                        <div class="col-8">
                            <h2>Production Target Manager</h2>
                            <p class="text-muted">Manage production targets by physical cell</p>
                        </div>
                        <div class="col-4 text-right">
                            <a href="/app/production-target-ma" class="btn btn-outline-secondary mr-2">
                                <i class="fa fa-table"></i> Bulk Manager
                            </a>
                            <button class="btn btn-primary" id="save-changes-btn" disabled>
                                <i class="fa fa-save"></i> Save Changes
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Physical Cell Selection -->
                <div class="cell-selection-card">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">
                                <i class="fa fa-cube text-primary"></i> Select Physical Cell and Style
                            </h5>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-6">
                                    <label class="form-label">Physical Cell</label>
                                    <select class="form-control" id="physical-cell-select">
                                        <option value="">Select Physical Cell...</option>
                                    </select>
                                </div>
                                <div class="col-6">
                                    <div class="cell-info" style="display: none;">
                                        <label class="form-label">Cell Information</label>
                                        <div class="info-display">
                                            <span class="badge badge-info" id="operator-count-badge"></span>
                                            <span class="badge badge-secondary" id="operation-group-badge"></span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
						<div class="card-body" id="style-card">
                            <div class="row">
                                <div class="col-6">
                                    <label class="form-label">Style</label>
                                    <select class="form-control" id="style-select">
                                        <option value="">Select Style...</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Bulk Update Controls -->
                <div class="bulk-controls-card" style="display: none;">
                    <div class="card">
                        <div class="card-header">
                            <h6 class="mb-0">
                                <i class="fa fa-flash text-warning"></i> Bulk Update All Styles
                            </h6>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-3">
                                    <label class="form-label">Bulk SAM</label>
                                    <div class="input-group input-group-sm">
                                        <input type="number" class="form-control" id="bulk-sam" step="0.01">
                                        <div class="input-group-append">
                                            <button class="btn btn-outline-secondary" id="calc-all-sam-btn" title="Calculate SAM for all">
                                                <i class="fa fa-calculator"></i>
                                            </button>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-3">
                                    <label class="form-label">Bulk Operator Count</label>
                                    <input type="number" class="form-control form-control-sm" id="bulk-operator" min="1">
                                </div>
                                <div class="col-3">
                                    <label class="form-label">Bulk Efficiency %</label>
                                    <input type="number" class="form-control form-control-sm" id="bulk-efficiency" min="0" max="100" step="0.01">
                                </div>
                                <div class="col-3">
                                    <label class="form-label">Bulk Target/Hr</label>
                                    <input type="number" class="form-control form-control-sm" id="bulk-target" min="0" step="0.01">
                                </div>
                            </div>
                            <div class="row mt-2">
                                <div class="col-12 text-right">
                                    <small class="text-muted">Changes will be applied to all visible styles</small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Loading Indicator -->
                <div class="loading-indicator text-center" style="display: none;">
                    <div class="spinner-border text-primary" role="status">
                        <span class="sr-only">Loading...</span>
                    </div>
                    <p class="mt-2 text-muted">Loading styles data...</p>
                </div>

                <!-- Styles Table -->
                <div class="styles-table-container" style="display: none;">
                    <div class="card">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <h5 class="mb-0">
                                <i class="fa fa-tags text-success"></i> 
                                <span id="selected-cell-name"></span> - <span id="selected-style-name"></span>
                            </h5>
                            <div>
                                <span class="badge badge-light" id="styles-count"></span>
                                <span class="badge badge-warning" id="pending-changes" style="display: none;"></span>
                            </div>
                        </div>
                        <div class="card-body p-0">
                            <div class="table-responsive">
                                <table class="table table-sm table-hover mb-0" id="styles-table">
                                    <thead class="thead-light">
                                        <tr>
                                            <th width="25%">Style Name</th>
                                            <th width="15%">SAM <i class="fa fa-info-circle" title="Standard Allowed Minutes"></i></th>
                                            <th width="15%">Operators</th>
                                            <th width="15%">Efficiency %</th>
                                            <th width="15%">Target/Hr</th>
                                            <th width="15%">History</th>
                                        </tr>
                                    </thead>
                                    <tbody id="styles-table-body">
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Status Bar -->
                <div class="status-bar mt-4">
                    <div class="row">
                        <div class="col-6">
                            <small class="text-muted" id="last-updated"></small>
                        </div>
                        <div class="col-6 text-right">
                            <small class="text-muted" id="total-configurations"></small>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Confirmation Modal -->
            <div class="modal fade" id="confirmModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Confirm Changes</h5>
                            <button type="button" class="close" data-dismiss="modal">
                                <span>&times;</span>
                            </button>
                        </div>
                        <div class="modal-body">
                            <p id="confirm-message"></p>
                            <div id="changes-preview"></div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="confirm-save">Save Changes</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        $(this.page.body).html(html);
    }

    bindEvents() {
        const self = this;

        // Physical Cell selection change
        $(this.page.body).on('change', '#physical-cell-select', function() {
            const cellName = $(this).val();
            if (cellName) {
                self.onCellSelected(cellName);
            } else {
                self.hideStylesTable();
            }
        });

		// style selection change
		$(this.page.body).on('change', '#style-select', function() {
            const styleName = $(this).val();
            if (styleName) {
                self.onStyleSelected(styleName);
            } else {
                self.hideStylesTable();
            }
        });

        // Bulk update inputs
        $(this.page.body).on('input', '#bulk-sam, #bulk-operator, #bulk-efficiency, #bulk-target', function() {
            self.handleBulkUpdate($(this).attr('id'));
        });

        // Calculate all SAM button
        $(this.page.body).on('click', '#calc-all-sam-btn', function() {
            self.calculateAllSAM();
        });

        // Save changes button
        $(this.page.body).on('click', '#save-changes-btn', function() {
            self.showSaveConfirmation();
        });

        // Confirm save
        $(this.page.body).on('click', '#confirm-save', function() {
            self.saveAllChanges();
        });

        // Individual row events - using delegation
        $(this.page.body).on('input', '.sam-input, .operator-input, .efficiency-input, .target-input', function() {
            self.handleIndividualUpdate($(this));
        });

        $(this.page.body).on('click', '.calc-sam-btn', function() {
            const styleCode = $(this).data('style');
            self.calculateSAM(styleCode, $(this));
        });

        $(this.page.body).on('click', '.history-btn', function() {
            const styleCode = $(this).data('style');
            self.showStyleHistory(styleCode);
        });
    }

    async loadInitialData() {
        try {
            const response = await frappe.call({
                method: 'erpnext_trackerx_customization.erpnext_trackerx_customization.api.production_target_configuration_manager.get_production_data'
            });

            this.data.physical_cells = response.message.physical_cells;
            this.data.styles = response.message.styles;
			this.data.sams = response.message.sams;

            this.populatePhysicalCellDropdown();
            this.updateLastUpdated();

        } catch (error) {
            console.error('Error loading initial data:', error);
            frappe.msgprint({
                title: 'Error',
                message: 'Failed to load initial data. Please refresh the page.',
                indicator: 'red'
            });
        }
    }

    populatePhysicalCellDropdown() {
        const select = $(this.page.body).find('#physical-cell-select');
        select.empty().append('<option value="">Select Physical Cell...</option>');

        this.data.physical_cells.forEach(cell => {
            select.append(`<option value="${cell.name}">${cell.name}</option>`);
        });
    }

	  populatedStyleDropdown() {
        const select = $(this.page.body).find('#style-select');
        select.empty().append('<option value="">Select Style...</option>');

        this.data.styles.forEach(style => {
            select.append(`<option value="${style.name}">${style.name}</option>`);
        });
    }

	showStyleDropDown() {
		(this.page.body).find('#style-card').show();

	}

    async onCellSelected(cellName) {

		this.showStyleDropDown();

		this.populatedStyleDropdown();

        this.selectedCell = this.data.physical_cells.find(c => c.name === cellName);
        if (!this.selectedCell) return;

        // Update cell info display
        $(this.page.body).find('#operator-count-badge').text(`${this.selectedCell.operator_count || 0} Operators`);
        $(this.page.body).find('#operation-group-badge').text(`Group: ${this.selectedCell.supported_operation_group || 'None'}`);
        $(this.page.body).find('.cell-info').show();

        // Load current configurations for this cell
        //await this.loadCellConfigurations();
        
        // Show bulk controls and table
        //$(this.page.body).find('.bulk-controls-card').show();
        //this.showStylesTable();
    }

	 async onStyleSelected(styleName) {


        this.selectedStyle = this.data.styles.find(s => s.name === styleName);
        if (!this.selectedStyle) return;

        // Load current configurations for this cell
        await this.loadCellConfigurations();
        
        // Show bulk controls and table
        //$(this.page.body).find('.bulk-controls-card').show();
        this.showStylesTable();
    }



    async loadCellConfigurations() {
        this.showLoading(true);
        
        try {
            // Get existing configs for this cell
            const response = await frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'Production Target Configuration',
                    filters: {
                        physical_cell: this.selectedCell.name,
						style: this.selectedStyle.name,
                        is_active: 1
                    },
                    fields: ['style', 'sam', 'operator', 'efficiency', 'hour_target']
                }
            });

            this.data.current_configs = response.message || [];
            this.populateStylesTable();

        } catch (error) {
            console.error('Error loading cell configurations:', error);
            frappe.msgprint('Error loading configurations for this cell');
        } finally {
            this.showLoading(false);
        }
    }

    populateStylesTable() {
        const tbody = $(this.page.body).find('#styles-table-body');
        tbody.empty();

        this.data.styles.forEach(style => {
			if(style != this.selectedStyle)
			{
				return;
			}

			
            const existingConfig = this.data.current_configs.find(c => c.style === style.name);
            const sam = existingConfig ? existingConfig.sam : (this.data.sams[this.selectedCell.name+"###"+this.selectedStyle.name] || 0);
            const operator = existingConfig ? existingConfig.operator : (this.selectedCell.operator_count || 0);
            const efficiency = existingConfig ? existingConfig.efficiency : 0;
            const target = existingConfig ? existingConfig.hour_target : 0;
            const hasConfig = !!existingConfig;
			

            const row = `
                <tr data-style="${style.name}" class="${hasConfig ? 'table-light' : ''}">
                    <td>
                        <div class="style-info">
                            <strong>${style.item_name || style.name}</strong>
                            <br><small class="text-muted">${style.name}</small>
                            ${hasConfig ? '<span class="badge badge-success badge-sm ml-2">Configured</span>' : '<span class="badge badge-secondary badge-sm ml-2">New</span>'}
                        </div>
                    </td>
                    <td>
                        <div class="input-group input-group-sm">
                            <input type="number" class="form-control sam-input" value="${sam || ''}" step="1" min="0">
                            <div class="input-group-append">
                                <button class="btn btn-outline-secondary calc-sam-btn" data-style="${style.name}" title="Calculate SAM">
                                    <i class="fa fa-calculator"></i>
                                </button>
                            </div>
                        </div>
                    </td>
                    <td>
                        <input type="number" class="form-control form-control-sm operator-input" value="${operator || ''}" min="1">
                    </td>
                    <td>
                        <input type="number" class="form-control form-control-sm efficiency-input" value="${efficiency || ''}" min="0" max="100" step="0.01">
                    </td>
                    <td>
                        <input type="number" class="form-control form-control-sm target-input" value="${target || ''}" min="0" step="0.01">
                    </td>
                    <td>
                        <button class="btn btn-sm btn-info history-btn" data-style="${style.name}" title="View History">
                            <i class="fa fa-history"></i>
                        </button>
                    </td>
                </tr>
            `;
            tbody.append(row);
        });

        // Update counters
        $(this.page.body).find('#selected-cell-name').text(this.selectedCell.name);
        $(this.page.body).find('#selected-style-name').text(this.selectedStyle.name);
        //$(this.page.body).find('#styles-count').text(`${this.data.styles.length} Styles`);
        
        this.clearPendingChanges();
    }

    handleBulkUpdate(fieldId) {
        const value = parseFloat($(this.page.body).find(`#${fieldId}`).val());
        if (isNaN(value)) return;

        const field = fieldId.replace('bulk-', '');
        
        $(this.page.body).find('#styles-table-body tr').each((index, row) => {
            const $row = $(row);
            
            switch(field) {
                case 'sam':
                    $row.find('.sam-input').val(value).trigger('input');
                    break;
                case 'operator':
                    $row.find('.operator-input').val(value).trigger('input');
                    break;
                case 'efficiency':
                    $row.find('.efficiency-input').val(value).trigger('input');
                    break;
                case 'target':
                    $row.find('.target-input').val(value).trigger('input');
                    break;
            }
        });
    }

    handleIndividualUpdate($input) {
        const $row = $input.closest('tr');
        const styleCode = $row.data('style');
        
        // Auto-calculate target/efficiency based on input
        if ($input.hasClass('efficiency-input')) {
            const efficiency = parseFloat($input.val()) || 0;
            const sam = parseFloat($row.find('.sam-input').val()) || 0;
            const operator = parseFloat($row.find('.operator-input').val()) || 1;
            
            if (sam > 0) {
                const target = Math.round((efficiency/100 * 60 * operator) / sam * 100) / 100;
                $row.find('.target-input').val(target);
            }
        } else if ($input.hasClass('target-input')) {
            const target = parseFloat($input.val()) || 0;
            const sam = parseFloat($row.find('.sam-input').val()) || 0;
            const operator = parseFloat($row.find('.operator-input').val()) || 1;
            
            if (sam > 0 && operator > 0) {
                const efficiency = Math.round((target * sam) / (60 * operator) * 10000) / 100;
                $row.find('.efficiency-input').val(efficiency);
            }
        }

        // Mark as changed
        this.markRowChanged($row, styleCode);
    }

    markRowChanged($row, styleCode) {
        $row.addClass('table-warning');
        
        const changeData = {
            physical_cell: this.selectedCell.name,
            style: styleCode,
            sam: parseFloat($row.find('.sam-input').val()) || 0,
            operator: parseFloat($row.find('.operator-input').val()) || 0,
            efficiency: parseFloat($row.find('.efficiency-input').val()) || 0,
            hour_target: parseFloat($row.find('.target-input').val()) || 0
        };

        this.pendingChanges.set(styleCode, changeData);
        this.updateSaveButtonState();
    }

    async calculateSAM(styleCode, $button) {
        const originalHTML = $button.html();
        $button.html('<i class="fa fa-spinner fa-spin"></i>').prop('disabled', true);

        try {
            const response = await frappe.call({
                method: 'erpnext_trackerx_customization.erpnext_trackerx_customization.api.production_target_configuration_manager.calculate_sam',
                args: {
                    physical_cell: this.selectedCell.name,
                    style: styleCode
                }
            });

            const sam = response.message;
            const $row = $button.closest('tr');
            $row.find('.sam-input').val(sam).trigger('input');

        } catch (error) {
            console.error('Error calculating SAM:', error);
            frappe.msgprint('Error calculating SAM');
        } finally {
            $button.html(originalHTML).prop('disabled', false);
        }
    }

    async calculateAllSAM() {
        const $button = $(this.page.body).find('#calc-all-sam-btn');
        $button.prop('disabled', true).html('<i class="fa fa-spinner fa-spin"></i>');

        let completed = 0;
        const total = this.data.styles.length;

        try {
            for (const style of this.data.styles) {
                const response = await frappe.call({
                    method: 'erpnext_trackerx_customization.erpnext_trackerx_customization.api.production_target_configuration_manager.calculate_sam',
                    args: {
                        physical_cell: this.selectedCell.name,
                        style: style.name
                    }
                });

                const sam = response.message;
                $(this.page.body).find(`tr[data-style="${style.name}"] .sam-input`).val(sam).trigger('input');
                
                completed++;
                $button.html(`<i class="fa fa-spinner fa-spin"></i> ${completed}/${total}`);
            }

            frappe.msgprint({
                title: 'Success',
                message: `SAM calculated for all ${total} styles`,
                indicator: 'green'
            });

        } catch (error) {
            console.error('Error calculating SAM for all:', error);
            frappe.msgprint('Error calculating SAM for all styles');
        } finally {
            $button.prop('disabled', false).html('<i class="fa fa-calculator"></i>');
        }
    }

    showSaveConfirmation() {
        if (this.pendingChanges.size === 0) return;

        const changesArray = Array.from(this.pendingChanges.values());
        let previewHTML = '<ul class="list-unstyled">';
        
        changesArray.forEach(change => {
            const style = this.data.styles.find(s => s.name === change.style);
            previewHTML += `<li><strong>${style.item_name || style.name}</strong>: SAM=${change.sam}, Efficiency=${change.efficiency}%, Target=${change.hour_target}/hr</li>`;
        });
        previewHTML += '</ul>';

        $(this.page.body).find('#confirm-message').text(`You are about to save ${changesArray.length} configuration changes. This will create new versions for modified combinations.`);
        $(this.page.body).find('#changes-preview').html(previewHTML);
        $('#confirmModal').modal('show');
    }

    async saveAllChanges() {
        $('#confirmModal').modal('hide');
        
        if (this.pendingChanges.size === 0) return;

        this.showLoading(true, 'Saving changes...');
        
        try {
            const changes = Array.from(this.pendingChanges.values());
            const response = await frappe.call({
                method: 'erpnext_trackerx_customization.erpnext_trackerx_customization.api.production_target_configuration_manager.bulk_update_configurations',
                args: {
                    configurations: changes
                }
            });

            if (response.message.status === 'success') {
                frappe.msgprint({
                    title: 'Success',
                    message: response.message.message,
                    indicator: 'green'
                });

                this.clearPendingChanges();
                await this.loadCellConfigurations(); // Refresh data
            }

        } catch (error) {
            console.error('Error saving changes:', error);
            frappe.msgprint({
                title: 'Error',
                message: 'Failed to save changes. Please try again.',
                indicator: 'red'
            });
        } finally {
            this.showLoading(false);
        }
    }

    async showStyleHistory(styleCode) {
        try {
            const response = await frappe.call({
                method: 'erpnext_trackerx_customization.erpnext_trackerx_customization.api.production_target_configuration_manager.get_configuration_history',
                args: {
                    physical_cell: this.selectedCell.name,
                    style: styleCode
                }
            });

            const history = response.message;
            // Reuse the history modal from the main page
            this.displayHistoryModal(this.selectedCell.name, styleCode, history);

        } catch (error) {
            console.error('Error fetching history:', error);
            frappe.msgprint('Error fetching configuration history');
        }
    }

    displayHistoryModal(physicalCell, style, history) {
        const styleName = this.data.styles.find(s => s.name === style)?.item_name || style;
        
        let historyHTML = `
            <div class="modal fade" id="historyModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Configuration History</h5>
                            <button type="button" class="close" data-dismiss="modal"><span>&times;</span></button>
                        </div>
                        <div class="modal-body">
                            <h6>${physicalCell} - ${styleName}</h6>
                            <table class="table table-sm">
                                <thead>
                                    <tr><th>Version</th><th>SAM</th><th>Efficiency</th><th>Target/Hr</th><th>Start</th><th>End</th><th>Status</th></tr>
                                </thead>
                                <tbody>`;

        history.forEach((record, index) => {
            const statusBadge = record.is_active ? 
                '<span class="badge badge-success">Active</span>' : 
                '<span class="badge badge-secondary">Historical</span>';
            
            historyHTML += `
                <tr>
                    <td>V${history.length - index}</td>
                    <td>${record.sam || 0}</td>
                    <td>${record.efficiency || 0}%</td>
                    <td>${record.hour_target || 0}</td>
                    <td>${frappe.datetime.str_to_user(record.start) || '-'}</td>
                    <td>${record.end ? frappe.datetime.str_to_user(record.end) : 'Current'}</td>
                    <td>${statusBadge}</td>
                </tr>`;
        });

        historyHTML += `</tbody></table></div><div class="modal-footer"><button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button></div></div></div></div>`;

        $('#historyModal').remove();
        $('body').append(historyHTML);
        $('#historyModal').modal('show');
    }

    clearPendingChanges() {
        this.pendingChanges.clear();
        $(this.page.body).find('#styles-table-body tr').removeClass('table-warning');
        this.updateSaveButtonState();
    }

    updateSaveButtonState() {
        const $btn = $(this.page.body).find('#save-changes-btn');
        const hasChanges = this.pendingChanges.size > 0;
        
        $btn.prop('disabled', !hasChanges);
        
        if (hasChanges) {
            //$btn.html(`<i class="fa fa-save"></i> Save ${this.pendingChanges.size} Changes`);
            //$(this.page.body).find('#pending-changes').text(`${this.pendingChanges.size} pending`).show();
        } else {
            $btn.html(`<i class="fa fa-save"></i> Save Changes`);
            $(this.page.body).find('#pending-changes').hide();
        }
    }

    showStylesTable() {
        $(this.page.body).find('.styles-table-container').show();
    }

    hideStylesTable() {
        $(this.page.body).find('.styles-table-container, .bulk-controls-card, .cell-info').hide();
        this.clearPendingChanges();
    }

    showLoading(show, message = 'Loading...') {
        const $loading = $(this.page.body).find('.loading-indicator');
        if (show) {
            $loading.find('p').text(message);
            $loading.show();
        } else {
            $loading.hide();
        }
    }

    updateLastUpdated() {
        $(this.page.body).find('#last-updated').text(`Last updated: ${new Date().toLocaleTimeString()}`);
    }
}