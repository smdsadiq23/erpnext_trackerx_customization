frappe.pages['warehouse-capacity-d'].on_page_load = function(wrapper) {
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
						<strong>Required permissions:</strong><br>
						• Stock User, Stock Manager, Material Manager, or Warehouse Manager role<br>
						• Appropriate company permissions
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
			if (window.loadDashboardData) {
				window.loadDashboardData();
			}
		}, true);

		// Add settings button
		page.add_menu_item(__('Dashboard Settings'), function() {
			showDashboardSettings();
		}, true);

		// Add permission info button
		page.add_menu_item(__('Permission Info'), function() {
			showUserPermissionInfo();
		}, true);

		// Insert the dashboard HTML content
		console.log('Setting page HTML...');
		const html = getWarehouseCapacityHTML();
		console.log('Generated HTML length:', html.length);
		$(page.body).html(html);
		console.log('Page body HTML set, checking elements...');

		// Check if elements exist after HTML insertion
		setTimeout(() => {
			console.log('cardsContainer exists after HTML set:', !!document.getElementById('cardsContainer'));
			console.log('refreshBtn exists:', !!document.getElementById('refreshBtn'));
			console.log('loadingIndicator exists:', !!document.getElementById('loadingIndicator'));
		}, 100);

		// Initialize dashboard functionality
		initializeWarehouseCapacityApp();
	}

	function showUserPermissionInfo() {
		frappe.call({
			method: 'erpnext_trackerx_customization.api.warehouse_permissions.get_user_permission_info',
			callback: function(r) {
				if (r.message) {
					const userInfo = r.message;
					const permissionDetails = `
						<div style="text-align: left; padding: 20px;">
							<h4>👤 User Permission Details</h4>
							<table style="width: 100%; margin-top: 15px;">
								<tr><td><strong>User:</strong></td><td>${userInfo.user || 'Unknown'}</td></tr>
								<tr><td><strong>Is System Manager:</strong></td><td>${userInfo.is_system_manager ? '✅ Yes' : '❌ No'}</td></tr>
								<tr><td><strong>Default Company:</strong></td><td>${userInfo.default_company || 'Not set'}</td></tr>
								<tr><td><strong>Accessible Companies:</strong></td><td>${userInfo.permitted_companies_count || 0}</td></tr>
								<tr><td><strong>User Roles:</strong></td><td>${userInfo.roles ? userInfo.roles.slice(0,8).join(', ') + (userInfo.roles.length > 8 ? '...' : '') : 'None'}</td></tr>
							</table>
							${userInfo.permitted_companies && userInfo.permitted_companies.length > 0 ?
								`<h5 style="margin-top: 20px;">🏢 Permitted Companies:</h5>
								<ul style="margin-top: 10px;">
								${userInfo.permitted_companies.slice(0,10).map(comp => `<li>${comp}</li>`).join('')}
								${userInfo.permitted_companies.length > 10 ? `<li><em>... and ${userInfo.permitted_companies.length - 10} more</em></li>` : ''}
								</ul>` : ''
							}
						</div>
					`;

					frappe.msgprint({
						title: 'User Permission Information',
						message: permissionDetails
					});
				}
			}
		});
	}

	function getWarehouseCapacityHTML() {
		return `
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
					display: grid !important;
					grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)) !important;
					gap: 20px !important;
					margin-bottom: 30px !important;
					width: 100% !important;
					visibility: visible !important;
				}

				.card {
					background: white !important;
					padding: 25px !important;
					border-radius: 12px !important;
					box-shadow: 0 2px 10px rgba(0,0,0,0.1) !important;
					border-left: 4px solid #96be37 !important;
					transition: transform 0.2s ease, box-shadow 0.2s ease !important;
					display: block !important;
					visibility: visible !important;
					opacity: 1 !important;
					height: auto !important;
					min-height: 150px !important;
				}

				.card:hover {
					transform: translateY(-2px);
					box-shadow: 0 4px 20px rgba(0,0,0,0.15);
				}

				.card-title {
					font-size: 1rem !important;
					font-weight: 600 !important;
					color: #333 !important;
					margin: 0 !important;
					display: block !important;
					visibility: visible !important;
				}

				.card-value {
					font-size: 2.5rem !important;
					font-weight: bold !important;
					color: #333 !important;
					margin: 10px 0 !important;
					display: block !important;
					visibility: visible !important;
				}

				.card-description {
					color: #666 !important;
					font-size: 0.9rem !important;
					display: block !important;
					visibility: visible !important;
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
					<p>Real-time monitoring and analytics for optimized warehouse management - Secure Access</p>
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
						<p style="color: #666; margin-top: 10px;">
							Data filtered based on your company permissions and role access
						</p>
					</div>
					<div id="tableContent">
						<!-- Table content will be populated here -->
					</div>
				</div>
			</div>
		`;
	}

	function initializeWarehouseCapacityApp() {
		console.log('initializeWarehouseCapacityApp called');
		// Dashboard variables
		window.dashboardData = null;
		window.selectedMainWarehouse = null;
		window.availableWarehouses = [];

		// Show permission info
		console.log('Calling showPermissionInfo...');
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

					if (permissionBar && userInfoSpan && companyInfoSpan && accessInfoSpan && userBadge) {
						userInfoSpan.textContent = `👤 ${userInfo.user || 'Unknown User'}`;
						companyInfoSpan.textContent = `🏢 ${userInfo.permitted_companies_count || 0} companies accessible`;

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

		if (!dropdown || !selector) return;

		if (window.availableWarehouses.length === 0) {
			dropdown.innerHTML = '<option value="">No warehouses available</option>';
			return;
		}

		// Add "All Warehouses" option
		let options = '<option value="">All Warehouses</option>';

		// Add individual warehouses
		options += window.availableWarehouses.map(warehouse =>
			`<option value="${warehouse.name}" ${warehouse.name === window.selectedMainWarehouse ? 'selected' : ''}>
				${warehouse.warehouse_name || warehouse.name}
			</option>`
		).join('');

		dropdown.innerHTML = options;
		selector.style.display = 'block';
	}

	window.changeSelectedWarehouse = function() {
		const dropdown = document.getElementById('warehouseDropdown');
		const newWarehouse = dropdown.value;

		if (newWarehouse !== window.selectedMainWarehouse) {
			window.selectedMainWarehouse = newWarehouse;
			loadDashboardData();
		}
	};

	window.loadDashboardData = async function() {
		const refreshBtn = document.getElementById('refreshBtn');
		const loadingIndicator = document.getElementById('loadingIndicator');
		const cardsContainer = document.getElementById('cardsContainer');
		const errorContainer = document.getElementById('errorContainer');

		if (!refreshBtn || !loadingIndicator) return;

		// Show loading state
		refreshBtn.disabled = true;
		refreshBtn.textContent = '⏳ Loading...';
		loadingIndicator.style.display = 'flex';
		if (cardsContainer) cardsContainer.style.display = 'none';
		if (errorContainer) errorContainer.style.display = 'none';

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

			console.log('Dashboard API Response:', response);
			console.log('Response message:', response.message);

			if (response.message && response.message.success) {
				window.dashboardData = response.message;
				console.log('Dashboard data set to:', window.dashboardData);
				renderDashboard();
			} else {
				console.error('API call failed:', response.message);
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
	};

	function renderDashboard() {
		console.log('renderDashboard called with window.dashboardData:', window.dashboardData);

		if (!window.dashboardData || !window.dashboardData.success) {
			console.error('Invalid dashboard data - success check failed');
			console.log('dashboardData exists:', !!window.dashboardData);
			console.log('dashboardData.success:', window.dashboardData?.success);
			showError('Invalid dashboard data received');
			return;
		}

		const data = window.dashboardData.data;
		console.log('Extracted data for rendering:', data);
		renderCards(data);
		renderTable(data);

		const cardsContainer = document.getElementById('cardsContainer');
		const tableContainer = document.getElementById('enhancedTableContainer');

		console.log('Setting containers to visible...');
		console.log('cardsContainer found for display:', !!cardsContainer);
		if (cardsContainer) {
			console.log('Setting cardsContainer display to grid');
			cardsContainer.style.display = 'grid';
			console.log('cardsContainer display is now:', cardsContainer.style.display);
		}
		if (tableContainer) {
			console.log('Setting tableContainer display to block');
			tableContainer.style.display = 'block';
		}
	}

	function renderCards(data) {
		console.log('renderCards called with data:', data);
		console.log('Looking for cardsContainer...');
		const container = document.getElementById('cardsContainer');
		console.log('cardsContainer found:', !!container);
		if (!container) {
			console.error('cardsContainer not found in DOM');
			console.log('Available elements with ID:', document.querySelectorAll('[id]'));
			return;
		}

		console.log('Setting cardsContainer innerHTML...');
		container.innerHTML = `
			<!-- Total Warehouses Card -->
			<div class="card">
				<div class="card-header">
					<h3 class="card-title">🏭 Total Warehouses</h3>
				</div>
				<div class="card-value">${data.total_warehouses.value}</div>
				<div class="card-change ${data.total_warehouses.change >= 0 ? 'positive' : 'negative'}">
					${data.total_warehouses.change >= 0 ? '↗' : '↘'} ${Math.abs(data.total_warehouses.change)}
				</div>
				<div class="card-description">${data.total_warehouses.description}</div>
			</div>

			<!-- Overall Utilization Card -->
			<div class="card">
				<div class="card-header">
					<h3 class="card-title">📊 Overall Utilization</h3>
				</div>
				<div class="card-value">${data.overall_utilization.value}%</div>
				<div class="card-change ${data.overall_utilization.change >= 0 ? 'positive' : 'negative'}">
					${data.overall_utilization.change >= 0 ? '↗' : '↘'} ${Math.abs(data.overall_utilization.change)}%
				</div>
				<div class="card-description">${data.overall_utilization.description}</div>
			</div>

			<!-- Critical Alerts Card -->
			<div class="card">
				<div class="card-header">
					<h3 class="card-title">⚠️ Critical Alerts</h3>
				</div>
				<div class="card-value">${data.critical_alerts.value}</div>
				<div class="card-change ${data.critical_alerts.change >= 0 ? 'negative' : 'positive'}">
					${data.critical_alerts.change >= 0 ? '↗' : '↘'} ${Math.abs(data.critical_alerts.change)}
				</div>
				<div class="card-description">${data.critical_alerts.description}</div>
			</div>

			<!-- Available Capacity Card -->
			<div class="card">
				<div class="card-header">
					<h3 class="card-title">📈 Available Capacity</h3>
				</div>
				<div class="card-value">${data.available_capacity.value}</div>
				<div class="card-change ${data.available_capacity.change >= 0 ? 'positive' : 'negative'}">
					${data.available_capacity.change >= 0 ? '↗' : '↘'} ${Math.abs(data.available_capacity.change)}
				</div>
				<div class="card-description">${data.available_capacity.description}</div>
			</div>
		`;

		console.log('renderCards completed. Container innerHTML length:', container.innerHTML.length);
		console.log('Container children count:', container.children.length);
	}

	function renderTable(data) {
		console.log('renderTable called with data:', data);
		const tableContainer = document.getElementById('tableContent');
		if (!tableContainer) {
			console.error('tableContent container not found');
			return;
		}

		// Show loading state
		tableContainer.innerHTML = `
			<div style="padding: 20px; text-align: center; color: #666;">
				<div>⏳ Loading warehouse table data...</div>
			</div>
		`;

		// Fetch detailed warehouse data
		const args = {};
		if (window.selectedMainWarehouse) {
			args.main_warehouse = window.selectedMainWarehouse;
		}

		frappe.call({
			method: 'erpnext_trackerx_customization.api.warehouse_capacity_dashboard.get_warehouse_tree_data',
			args: args,
			callback: function(r) {
				console.log('Warehouse tree data response:', r);
				if (r.message && r.message.success) {
					displayWarehouseTree(r.message, tableContainer);
				} else {
					showTableError(tableContainer, r.message?.error || 'Failed to load warehouse data');
				}
			},
			error: function(e) {
				console.error('Error fetching warehouse data:', e);
				showTableError(tableContainer, 'Error loading warehouse data');
			}
		});
	}

	function displayWarehouseTree(data, container) {
		console.log('Displaying warehouse tree with data:', data);
		const warehouseTree = data.warehouse_tree || [];

		if (warehouseTree.length === 0) {
			container.innerHTML = `
				<div style="padding: 20px; text-align: center; color: #666;">
					<div style="background: #fff3cd; padding: 20px; border-radius: 8px; border: 1px solid #ffeaa7;">
						<h4 style="color: #856404;">📊 No Warehouse Data Found</h4>
						<p>No warehouses found matching your selection criteria.</p>
						<p><strong>Current Selection:</strong> ${window.selectedMainWarehouse || 'All Warehouses'}</p>
					</div>
				</div>
			`;
			return;
		}

		// Count total warehouses in tree
		function countWarehouses(tree) {
			let count = 0;
			tree.forEach(node => {
				count++;
				if (node.children) {
					count += countWarehouses(node.children);
				}
			});
			return count;
		}

		const totalWarehouses = countWarehouses(warehouseTree);

		// Create tree HTML with search and filtering
		let treeHTML = `
			<style>
				.tree-container { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
				.tree-node { margin: 2px 0; }
				.tree-item {
					display: flex;
					align-items: center;
					padding: 8px 12px;
					border-radius: 6px;
					cursor: pointer;
					transition: all 0.2s ease;
				}
				.tree-item:hover { background: #f8f9fa; }
				.tree-toggle {
					width: 20px;
					height: 20px;
					margin-right: 8px;
					cursor: pointer;
					border: none;
					background: none;
					color: #666;
					font-size: 12px;
				}
				.tree-icon { margin-right: 8px; font-size: 16px; }
				.tree-name { font-weight: 500; color: #333; margin-right: 10px; }
				.tree-info { font-size: 0.85rem; color: #666; margin-left: auto; }
				.tree-children { margin-left: 20px; display: none; }
				.tree-children.expanded { display: block; }
				.status-critical { color: #dc3545 !important; font-weight: bold; }
				.status-warning { color: #ffc107 !important; font-weight: bold; }
				.status-healthy { color: #28a745 !important; }
				.status-normal { color: #666 !important; }
				.item-node { background: #f8f9fa; margin: 2px 0; border-radius: 4px; border-left: 3px solid #007bff; }
				.item-details { font-size: 0.8rem; color: #555; margin-left: 28px; padding: 4px 8px; }
				.search-container {
					background: #f8f9fa;
					padding: 15px;
					border-radius: 8px;
					margin-bottom: 15px;
					border: 1px solid #dee2e6;
				}
				.search-input {
					width: 100%;
					padding: 10px 12px;
					border: 1px solid #ced4da;
					border-radius: 6px;
					font-size: 14px;
					margin-bottom: 10px;
				}
				.filter-buttons {
					display: flex;
					gap: 10px;
					flex-wrap: wrap;
				}
				.filter-btn {
					padding: 6px 12px;
					border: 1px solid #007bff;
					background: white;
					color: #007bff;
					border-radius: 4px;
					cursor: pointer;
					font-size: 0.85rem;
				}
				.filter-btn.active {
					background: #007bff;
					color: white;
				}
				.items-loading {
					color: #666;
					font-style: italic;
					margin-left: 28px;
					padding: 4px 8px;
				}
			</style>
			<div style="background: #e8f5e8; padding: 15px; border-radius: 8px; border: 1px solid #4caf50; margin-bottom: 20px;">
				<p style="color: #2c5530; margin: 0;">
					✅ <strong>Secure Access Confirmed</strong><br>
					Hierarchical warehouse structure with ${totalWarehouses} warehouses and item details
				</p>
			</div>

			<!-- Search and Filter Section -->
			<div class="search-container">
				<input type="text" id="itemSearchInput" class="search-input" placeholder="🔍 Search items by name, code, or description..." oninput="filterItems()">
				<div class="filter-buttons">
					<button class="filter-btn active" onclick="setItemFilter('all')">All Items</button>
					<button class="filter-btn" onclick="setItemFilter('Yarns')">Yarns</button>
					<button class="filter-btn" onclick="setItemFilter('Fabrics')">Fabrics</button>
					<button class="filter-btn" onclick="setItemFilter('Accessories')">Accessories</button>
					<button class="filter-btn" onclick="setItemFilter('high-value')">High Value (>₹1000)</button>
					<button class="filter-btn" onclick="setItemFilter('out-of-stock')">Out of Stock</button>
				</div>
			</div>

			<div class="tree-container" style="background: white; border-radius: 8px; padding: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
		`;

		function renderTreeNode(node, level = 0) {
			const hasChildren = node.children && node.children.length > 0;
			const indent = level * 15;

			// Determine status and icon
			const utilization = node.hierarchical_utilization_percent || 0;
			const capacity = node.hierarchical_capacity || 0;
			const currentStock = node.hierarchical_current_stock || 0;

			let statusIcon = '📁';
			let statusClass = 'status-normal';
			let statusText = 'Group';

			if (!hasChildren) {
				statusIcon = '📦';
				statusText = node.hierarchical_status || 'Normal';

				if (utilization > 95) {
					statusClass = 'status-critical';
					statusIcon = '🚨';
				} else if (utilization > 80) {
					statusClass = 'status-warning';
					statusIcon = '⚠️';
				} else if (capacity > 0) {
					statusClass = 'status-healthy';
					statusIcon = '✅';
				}
			}

			const toggleIcon = hasChildren ? '▶' : '·';
			const capacityInfo = capacity > 0 ? `${capacity} ${node.hierarchical_capacity_unit || 'Units'}` : 'No Capacity';
			const stockInfo = currentStock > 0 ? `Stock: ${currentStock}` : '';
			const utilizationInfo = capacity > 0 ? `${utilization.toFixed(1)}%` : '';

			// Add items button for individual warehouses (not groups)
			const itemsButton = !hasChildren && node.is_group === 0 ?
				`<button class="filter-btn" style="margin-left: 10px; padding: 4px 8px; font-size: 0.75rem;" onclick="loadWarehouseItems('${node.warehouse}', this)">📦 Items</button>` : '';

			let nodeHTML = `
				<div class="tree-node" style="margin-left: ${indent}px;">
					<div class="tree-item" data-warehouse="${node.warehouse}">
						${hasChildren ?
							`<button class="tree-toggle" onclick="toggleTreeNode(this)">${toggleIcon}</button>` :
							`<span class="tree-toggle">·</span>`
						}
						<span class="tree-icon">${statusIcon}</span>
						<span class="tree-name">${node.warehouse_name || node.warehouse}</span>
						<span class="tree-info ${statusClass}">
							${capacityInfo} ${stockInfo} ${utilizationInfo ? `| ${utilizationInfo}` : ''} | ${statusText}
						</span>
						${itemsButton}
					</div>
					<div class="items-container" id="items-${node.warehouse}" style="display: none;"></div>
			`;

			if (hasChildren) {
				nodeHTML += `<div class="tree-children">`;
				node.children.forEach(child => {
					nodeHTML += renderTreeNode(child, level + 1);
				});
				nodeHTML += `</div>`;
			}

			nodeHTML += `</div>`;
			return nodeHTML;
		}

		warehouseTree.forEach(rootNode => {
			treeHTML += renderTreeNode(rootNode);
		});

		treeHTML += `
			</div>
			<div style="margin-top: 15px; padding: 10px; background: #f8f9fa; border-radius: 6px; font-size: 0.9rem; color: #666;">
				<strong>Tree View:</strong> ${totalWarehouses} warehouses in hierarchical structure |
				<strong>Selection:</strong> ${window.selectedMainWarehouse || 'All Warehouses'} |
				<strong>Legend:</strong> 📁 Group | 📦 Warehouse | 🚨 Critical | ⚠️ Warning | ✅ Healthy
			</div>
		`;

		container.innerHTML = treeHTML;

		// Add tree toggle functionality
		window.toggleTreeNode = function(button) {
			const treeNode = button.closest('.tree-node');
			const children = treeNode.querySelector('.tree-children');

			if (children) {
				const isExpanded = children.classList.contains('expanded');
				if (isExpanded) {
					children.classList.remove('expanded');
					button.textContent = '▶';
				} else {
					children.classList.add('expanded');
					button.textContent = '▼';
				}
			}
		};

		// Auto-expand first level
		container.querySelectorAll('.tree-toggle').forEach((toggle, index) => {
			if (index < 5) { // Expand first 5 root nodes
				const treeNode = toggle.closest('.tree-node');
				const children = treeNode.querySelector('.tree-children');
				if (children) {
					children.classList.add('expanded');
					toggle.textContent = '▼';
				}
			}
		});

		// Initialize search and filter functionality
		initializeItemSearch();
	}

	function initializeItemSearch() {
		window.currentItemFilter = 'all';
		window.searchTerm = '';
		window.warehouseItems = {}; // Cache for loaded items

		// Load warehouse items function
		window.loadWarehouseItems = function(warehouse, button) {
			const itemsContainer = document.getElementById(`items-${warehouse}`);
			if (!itemsContainer) return;

			// Toggle visibility
			if (itemsContainer.style.display === 'block') {
				itemsContainer.style.display = 'none';
				button.textContent = '📦 Items';
				return;
			}

			// Show loading
			itemsContainer.style.display = 'block';
			itemsContainer.innerHTML = '<div class="items-loading">⏳ Loading items...</div>';
			button.textContent = '📦 Loading...';

			// Fetch items
			frappe.call({
				method: 'erpnext_trackerx_customization.api.warehouse_capacity_dashboard.get_warehouse_items_detail',
				args: { warehouse: warehouse },
				callback: function(r) {
					if (r.message && r.message.success) {
						window.warehouseItems[warehouse] = r.message.items || [];
						displayWarehouseItems(warehouse, r.message);
						button.textContent = '📦 Hide Items';
					} else {
						itemsContainer.innerHTML = '<div class="items-loading">❌ Failed to load items</div>';
						button.textContent = '📦 Retry';
					}
				},
				error: function() {
					itemsContainer.innerHTML = '<div class="items-loading">❌ Error loading items</div>';
					button.textContent = '📦 Retry';
				}
			});
		};

		// Filter items function
		window.setItemFilter = function(filter) {
			window.currentItemFilter = filter;

			// Update button states
			document.querySelectorAll('.filter-btn').forEach(btn => {
				btn.classList.remove('active');
			});
			event.target.classList.add('active');

			// Re-render all visible item lists
			Object.keys(window.warehouseItems).forEach(warehouse => {
				const itemsContainer = document.getElementById(`items-${warehouse}`);
				if (itemsContainer && itemsContainer.style.display === 'block') {
					displayWarehouseItems(warehouse, {
						items: window.warehouseItems[warehouse],
						warehouse: warehouse,
						total_items: window.warehouseItems[warehouse].length
					});
				}
			});
		};

		// Search items function
		window.filterItems = function() {
			window.searchTerm = document.getElementById('itemSearchInput').value.toLowerCase();

			// Re-render all visible item lists
			Object.keys(window.warehouseItems).forEach(warehouse => {
				const itemsContainer = document.getElementById(`items-${warehouse}`);
				if (itemsContainer && itemsContainer.style.display === 'block') {
					displayWarehouseItems(warehouse, {
						items: window.warehouseItems[warehouse],
						warehouse: warehouse,
						total_items: window.warehouseItems[warehouse].length
					});
				}
			});
		};
	}

	function displayWarehouseItems(warehouse, data) {
		const itemsContainer = document.getElementById(`items-${warehouse}`);
		if (!itemsContainer) return;

		const items = data.items || [];

		// Filter items based on current filter and search
		const filteredItems = items.filter(item => {
			// Search filter
			const matchesSearch = !window.searchTerm ||
				item.item_code.toLowerCase().includes(window.searchTerm) ||
				item.item_name.toLowerCase().includes(window.searchTerm) ||
				(item.description && item.description.toLowerCase().includes(window.searchTerm)) ||
				item.item_group.toLowerCase().includes(window.searchTerm);

			// Category filter
			let matchesCategory = true;
			switch(window.currentItemFilter) {
				case 'all':
					matchesCategory = true;
					break;
				case 'Yarns':
				case 'Fabrics':
				case 'Accessories':
					matchesCategory = item.item_group === window.currentItemFilter;
					break;
				case 'high-value':
					matchesCategory = item.total_value > 1000;
					break;
				case 'out-of-stock':
					matchesCategory = item.qty <= 0;
					break;
			}

			return matchesSearch && matchesCategory;
		});

		if (filteredItems.length === 0) {
			itemsContainer.innerHTML = `
				<div class="items-loading">
					📦 No items found matching current filter
					${window.searchTerm ? ` and search term "${window.searchTerm}"` : ''}
				</div>
			`;
			return;
		}

		// Generate items HTML
		let itemsHTML = `
			<div style="margin-left: 20px; border-left: 2px solid #dee2e6; padding-left: 15px;">
				<div style="font-size: 0.85rem; color: #666; margin-bottom: 8px; font-weight: 500;">
					📋 ${filteredItems.length} items found (Total value: ₹${items.reduce((sum, item) => sum + (item.total_value || 0), 0).toLocaleString()})
				</div>
		`;

		filteredItems.forEach(item => {
			const valueColor = item.total_value > 1000 ? '#28a745' : '#666';
			const qtyStatus = item.qty > 0 ? '✅' : '❌';

			itemsHTML += `
				<div class="item-node">
					<div style="display: flex; align-items: center; padding: 8px 12px;">
						<span style="margin-right: 8px;">${qtyStatus}</span>
						<div style="flex: 1;">
							<div style="font-weight: 500; color: #333; font-size: 0.9rem;">
								${item.item_name} <span style="color: #666; font-weight: normal;">(${item.item_code})</span>
							</div>
							<div style="font-size: 0.8rem; color: #666; margin-top: 2px;">
								<strong>Qty:</strong> ${item.qty} ${item.stock_uom} |
								<strong>Group:</strong> ${item.item_group} |
								<strong>Value:</strong> <span style="color: ${valueColor}; font-weight: 500;">₹${(item.total_value || 0).toLocaleString()}</span>
								${item.avg_rate > 0 ? ` | <strong>Rate:</strong> ₹${item.avg_rate}/${item.stock_uom}` : ''}
							</div>
						</div>
					</div>
				</div>
			`;
		});

		itemsHTML += '</div>';
		itemsContainer.innerHTML = itemsHTML;
	}

	function showTableError(container, errorMessage) {
		container.innerHTML = `
			<div style="padding: 20px; text-align: center; color: #666;">
				<div style="background: #f8d7da; padding: 20px; border-radius: 8px; border: 1px solid #f5c6cb; color: #721c24;">
					<h4>❌ Error Loading Table Data</h4>
					<p>${errorMessage}</p>
					<button onclick="loadDashboardData()" style="
						background: #dc3545; color: white; border: none; padding: 10px 20px;
						border-radius: 6px; cursor: pointer; margin-top: 10px;
					">🔄 Retry</button>
				</div>
			</div>
		`;
	}

	function showError(message) {
		const errorContainer = document.getElementById('errorContainer');
		if (errorContainer) {
			errorContainer.innerHTML = `<strong>Error:</strong> ${message}`;
			errorContainer.style.display = 'block';
		}
	}

	function showDashboardSettings() {
		frappe.msgprint({
			title: 'Dashboard Settings',
			message: `
				<div style="padding: 15px;">
					<h4>🔧 Dashboard Configuration</h4>
					<p>Configure your warehouse dashboard preferences:</p>
					<ul style="text-align: left; margin: 15px 0;">
						<li>Auto-refresh interval</li>
						<li>Default warehouse selection</li>
						<li>Notification preferences</li>
						<li>Export settings</li>
						<li>Permission-based filtering</li>
					</ul>
					<p style="color: #666; font-size: 0.9rem;">
						Settings panel coming soon...
					</p>
				</div>
			`
		});
	}

	// Auto-refresh every 5 minutes
	setInterval(() => {
		if (typeof window.loadDashboardData === 'function') {
			window.loadDashboardData();
		}
	}, 5 * 60 * 1000);
};