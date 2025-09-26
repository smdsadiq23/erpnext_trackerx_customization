// production-target-manager.js - Frappe Page Implementation
frappe.pages['production-target-ma'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Production Target Manager',
        single_column: true
    });

    // Add custom CSS
    //frappe.require('/assets/erpnext_trackerx_customization/css/production-target-manager.css');
    
    // Initialize the manager
    new ProductionTargetManager(page);
};

class ProductionTargetManager {
    constructor(page) {
        this.page = page;
        this.data = {
            physical_cells: [],
            styles: [],
            existing_configs: [],
            combinations: []
        };
        this.currentView = 'style';
        this.pendingChanges = new Map();
        this.init();
    }

    init() {
        this.setupPage();
        this.bindEvents();
        this.loadData();
    }

    setupPage() {
        const html = `
            <div class="production-target-manager">
                <div class="page-header">
                    <div class="row">
                        <div class="col-8">
                            <h2>Production Target Manager</h2>
                            <p class="text-muted">Configure production targets by physical cell and style combinations</p>
                        </div>
                        <div class="col-4 text-right">
                            <button class="btn btn-primary" id="save-all-btn">
                                <i class="fa fa-save"></i> Save All Changes
                            </button>
                        </div>
                    </div>
                </div>

                <div class="view-controls mb-4">
                    <div class="btn-group" role="group">
                        <button type="button" class="btn btn-outline-primary active" data-view="style">
                            <i class="fa fa-tags"></i> View by Style
                        </button>
                        <button type="button" class="btn btn-outline-primary" data-view="cell">
                            <i class="fa fa-cube"></i> View by Physical Cell
                        </button>
                    </div>
                    <button class="btn btn-success ml-3" id="refresh-btn">
                        <i class="fa fa-refresh"></i> Refresh Data
                    </button>
                </div>

                <div class="loading-indicator text-center" style="display: none;">
                    <div class="spinner-border" role="status">
                        <span class="sr-only">Loading...</span>
                    </div>
                    <p class="mt-2">Loading data...</p>
                </div>

                <div class="tree-container">
                    <div id="tree-view"></div>
                </div>

                <div class="status-bar mt-4">
                    <div class="row">
                        <div class="col-6">
                            <small class="text-muted" id="last-updated"></small>
                        </div>
                        <div class="col-6 text-right">
                            <small class="text-muted" id="total-combinations"></small>
                        </div>
                    </div>
                </div>
            </div>

            <div class="modal fade" id="confirmModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Confirm Action</h5>
                            <button type="button" class="close" data-dismiss="modal">
                                <span>&times;</span>
                            </button>
                        </div>
                        <div class="modal-body">
                            <p id="confirm-message"></p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="confirm-action">Confirm</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        $(this.page.body).html(html);
    }

    bindEvents() {
        const self = this;
        
        $(this.page.body).on('click', '[data-view]', function(e) {
            $(self.page.body).find('[data-view]').removeClass('active');
            $(this).addClass('active');
            self.currentView = $(this).data('view');
            self.renderTreeView();
        });

        $(this.page.body).on('click', '#save-all-btn', function() {
            self.saveAllChanges();
        });

        $(this.page.body).on('click', '#refresh-btn', function() {
            self.loadData();
        });

        $(this.page.body).on('click', '#confirm-action', function() {
            if (self.pendingConfirmAction) {
                self.pendingConfirmAction();
                $('#confirmModal').modal('hide');
            }
        });
    }

    async loadData() {
        this.showLoading(true);
        try {
            const response = await frappe.call({
                method: 'erpnext_trackerx_customization.erpnext_trackerx_customization.api.production_target_configuration_manager.get_production_data'
            });

            this.data = response.message;

			//this.data.sams.get(cell.name+"###".style.name) ||
			console.log()
            this.generateCombinations();
            this.renderTreeView();
            this.updateStatus();
        } catch (error) {
            console.error('Error loading data:', error);
            frappe.msgprint('Error loading data. Please try again.');
        } finally {
            this.showLoading(false);
        }
    }

    generateCombinations() {
        const combinations = [];
        
        this.data.physical_cells.forEach(cell => {
            this.data.styles.forEach(style => {
                const existing = this.data.existing_configs.find(config => 
                    config.physical_cell === cell.name && config.style === style.name
                );
                
                const combination = {
                    physical_cell: cell.name,
                    style: style.name,
                    style_name: style.item_name || style.name,
                    operator: cell.operator_count || 0,
                    sam: existing ? existing.sam : ( this.data.sams[cell.name+"###"+style.name] || 0),
                    efficiency: existing ? existing.efficiency : 0,
                    hour_target: existing ? existing.hour_target : 0,
                    is_existing: !!existing,
                    config_name: existing ? existing.name : null,
                    has_changes: false
                };

                combinations.push(combination);
            });
        });

        this.data.combinations = combinations;
    }

    renderTreeView() {
        const container = $(this.page.body).find('#tree-view')[0];
        container.innerHTML = '';

        if (this.currentView === 'style') {
            this.renderStyleView(container);
        } else {
            this.renderCellView(container);
        }
    }

    renderStyleView(container) {
        const styleGroups = this.groupBy(this.data.combinations, 'style');
        
        Object.keys(styleGroups).forEach(styleName => {
            const combinations = styleGroups[styleName];
            const styleItem = this.data.styles.find(s => s.name === styleName);
            
            if (styleItem) {
                const styleGroup = this.createStyleGroup(styleItem, combinations);
                container.appendChild(styleGroup);
            }
        });
    }

    renderCellView(container) {
        const cellGroups = this.groupBy(this.data.combinations, 'physical_cell');
        
        Object.keys(cellGroups).forEach(cellName => {
            const combinations = cellGroups[cellName];
            const cellItem = this.data.physical_cells.find(c => c.name === cellName);
            
            if (cellItem) {
                const cellGroup = this.createCellGroup(cellItem, combinations);
                container.appendChild(cellGroup);
            }
        });
    }

    createStyleGroup(styleItem, combinations) {
        const groupDiv = document.createElement('div');
        groupDiv.className = 'tree-group mb-4';
        
        groupDiv.innerHTML = `
            <div class="tree-group-header">
                <div class="row">
                    <div class="col-6">
                        <h5 class="mb-0">
                            <i class="fa fa-tags text-primary"></i>
                            ${styleItem.item_name || styleItem.name}
                            <small class="text-muted">(${styleItem.name})</small>
                        </h5>
                    </div>
                    <div class="col-3">
                        <label class="form-label">Bulk Efficiency %</label>
                        <input type="number" class="form-control form-control-sm bulk-efficiency" 
                               data-group="${styleItem.name}" placeholder="Enter efficiency">
                    </div>
                    <div class="col-3">
                        <label class="form-label">Bulk Target/Hr</label>
                        <input type="number" class="form-control form-control-sm bulk-target" 
                               data-group="${styleItem.name}" placeholder="Enter target">
                    </div>
                </div>
            </div>
            <div class="tree-group-content">
                ${this.createCombinationTable(combinations, 'cell')}
            </div>
        `;

        this.bindBulkUpdateEvents(groupDiv, styleItem.name, combinations);
        return groupDiv;
    }

    createCellGroup(cellItem, combinations) {
        const groupDiv = document.createElement('div');
        groupDiv.className = 'tree-group mb-4';
        
        groupDiv.innerHTML = `
            <div class="tree-group-header">
                <div class="row">
                    <div class="col-6">
                        <h5 class="mb-0">
                            <i class="fa fa-cube text-success"></i>
                            ${cellItem.name}
                            <small class="text-muted">(${cellItem.operator_count || 0} operators)</small>
                        </h5>
                    </div>
                    <div class="col-3">
                        <label class="form-label">Bulk Efficiency %</label>
                        <input type="number" class="form-control form-control-sm bulk-efficiency" 
                               data-group="${cellItem.name}" placeholder="Enter efficiency">
                    </div>
                    <div class="col-3">
                        <label class="form-label">Bulk Target/Hr</label>
                        <input type="number" class="form-control form-control-sm bulk-target" 
                               data-group="${cellItem.name}" placeholder="Enter target">
                    </div>
                </div>
            </div>
            <div class="tree-group-content">
                ${this.createCombinationTable(combinations, 'style')}
            </div>
        `;

        this.bindBulkUpdateEvents(groupDiv, cellItem.name, combinations);
        return groupDiv;
    }

    createCombinationTable(combinations, labelColumn) {
        let tableHTML = `
            <table class="table table-sm combination-table">
                <thead>
                    <tr>
                        <th>${labelColumn === 'cell' ? 'Physical Cell' : 'Style'}</th>
                        <th>SAM</th>
                        <th>Operators</th>
                        <th>Efficiency %</th>
                        <th>Target/Hr</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
        `;

        combinations.forEach(combination => {
            const isChanged = combination.has_changes;
            const rowClass = isChanged ? 'table-warning' : '';
            const labelValue = labelColumn === 'cell' ? combination.physical_cell : 
                             (combination.style_name || combination.style);
            
            tableHTML += `
                <tr class="${rowClass}" data-combination='${JSON.stringify(combination).replace(/'/g, "&#39;")}'>
                    <td>
                        <strong>${labelValue}</strong>
                        ${combination.is_existing ? '<span class="badge badge-success badge-sm">Configured</span>' : '<span class="badge badge-secondary badge-sm">New</span>'}
                    </td>
                    <td>
                        <span class="sam-display">${combination.sam || 0}</span>
                        <button class="btn btn-sm btn-link calculate-sam-btn" data-cell="${combination.physical_cell}" data-style="${combination.style}">
                            <i class="fa fa-calculator"></i>
                        </button>
                    </td>
                    <td>${combination.operator}</td>
                    <td>
                        <input type="number" class="form-control form-control-sm efficiency-input" 
                               value="${combination.efficiency || ''}" min="0" max="100" step="0.01">
                    </td>
                    <td>
                        <input type="number" class="form-control form-control-sm target-input" 
                               value="${combination.hour_target || ''}" min="0" step="0.01">
                    </td>
                    <td>
                        <button class="btn btn-sm btn-info history-btn" data-cell="${combination.physical_cell}" data-style="${combination.style}">
                            <i class="fa fa-history"></i>
                        </button>
                    </td>
                </tr>
            `;
        });

        tableHTML += '</tbody></table>';
        return tableHTML;
    }

    bindBulkUpdateEvents(groupDiv, groupName, combinations) {
        const self = this;
        
        $(groupDiv).on('click', '.calculate-sam-btn', async function(e) {
            const cell = $(this).data('cell');
            const style = $(this).data('style');
            await self.calculateSAM(cell, style, this);
        });

        $(groupDiv).on('input', '.bulk-efficiency', function(e) {
            const efficiency = parseFloat($(this).val());
            if (!isNaN(efficiency)) {
                self.bulkUpdateEfficiency(combinations, efficiency);
            }
        });

        $(groupDiv).on('input', '.bulk-target', function(e) {
            const target = parseFloat($(this).val());
            if (!isNaN(target)) {
                self.bulkUpdateTarget(combinations, target);
            }
        });

        $(groupDiv).on('input', '.efficiency-input', function(e) {
            const row = $(this).closest('tr')[0];
            const combination = JSON.parse(row.dataset.combination.replace(/&#39;/g, "'"));
            const efficiency = parseFloat($(this).val()) || 0;
            
            const target = self.calculateTargetFromEfficiency(efficiency, combination.operator, combination.sam);
            $(row).find('.target-input').val(target);
            
            self.markCombinationChanged(row, combination, { efficiency, hour_target: target });
        });

        $(groupDiv).on('input', '.target-input', function(e) {
            const row = $(this).closest('tr')[0];
            const combination = JSON.parse(row.dataset.combination.replace(/&#39;/g, "'"));
            const target = parseFloat($(this).val()) || 0;
            
            const efficiency = self.calculateEfficiencyFromTarget(target, combination.operator, combination.sam);
            $(row).find('.efficiency-input').val(efficiency);
            
            self.markCombinationChanged(row, combination, { efficiency, hour_target: target });
        });

        $(groupDiv).on('click', '.history-btn', function(e) {
            const cell = $(this).data('cell');
            const style = $(this).data('style');
            self.showHistory(cell, style);
        });
    }

    bulkUpdateEfficiency(combinations, efficiency) {
        const self = this;
        combinations.forEach(combination => {
            const target = self.calculateTargetFromEfficiency(efficiency, combination.operator, combination.sam);
            const row = $(self.page.body).find(`tr[data-combination*='"physical_cell":"${combination.physical_cell}"'][data-combination*='"style":"${combination.style}"']`)[0];
            
            if (row) {
                $(row).find('.efficiency-input').val(efficiency);
                $(row).find('.target-input').val(target);
                self.markCombinationChanged(row, combination, { efficiency, hour_target: target });
            }
        });
    }

    bulkUpdateTarget(combinations, target) {
        const self = this;
        combinations.forEach(combination => {
            const efficiency = self.calculateEfficiencyFromTarget(target, combination.operator, combination.sam);
            const row = $(self.page.body).find(`tr[data-combination*='"physical_cell":"${combination.physical_cell}"'][data-combination*='"style":"${combination.style}"']`)[0];
            
            if (row) {
                $(row).find('.efficiency-input').val(efficiency);
                $(row).find('.target-input').val(target);
                self.markCombinationChanged(row, combination, { efficiency, hour_target: target });
            }
        });
    }

    markCombinationChanged(row, combination, changes) {
        const key = `${combination.physical_cell}-${combination.style}`;
        const existingChanges = this.pendingChanges.get(key) || { ...combination };
        
        Object.assign(existingChanges, changes);
        existingChanges.has_changes = true;
        
        this.pendingChanges.set(key, existingChanges);
        $(row).addClass('table-warning');
        row.dataset.combination = JSON.stringify(existingChanges).replace(/'/g, "&#39;");
        
        this.updateSaveButtonState();
    }

    updateSaveButtonState() {
        const saveBtn = $(this.page.body).find('#save-all-btn')[0];
        const hasChanges = this.pendingChanges.size > 0;
        
        saveBtn.disabled = !hasChanges;
        saveBtn.innerHTML = hasChanges ? 
            `<i class="fa fa-save"></i> Save ${this.pendingChanges.size} Changes` :
            `<i class="fa fa-save"></i> Save All Changes`;
    }

    async saveAllChanges() {
        if (this.pendingChanges.size === 0) {
            frappe.msgprint('No changes to save');
            return;
        }

        const changes = Array.from(this.pendingChanges.values());
        this.showConfirmModal(
            `Are you sure you want to save ${changes.length} configuration changes? This will create new versions for modified combinations.`,
            () => this.performSave(changes)
        );
    }

    async performSave(changes) {
        this.showLoading(true, 'Saving changes...');
        
        try {
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
                
                this.pendingChanges.clear();
                await this.loadData();
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

    async calculateSAM(physicalCell, style, button) {
        const originalHTML = button.innerHTML;
        button.innerHTML = '<i class="fa fa-spinner fa-spin"></i>';
        button.disabled = true;

        try {
            const response = await frappe.call({
                method: 'erpnext_trackerx_customization.erpnext_trackerx_customization.api.production_target_configuration_manager.calculate_sam',
                args: {
                    physical_cell: physicalCell,
                    style: style
                }
            });

            const sam = response.message;
            const samDisplay = $(button).parent().find('.sam-display')[0];
            samDisplay.textContent = sam;
            
            const row = $(button).closest('tr')[0];
            const combination = JSON.parse(row.dataset.combination.replace(/&#39;/g, "'"));
            this.markCombinationChanged(row, combination, { sam });

        } catch (error) {
            console.error('Error calculating SAM:', error);
            frappe.msgprint('Error calculating SAM');
        } finally {
            button.innerHTML = originalHTML;
            button.disabled = false;
        }
    }

    calculateTargetFromEfficiency(efficiency, operator, sam) {
        if (sam === 0) return 0;
        return Math.round((efficiency * 60 * operator) / sam * 100) / 100;
    }

    calculateEfficiencyFromTarget(target, operator, sam) {
        if (operator === 0 || sam === 0) return 0;
        return Math.round((target * sam) / (60 * operator) * 10000) / 100;
    }

    async showHistory(physicalCell, style) {
        try {
            const response = await frappe.call({
                method: 'erpnext_trackerx_customization.erpnext_trackerx_customization.api.production_target_configuration_manager.get_configuration_history',
                args: {
                    physical_cell: physicalCell,
                    style: style
                }
            });

            const history = response.message;
            this.displayHistoryModal(physicalCell, style, history);

        } catch (error) {
            console.error('Error fetching history:', error);
            frappe.msgprint('Error fetching configuration history');
        }
    }

    displayHistoryModal(physicalCell, style, history) {
        let historyHTML = `
            <div class="modal fade" id="historyModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Configuration History</h5>
                            <button type="button" class="close" data-dismiss="modal">
                                <span>&times;</span>
                            </button>
                        </div>
                        <div class="modal-body">
                            <h6>${physicalCell} - ${style}</h6>
                            <table class="table table-sm">
                                <thead>
                                    <tr>
                                        <th>Version</th>
                                        <th>SAM</th>
                                        <th>Efficiency</th>
                                        <th>Target/Hr</th>
                                        <th>Start</th>
                                        <th>End</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
        `;

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
                </tr>
            `;
        });

        historyHTML += `
                                </tbody>
                            </table>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        $('#historyModal').remove();
        $('body').append(historyHTML);
        $('#historyModal').modal('show');
    }

    showConfirmModal(message, confirmAction) {
        $(this.page.body).find('#confirm-message').text(message);
        this.pendingConfirmAction = confirmAction;
        $('#confirmModal').modal('show');
    }

    showLoading(show, message = 'Loading...') {
        const loadingIndicator = $(this.page.body).find('.loading-indicator')[0];
        if (show) {
            loadingIndicator.style.display = 'block';
            $(loadingIndicator).find('p').text(message);
            $(this.page.body).find('.tree-container').css('opacity', '0.5');
        } else {
            loadingIndicator.style.display = 'none';
            $(this.page.body).find('.tree-container').css('opacity', '1');
        }
    }

    updateStatus() {
        const totalCombinations = this.data.combinations.length;
        const existingConfigurations = this.data.combinations.filter(c => c.is_existing).length;
        
        $(this.page.body).find('#total-combinations').text(
            `${totalCombinations} combinations (${existingConfigurations} configured)`
        );
        
        $(this.page.body).find('#last-updated').text(
            `Last updated: ${new Date().toLocaleTimeString()}`
        );
    }

    groupBy(array, key) {
        return array.reduce((groups, item) => {
            const group = item[key];
            if (!groups[group]) {
                groups[group] = [];
            }
            groups[group].push(item);
            return groups;
        }, {});
    }
}