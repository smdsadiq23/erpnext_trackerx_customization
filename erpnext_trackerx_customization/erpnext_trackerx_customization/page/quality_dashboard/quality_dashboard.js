frappe.pages['quality_dashboard'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Quality Dashboard',
        single_column: true
    });
    
    frappe.quality_dashboard = new QualityDashboard(page);
};

class QualityDashboard {
    constructor(page) {
        this.page = page;
        this.make();
    }
    
    make() {
        // Check user roles
        this.user_roles = frappe.user_roles || [];
        this.is_quality_inspector = this.user_roles.includes('Quality Inspector');
        this.is_quality_manager = this.user_roles.includes('Quality Manager');
        this.is_system_user = this.user_roles.includes('Administrator') || this.user_roles.includes('System Manager');
        
        // Set dashboard title based on role
        let dashboard_title = 'Quality Dashboard';
        let inspection_type_text = '';
        
        if (this.is_quality_manager && !this.is_system_user) {
            dashboard_title = 'Quality Manager Dashboard';
            inspection_type_text = '<p class="role-info">Showing completed inspections (Passed, Failed, Hold)</p>';
        } else if (this.is_quality_inspector && !this.is_system_user) {
            dashboard_title = 'Quality Inspector Dashboard';
            inspection_type_text = '<p class="role-info">Showing pending inspections (Draft, In Progress, Hold)</p>';
        }
        
        this.page.main.html(`
            <div id="quality-dashboard-container">
                <div class="dashboard-header">
                    <h1 id="dashboard-title">${dashboard_title}</h1>
                    ${inspection_type_text}
                </div>
                
                <div id="stats-grid" class="stats-grid" style="display: none;">
                    <!-- Statistics will be populated by JavaScript -->
                </div>
                
                <div class="inspection-section">
                    <div class="tabs">
                        <div class="tab active" data-tab="fabric">
                            🧵 Fabric Inspections (<span id="fabric-count">0</span>)
                        </div>
                        <div class="tab" data-tab="trims">
                            ✂️ Trims Inspections (<span id="trims-count">0</span>)
                        </div>
                    </div>
                    
                    <div id="fabric-tab" class="tab-content active">
                        <div id="fabric-inspections-list">
                            <p class="loading">Loading fabric inspections...</p>
                        </div>
                    </div>
                    
                    <div id="trims-tab" class="tab-content">
                        <div id="trims-inspections-list">
                            <p class="loading">Loading trims inspections...</p>
                        </div>
                    </div>
                </div>
            </div>
        `);
        
        this.add_styles();
        this.load_data();
        this.setup_events();
    }
    
    add_styles() {
        if (!document.getElementById('quality-dashboard-styles')) {
            const style = document.createElement('style');
            style.id = 'quality-dashboard-styles';
            style.textContent = `
                #quality-dashboard-container {
                    max-width: 1400px;
                    margin: 0 auto;
                    padding: 20px;
                }
                
                .dashboard-header {
                    background: white;
                    border-radius: 12px;
                    padding: 24px;
                    margin-bottom: 24px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }
                
                .dashboard-header h1 {
                    margin: 0;
                    color: #1e293b;
                    font-size: 28px;
                    font-weight: 700;
                }
                
                .role-info {
                    margin: 8px 0 0 0;
                    color: #64748b;
                    font-size: 14px;
                    font-style: italic;
                }
                
                .inspection-section {
                    background: white;
                    border-radius: 12px;
                    padding: 24px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }
                
                .tabs {
                    display: flex;
                    margin-bottom: 20px;
                    border-bottom: 1px solid #e2e8f0;
                }
                
                .tab {
                    padding: 12px 24px;
                    cursor: pointer;
                    border-bottom: 2px solid transparent;
                    font-weight: 500;
                    color: #64748b;
                    transition: all 0.2s;
                }
                
                .tab.active {
                    color: #2563eb;
                    border-bottom-color: #2563eb;
                }
                
                .tab-content {
                    display: none;
                }
                
                .tab-content.active {
                    display: block;
                }
                
                .inspection-table {
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 14px;
                }
                
                .inspection-table th {
                    background: #f8fafc;
                    padding: 12px;
                    text-align: left;
                    font-weight: 600;
                    color: #475569;
                    border-bottom: 1px solid #e2e8f0;
                }
                
                .inspection-table td {
                    padding: 12px;
                    border-bottom: 1px solid #e2e8f0;
                    vertical-align: top;
                }
                
                .inspection-table tbody tr:hover {
                    background: #f8fafc;
                    cursor: pointer;
                }
                
                .status-badge {
                    display: inline-block;
                    padding: 4px 8px;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: 600;
                    text-transform: uppercase;
                }
                
                .status-draft { background: #f1f5f9; color: #475569; }
                .status-in-progress { background: #fef3c7; color: #92400e; }
                .status-hold { background: #fed7d7; color: #c53030; }
                .status-passed { background: #d1fae5; color: #166534; }
                .status-failed { background: #fee2e2; color: #dc2626; }
                .status-completed { background: #d1fae5; color: #166534; }
                .status-conditionally-passed { background: #fef3c7; color: #92400e; }
                .status-accepted { background: #d1fae5; color: #166534; }
                .status-rejected { background: #fee2e2; color: #dc2626; }
                .status-conditional-accept { background: #fef3c7; color: #92400e; }
                .status-pending { background: #f1f5f9; color: #475569; }
                .status-approved { background: #d1fae5; color: #166534; }
                .status-rejected { background: #fee2e2; color: #dc2626; }
                
                .btn {
                    display: inline-block;
                    padding: 8px 16px;
                    border-radius: 6px;
                    text-decoration: none;
                    font-weight: 500;
                    font-size: 14px;
                    transition: all 0.2s;
                    background: #2563eb;
                    color: white;
                    border: none;
                    cursor: pointer;
                }
                
                .btn:hover {
                    background: #1d4ed8;
                }
                
                .loading, .no-inspections {
                    text-align: center;
                    padding: 40px;
                    color: #64748b;
                }
            `;
            document.head.appendChild(style);
        }
    }
    
    setup_events() {
        // Tab switching
        $(document).on('click', '.tab', (e) => {
            const tab = $(e.target).data('tab');
            this.switch_tab(tab);
        });
    }
    
    switch_tab(tab_name) {
        // Remove active from all tabs
        $('.tab').removeClass('active');
        $('.tab-content').removeClass('active');
        
        // Add active to selected tab
        $(`.tab[data-tab="${tab_name}"]`).addClass('active');
        $(`#${tab_name}-tab`).addClass('active');
    }
    
    load_data() {
        this.load_fabric_inspections();
        this.load_trims_inspections();
    }
    
    load_fabric_inspections() {
        // Choose method based on user role
        let method = 'get_pending_fabric_inspections'; // Default for Quality Inspector
        
        if (this.is_quality_manager && !this.is_system_user) {
            method = 'get_completed_fabric_inspections';
        }
        
        frappe.call({
            method: `erpnext_trackerx_customization.erpnext_trackerx_customization.page.quality_dashboard.quality_dashboard.${method}`,
            callback: (r) => {
                if (r.message) {
                    this.render_fabric_inspections(r.message);
                    $('#fabric-count').text(r.message.length);
                }
            }
        });
    }
    
    load_trims_inspections() {
        // Choose method based on user role
        let method = 'get_pending_trims_inspections'; // Default for Quality Inspector
        
        if (this.is_quality_manager && !this.is_system_user) {
            method = 'get_completed_trims_inspections';
        }
        
        frappe.call({
            method: `erpnext_trackerx_customization.erpnext_trackerx_customization.page.quality_dashboard.quality_dashboard.${method}`,
            callback: (r) => {
                if (r.message) {
                    this.render_trims_inspections(r.message);
                    $('#trims-count').text(r.message.length);
                }
            }
        });
    }
    
    render_fabric_inspections(inspections) {
        const container = $('#fabric-inspections-list');
        
        // Set messages based on user role
        let no_inspections_title = 'No Fabric Inspections Found';
        let no_inspections_message = 'No fabric inspections at the moment.';
        let action_button_text = 'View';
        
        if (this.is_quality_manager && !this.is_system_user) {
            no_inspections_message = 'No completed fabric inspections at the moment.';
            action_button_text = 'Review';
        } else if (this.is_quality_inspector && !this.is_system_user) {
            no_inspections_message = 'No pending fabric inspections at the moment.';
            action_button_text = 'Inspect';
        }
        
        if (inspections.length === 0) {
            container.html(`<div class="no-inspections"><h3>${no_inspections_title}</h3><p>${no_inspections_message}</p></div>`);
            return;
        }
        
        let html = '<table class="inspection-table"><thead><tr>';
        html += '<th>Inspection ID</th><th>Date</th><th>Supplier</th><th>Item</th><th>Quantity</th><th>Status</th><th>Action</th>';
        html += '</tr></thead><tbody>';
        
        inspections.forEach((inspection) => {
            html += `<tr onclick="open_fabric_inspection('${inspection.name}')">`;
            html += `<td><strong>${inspection.name}</strong></td>`;
            html += `<td>${inspection.inspection_date || ''}</td>`;
            html += `<td>${inspection.supplier || ''}</td>`;
            html += `<td>${inspection.item_code || ''}</td>`;
            html += `<td>${inspection.total_quantity || 0}</td>`;
            
            // For Quality Manager, show inspection_result; for others, show inspection_status
            let displayStatus = inspection.inspection_status || 'Draft';
            let statusClass = (displayStatus || '').toLowerCase().replace(' ', '-');
            
            // Now using single inspection_status field for all statuses
            
            html += `<td><span class="status-badge status-${statusClass}">${displayStatus}</span></td>`;
            html += `<td><button class="btn" onclick="open_fabric_inspection('${inspection.name}'); event.stopPropagation();">${action_button_text}</button></td>`;
            html += '</tr>';
        });
        
        html += '</tbody></table>';
        container.html(html);
    }
    
    render_trims_inspections(inspections) {
        const container = $('#trims-inspections-list');
        
        // Set messages based on user role
        let no_inspections_title = 'No Trims Inspections Found';
        let no_inspections_message = 'No trims inspections at the moment.';
        let action_button_text = 'View';
        
        if (this.is_quality_manager && !this.is_system_user) {
            no_inspections_message = 'No completed trims inspections at the moment.';
            action_button_text = 'Review';
        } else if (this.is_quality_inspector && !this.is_system_user) {
            no_inspections_message = 'No pending trims inspections at the moment.';
            action_button_text = 'Inspect';
        }
        
        if (inspections.length === 0) {
            container.html(`<div class="no-inspections"><h3>${no_inspections_title}</h3><p>${no_inspections_message}</p></div>`);
            return;
        }
        
        let html = '<table class="inspection-table"><thead><tr>';
        html += '<th>Inspection ID</th><th>Date</th><th>Supplier</th><th>Item</th><th>Quantity</th><th>Status</th><th>Action</th>';
        html += '</tr></thead><tbody>';
        
        inspections.forEach((inspection) => {
            html += `<tr onclick="open_trims_inspection('${inspection.name}')">`;
            html += `<td><strong>${inspection.name}</strong></td>`;
            html += `<td>${inspection.inspection_date || ''}</td>`;
            html += `<td>${inspection.supplier || ''}</td>`;
            html += `<td>${inspection.item_code || ''}</td>`;
            html += `<td>${inspection.total_quantity || 0}</td>`;
            
            // For Quality Manager, show inspection_result; for others, show inspection_status
            let displayStatus = inspection.inspection_status || 'Draft';
            let statusClass = (displayStatus || '').toLowerCase().replace(' ', '-');
            
            // Now using single inspection_status field for all statuses
            
            html += `<td><span class="status-badge status-${statusClass}">${displayStatus}</span></td>`;
            html += `<td><button class="btn" onclick="open_trims_inspection('${inspection.name}'); event.stopPropagation();">${action_button_text}</button></td>`;
            html += '</tr>';
        });
        
        html += '</tbody></table>';
        container.html(html);
    }
}

// Global functions for opening inspections
function open_fabric_inspection(inspection_name) {
    window.open(`/fabric_inspection_ui?name=${encodeURIComponent(inspection_name)}`, '_blank');
}

function open_trims_inspection(inspection_name) {
    window.open(`/trims_inspection_ui?name=${encodeURIComponent(inspection_name)}`, '_blank');
}

// Quality Manager quick actions for Fabric Inspections
function quick_pass_fabric_inspection(inspection_name) {
    frappe.prompt([
        {
            label: 'Manager Comment (Optional)',
            fieldname: 'comment',
            fieldtype: 'Small Text',
            description: 'Optional comment for passing this inspection'
        }
    ], function(values) {
        frappe.call({
            method: 'erpnext_trackerx_customization.templates.pages.fabric_inspection_ui.fabric_manager_pass_inspection',
            args: {
                inspection_name: inspection_name,
                manager_comment: values.comment || ''
            },
            callback: function(response) {
                if (response.message && response.message.status === 'success') {
                    frappe.show_alert({
                        message: response.message.message,
                        indicator: 'green'
                    });
                    // Refresh the dashboard
                    setTimeout(() => {
                        frappe.quality_dashboard.load_fabric_inspections();
                    }, 1000);
                } else {
                    frappe.show_alert({
                        message: 'Failed to update inspection status',
                        indicator: 'red'
                    });
                }
            },
            error: function(error) {
                console.error('Error:', error);
                frappe.show_alert({
                    message: error.message || 'Failed to update inspection status',
                    indicator: 'red'
                });
            }
        });
    }, 'Pass Fabric Inspection', 'Pass');
}

function conditional_pass_fabric_inspection(inspection_name) {
    frappe.prompt([
        {
            label: 'Manager Comment (Required)',
            fieldname: 'comment',
            fieldtype: 'Small Text',
            reqd: 1,
            description: 'Comment is required for conditional pass'
        }
    ], function(values) {
        if (!values.comment || !values.comment.trim()) {
            frappe.show_alert({
                message: 'Comment is required for conditional pass',
                indicator: 'red'
            });
            return;
        }
        
        frappe.call({
            method: 'erpnext_trackerx_customization.templates.pages.fabric_inspection_ui.fabric_manager_conditional_pass',
            args: {
                inspection_name: inspection_name,
                manager_comment: values.comment
            },
            callback: function(response) {
                if (response.message && response.message.status === 'success') {
                    frappe.show_alert({
                        message: response.message.message,
                        indicator: 'orange'
                    });
                    // Refresh the dashboard
                    setTimeout(() => {
                        frappe.quality_dashboard.load_fabric_inspections();
                    }, 1000);
                } else {
                    frappe.show_alert({
                        message: 'Failed to update inspection status',
                        indicator: 'red'
                    });
                }
            },
            error: function(error) {
                console.error('Error:', error);
                frappe.show_alert({
                    message: error.message || 'Failed to update inspection status',
                    indicator: 'red'
                });
            }
        });
    }, 'Conditional Pass Fabric Inspection', 'Conditional Pass');
}

// Quality Manager quick actions for Trims Inspections
function quick_pass_trims_inspection(inspection_name) {
    frappe.prompt([
        {
            label: 'Manager Comment (Optional)',
            fieldname: 'comment',
            fieldtype: 'Small Text',
            description: 'Optional comment for passing this inspection'
        }
    ], function(values) {
        frappe.call({
            method: 'erpnext_trackerx_customization.templates.pages.trims_inspection_ui.trims_manager_pass_inspection',
            args: {
                inspection_name: inspection_name,
                manager_comment: values.comment || ''
            },
            callback: function(response) {
                if (response.message && response.message.status === 'success') {
                    frappe.show_alert({
                        message: response.message.message,
                        indicator: 'green'
                    });
                    // Refresh the dashboard
                    setTimeout(() => {
                        frappe.quality_dashboard.load_trims_inspections();
                    }, 1000);
                } else {
                    frappe.show_alert({
                        message: 'Failed to update inspection status',
                        indicator: 'red'
                    });
                }
            },
            error: function(error) {
                console.error('Error:', error);
                frappe.show_alert({
                    message: error.message || 'Failed to update inspection status',
                    indicator: 'red'
                });
            }
        });
    }, 'Pass Trims Inspection', 'Pass');
}

function conditional_pass_trims_inspection(inspection_name) {
    frappe.prompt([
        {
            label: 'Manager Comment (Required)',
            fieldname: 'comment',
            fieldtype: 'Small Text',
            reqd: 1,
            description: 'Comment is required for conditional pass'
        }
    ], function(values) {
        if (!values.comment || !values.comment.trim()) {
            frappe.show_alert({
                message: 'Comment is required for conditional pass',
                indicator: 'red'
            });
            return;
        }
        
        frappe.call({
            method: 'erpnext_trackerx_customization.templates.pages.trims_inspection_ui.trims_manager_conditional_pass',
            args: {
                inspection_name: inspection_name,
                manager_comment: values.comment
            },
            callback: function(response) {
                if (response.message && response.message.status === 'success') {
                    frappe.show_alert({
                        message: response.message.message,
                        indicator: 'orange'
                    });
                    // Refresh the dashboard
                    setTimeout(() => {
                        frappe.quality_dashboard.load_trims_inspections();
                    }, 1000);
                } else {
                    frappe.show_alert({
                        message: 'Failed to update inspection status',
                        indicator: 'red'
                    });
                }
            },
            error: function(error) {
                console.error('Error:', error);
                frappe.show_alert({
                    message: error.message || 'Failed to update inspection status',
                    indicator: 'red'
                });
            }
        });
    }, 'Conditional Pass Trims Inspection', 'Conditional Pass');
}