frappe.pages['warehouse-capacity-dashboard'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Warehouse Capacity Dashboard',
		single_column: true
	});

	// Check permissions before loading
	frappe.call({
		method: 'erpnext_trackerx_customization.api.warehouse_permissions.validate_warehouse_dashboard_access',
		callback: function(r) {
			if (r.message && r.message.allowed) {
				// User has permission, load the dashboard
				loadWarehouseCapacityDashboard(page);
			} else {
				// Show permission error
				showPermissionError(page, r.message ? r.message.reason : 'Access denied');
			}
		},
		error: function() {
			showPermissionError(page, 'Failed to validate permissions. Please contact your administrator.');
		}
	});
};

function showPermissionError(page, reason) {
	$(page.body).html(`
		<div style="
			display: flex;
			flex-direction: column;
			align-items: center;
			justify-content: center;
			height: 60vh;
			text-align: center;
			color: #666;
		">
			<div style="
				background: #fff5f5;
				border: 2px solid #fed7d7;
				border-radius: 12px;
				padding: 40px;
				max-width: 500px;
				box-shadow: 0 4px 12px rgba(0,0,0,0.1);
			">
				<div style="font-size: 4rem; margin-bottom: 20px;">🔒</div>
				<h2 style="color: #c53030; margin-bottom: 15px;">Access Restricted</h2>
				<p style="color: #666; margin-bottom: 20px; font-size: 1.1rem;">
					You don't have permission to access the Warehouse Capacity Dashboard.
				</p>
				<div style="
					background: #f7fafc;
					border: 1px solid #e2e8f0;
					border-radius: 8px;
					padding: 15px;
					margin-bottom: 20px;
					font-size: 0.9rem;
					color: #4a5568;
				">
					<strong>Reason:</strong> ${reason}
				</div>
				<p style="color: #666; font-size: 0.9rem; margin-bottom: 25px;">
					Required permissions: Warehouse module access and appropriate company permissions
				</p>
				<button onclick="frappe.set_route('List', 'User Permission')" style="
					background: #3182ce;
					color: white;
					border: none;
					padding: 12px 24px;
					border-radius: 8px;
					cursor: pointer;
					font-size: 1rem;
					margin-right: 10px;
				">View User Permissions</button>
				<button onclick="frappe.set_route('workspace')" style="
					background: #718096;
					color: white;
					border: none;
					padding: 12px 24px;
					border-radius: 8px;
					cursor: pointer;
					font-size: 1rem;
				">Go to Workspace</button>
			</div>
		</div>
	`);
}

function loadWarehouseCapacityDashboard(page) {
	// Add refresh button to page toolbar
	page.add_menu_item(__('Refresh Data'), function() {
		loadDashboardData();
	}, true);

	// Add settings button
	page.add_menu_item(__('Dashboard Settings'), function() {
		showDashboardSettings();
	}, true);

	// Insert the dashboard HTML content
	$(page.body).html(getWarehouseCapacityHTML());

	// Initialize dashboard functionality
	initializeWarehouseCapacityApp();
}

function getWarehouseCapacityHTML() {
	return \`
		<style>
			.warehouse-dashboard {
				font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", "Oxygen", "Ubuntu", "Cantarell", "Fira Sans", "Droid Sans", "Helvetica Neue", sans-serif;
				margin: 0;
				padding: 20px;
				background-color: #f8f9fa;
			}

			.dashboard-header {
				background: linear-gradient(135deg, #96be37 0%, #7ba428 100%);
				color: white;
				padding: 30px;
				border-radius: 10px;
				margin-bottom: 30px;
				text-align: center;
			}

			.dashboard-header h1 {
				margin: 0;
				font-size: 2.5rem;
				font-weight: 600;
			}

			.dashboard-header p {
				margin: 10px 0 0 0;
				opacity: 0.9;
				font-size: 1.1rem;
			}

			.cards-container {
				display: grid;
				grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
				gap: 20px;
				margin-bottom: 30px;
			}

			.card {
				background: white;
				padding: 25px;
				border-radius: 12px;
				box-shadow: 0 2px 10px rgba(0,0,0,0.1);
				border-left: 4px solid #96be37;
				transition: transform 0.2s ease, box-shadow 0.2s ease;
			}

			.card:hover {
				transform: translateY(-2px);
				box-shadow: 0 4px 20px rgba(0,0,0,0.15);
			}

			.card-header {
				display: flex;
				justify-content: space-between;
				align-items: center;
				margin-bottom: 15px;
			}

			.card-title {
				font-size: 0.9rem;
				color: #666;
				text-transform: uppercase;
				letter-spacing: 0.5px;
				margin: 0;
			}

			.card-value {
				font-size: 2.2rem;
				font-weight: 700;
				color: #333;
				margin: 10px 0;
			}

			.card-change {
				font-size: 0.85rem;
				font-weight: 500;
			}

			.card-change.positive {
				color: #27ae60;
			}

			.card-change.negative {
				color: #e74c3c;
			}

			.card-description {
				font-size: 0.8rem;
				color: #888;
				margin-top: 8px;
			}

			.loading-indicator {
				display: flex;
				justify-content: center;
				align-items: center;
				padding: 40px;
				font-size: 1.1rem;
				color: #666;
			}

			.error-container {
				background: #fff5f5;
				border: 1px solid #fed7d7;
				border-radius: 8px;
				padding: 20px;
				margin: 20px 0;
				color: #c53030;
			}

			.refresh-btn {
				background: linear-gradient(135deg, #96be37, #7ba428);
				color: white;
				border: none;
				padding: 12px 24px;
				border-radius: 6px;
				cursor: pointer;
				font-size: 1rem;
				font-weight: 500;
				transition: all 0.2s ease;
				margin-bottom: 20px;
			}

			.refresh-btn:hover {
				transform: translateY(-1px);
				box-shadow: 0 4px 12px rgba(150, 190, 55, 0.3);
			}

			.refresh-btn:disabled {
				background: #ccc;
				cursor: not-allowed;
			}

			/* Permission Info Bar */
			.permission-info-bar {
				background: #e8f5e8;
				border: 1px solid #4caf50;
				border-radius: 8px;
				padding: 15px;
				margin-bottom: 20px;
				display: flex;
				justify-content: space-between;
				align-items: center;
			}

			.permission-info {
				display: flex;
				gap: 20px;
				align-items: center;
				font-size: 0.9rem;
				color: #2c5530;
			}

			.user-badge {
				background: #4caf50;
				color: white;
				padding: 4px 12px;
				border-radius: 12px;
				font-size: 0.8rem;
				font-weight: 500;
			}

			/* Table styles and other existing styles from the HTML file */
			.enhanced-table-container {
				background: white;
				border-radius: 12px;
				box-shadow: 0 2px 10px rgba(0,0,0,0.1);
				margin-top: 30px;
			}

			.table-header {
				padding: 25px;
				border-bottom: 1px solid #e0e0e0;
			}

			.table-header h3 {
				margin: 0;
				color: #333;
				font-size: 1.5rem;
			}

			.enhanced-table {
				width: 100%;
				border-collapse: collapse;
			}

			.enhanced-table th {
				background: #f8f9fa;
				padding: 15px 12px;
				text-align: left;
				font-weight: 600;
				color: #333;
				border-bottom: 2px solid #e0e0e0;
			}

			.enhanced-table td {
				padding: 12px;
				border-bottom: 1px solid #e0e0e0;
			}

			.enhanced-table tr:hover {
				background: #f8f9fa;
			}

			.status-badge {
				padding: 4px 8px;
				border-radius: 4px;
				font-size: 0.8rem;
				font-weight: 500;
			}

			.status-healthy { background: #d4edda; color: #155724; }
			.status-caution { background: #fff3cd; color: #856404; }
			.status-warning { background: #f8d7da; color: #721c24; }
			.status-critical { background: #f5c6cb; color: #721c24; }
		</style>

		<div class="warehouse-dashboard">
			<!-- Permission Info Bar -->
			<div id="permissionInfoBar" class="permission-info-bar" style="display: none;">
				<div class="permission-info">
					<span id="userInfo"></span>
					<span id="companyInfo"></span>
					<span id="accessInfo"></span>
				</div>
				<span class="user-badge" id="userBadge">Authorized User</span>
			</div>

			<!-- Dashboard Header -->
			<div class="dashboard-header">
				<h1>🏭 Warehouse Capacity Intelligence Dashboard</h1>
				<p>Real-time monitoring and analytics for optimized warehouse management</p>
				<div id="selectedWarehouseInfo" style="margin-top: 15px; font-size: 1rem; display: none;"></div>
				<div id="warehouseSelector" style="margin-top: 20px; display: none;">
					<div style="display: flex; align-items: flex-end; gap: 15px; flex-wrap: wrap; justify-content: center;">
						<div style="flex: 1; min-width: 300px; max-width: 400px;">
							<label for="warehouseDropdown" style="display: block; margin-bottom: 8px; font-size: 1rem; opacity: 0.9; font-weight: 500;">📍 Selected Warehouse:</label>
							<select id="warehouseDropdown" onchange="changeSelectedWarehouse()" style="
								padding: 12px 16px;
								font-size: 1rem;
								border: 2px solid rgba(255,255,255,0.3);
								border-radius: 10px;
								background: rgba(255,255,255,0.2);
								color: white;
								backdrop-filter: blur(10px);
								width: 100%;
								height: 48px;
								box-sizing: border-box;
								transition: all 0.3s ease;
							">
								<option value="">Loading warehouses...</option>
							</select>
						</div>
					</div>
				</div>
			</div>

			<!-- Refresh Button -->
			<button id="refreshBtn" class="refresh-btn" onclick="loadDashboardData()">
				🔄 Refresh Data
			</button>

			<!-- Loading Indicator -->
			<div id="loadingIndicator" class="loading-indicator" style="display: none;">
				<div>⏳ Loading dashboard data...</div>
			</div>

			<!-- Error Container -->
			<div id="errorContainer" class="error-container" style="display: none;"></div>

			<!-- Cards Container -->
			<div id="cardsContainer" class="cards-container" style="display: none;">
				<!-- Cards will be populated here -->
			</div>

			<!-- Enhanced Table -->
			<div id="enhancedTableContainer" class="enhanced-table-container" style="display: none;">
				<div class="table-header">
					<h3>📊 Warehouse Data Overview</h3>
				</div>
				<div id="tableContent">
					<!-- Table content will be populated here -->
				</div>
			</div>
		</div>
	\`;
}

function initializeWarehouseCapacityApp() {
	// Dashboard variables
	window.dashboardData = null;
	window.selectedMainWarehouse = null;
	window.availableWarehouses = [];

	// Show permission info
	showPermissionInfo();

	// Initialize the application
	initializeApp();
}

function showPermissionInfo() {
	frappe.call({
		method: 'erpnext_trackerx_customization.api.warehouse_permissions.get_user_permission_info',
		callback: function(r) {
			if (r.message) {
				const userInfo = r.message;
				const permissionBar = document.getElementById('permissionInfoBar');
				const userInfoSpan = document.getElementById('userInfo');
				const companyInfoSpan = document.getElementById('companyInfo');
				const accessInfoSpan = document.getElementById('accessInfo');
				const userBadge = document.getElementById('userBadge');

				userInfoSpan.textContent = \`👤 \${userInfo.user || 'Unknown User'}\`;
				companyInfoSpan.textContent = \`🏢 \${userInfo.permitted_companies_count || 0} companies accessible\`;

				if (userInfo.is_system_manager) {
					accessInfoSpan.textContent = '🔑 System Manager (All data visible)';
					userBadge.textContent = 'System Manager';
					userBadge.style.background = '#4caf50';
				} else {
					accessInfoSpan.textContent = 'Warehouse Module Access';
					userBadge.textContent = 'Authorized User';
					userBadge.style.background = '#2196f3';
				}

				permissionBar.style.display = 'flex';
			}
		}
	});
}

async function initializeApp() {
	try {
		// Load available warehouses using the secure API
		const response = await frappe.call({
			method: 'erpnext_trackerx_customization.api.warehouse_permissions.get_permitted_warehouses'
		});

		if (response.message && response.message.length > 0) {
			// Process warehouses to find main warehouses
			window.availableWarehouses = response.message.filter(wh =>
				!wh.parent_warehouse || wh.parent_warehouse === ''
			);

			setupWarehouseDropdown();

			// Load dashboard data for the first warehouse or all warehouses
			if (window.availableWarehouses.length > 0) {
				window.selectedMainWarehouse = window.availableWarehouses[0].name;
			}

			loadDashboardData();
		} else {
			showError('No warehouses found. Please check your permissions or contact your administrator.');
		}
	} catch (error) {
		showError('Error loading warehouses: ' + error.message);
	}
}

function setupWarehouseDropdown() {
	const dropdown = document.getElementById('warehouseDropdown');
	const selector = document.getElementById('warehouseSelector');

	if (window.availableWarehouses.length === 0) {
		dropdown.innerHTML = '<option value="">No warehouses available</option>';
		return;
	}

	// Add "All Warehouses" option
	let options = '<option value="">All Warehouses</option>';

	// Add individual warehouses
	options += window.availableWarehouses.map(warehouse =>
		\`<option value="\${warehouse.name}" \${warehouse.name === window.selectedMainWarehouse ? 'selected' : ''}">
			\${warehouse.warehouse_name || warehouse.name}
		</option>\`
	).join('');

	dropdown.innerHTML = options;
	selector.style.display = 'block';
}

function changeSelectedWarehouse() {
	const dropdown = document.getElementById('warehouseDropdown');
	const newWarehouse = dropdown.value;

	if (newWarehouse !== window.selectedMainWarehouse) {
		window.selectedMainWarehouse = newWarehouse;
		loadDashboardData();
	}
}

async function loadDashboardData() {
	const refreshBtn = document.getElementById('refreshBtn');
	const loadingIndicator = document.getElementById('loadingIndicator');
	const cardsContainer = document.getElementById('cardsContainer');
	const errorContainer = document.getElementById('errorContainer');

	// Show loading state
	refreshBtn.disabled = true;
	refreshBtn.textContent = '⏳ Loading...';
	loadingIndicator.style.display = 'flex';
	cardsContainer.style.display = 'none';
	errorContainer.style.display = 'none';

	try {
		// Call secure API
		const args = {};
		if (window.selectedMainWarehouse) {
			args.main_warehouse = window.selectedMainWarehouse;
		}

		const response = await frappe.call({
			method: 'erpnext_trackerx_customization.api.warehouse_capacity_dashboard.get_warehouse_capacity_summary',
			args: args
		});

		if (response.message && response.message.success) {
			window.dashboardData = response.message;
			renderDashboard();
		} else {
			showError('Failed to load dashboard data: ' + (response.message?.error || 'Unknown error'));
		}

	} catch (error) {
		console.error('Error loading dashboard data:', error);
		showError('Error loading dashboard data: ' + error.message);
	} finally {
		// Reset loading state
		refreshBtn.disabled = false;
		refreshBtn.textContent = '🔄 Refresh Data';
		loadingIndicator.style.display = 'none';
	}
}

function renderDashboard() {
	if (!window.dashboardData || !window.dashboardData.success) {
		showError('Invalid dashboard data received');
		return;
	}

	const data = window.dashboardData.data;
	renderCards(data);
	renderTable(data);

	document.getElementById('cardsContainer').style.display = 'grid';
	document.getElementById('enhancedTableContainer').style.display = 'block';
}

function renderCards(data) {
	const container = document.getElementById('cardsContainer');

	container.innerHTML = \`
		<!-- Total Warehouses Card -->
		<div class="card">
			<div class="card-header">
				<h3 class="card-title">🏭 Total Warehouses</h3>
			</div>
			<div class="card-value">\${data.total_warehouses.value}</div>
			<div class="card-change \${data.total_warehouses.change >= 0 ? 'positive' : 'negative'}">
				\${data.total_warehouses.change >= 0 ? '↗' : '↘'} \${Math.abs(data.total_warehouses.change)}
			</div>
			<div class="card-description">\${data.total_warehouses.description}</div>
		</div>

		<!-- Overall Utilization Card -->
		<div class="card">
			<div class="card-header">
				<h3 class="card-title">📊 Overall Utilization</h3>
			</div>
			<div class="card-value">\${data.overall_utilization.value}%</div>
			<div class="card-change \${data.overall_utilization.change >= 0 ? 'positive' : 'negative'}">
				\${data.overall_utilization.change >= 0 ? '↗' : '↘'} \${Math.abs(data.overall_utilization.change)}%
			</div>
			<div class="card-description">\${data.overall_utilization.description}</div>
		</div>

		<!-- Critical Alerts Card -->
		<div class="card">
			<div class="card-header">
				<h3 class="card-title">⚠️ Critical Alerts</h3>
			</div>
			<div class="card-value">\${data.critical_alerts.value}</div>
			<div class="card-change \${data.critical_alerts.change >= 0 ? 'negative' : 'positive'}">
				\${data.critical_alerts.change >= 0 ? '↗' : '↘'} \${Math.abs(data.critical_alerts.change)}
			</div>
			<div class="card-description">\${data.critical_alerts.description}</div>
		</div>

		<!-- Available Capacity Card -->
		<div class="card">
			<div class="card-header">
				<h3 class="card-title">📈 Available Capacity</h3>
			</div>
			<div class="card-value">\${data.available_capacity.value}</div>
			<div class="card-change \${data.available_capacity.change >= 0 ? 'positive' : 'negative'}">
				\${data.available_capacity.change >= 0 ? '↗' : '↘'} \${Math.abs(data.available_capacity.change)}
			</div>
			<div class="card-description">\${data.available_capacity.description}</div>
		</div>
	\`;
}

function renderTable(data) {
	const tableContainer = document.getElementById('tableContent');

	// Simple table rendering - you can expand this based on your data structure
	tableContainer.innerHTML = \`
		<div style="padding: 20px; text-align: center; color: #666;">
			<p>📊 Detailed warehouse analysis data will be displayed here</p>
			<p>Current warehouse: \${window.selectedMainWarehouse || 'All Warehouses'}</p>
		</div>
	\`;
}

function showError(message) {
	const errorContainer = document.getElementById('errorContainer');
	errorContainer.innerHTML = \`<strong>Error:</strong> \${message}\`;
	errorContainer.style.display = 'block';
}

function showDashboardSettings() {
	frappe.msgprint({
		title: 'Dashboard Settings',
		message: \`
			<div style="padding: 15px;">
				<h4>🔧 Dashboard Configuration</h4>
				<p>Configure your warehouse dashboard preferences:</p>
				<ul style="text-align: left; margin: 15px 0;">
					<li>Auto-refresh interval</li>
					<li>Default warehouse selection</li>
					<li>Notification preferences</li>
					<li>Export settings</li>
				</ul>
				<p style="color: #666; font-size: 0.9rem;">
					Settings panel coming soon...
				</p>
			</div>
		\`
	});
}

// Auto-refresh every 5 minutes
setInterval(() => {
	if (typeof loadDashboardData === 'function') {
		loadDashboardData();
	}
}, 5 * 60 * 1000);