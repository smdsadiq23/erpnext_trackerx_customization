import * as React from "react";
import { App } from "./App";
import { createRoot } from "react-dom/client";

class ProductionTVDashboard {
	constructor({ page, wrapper }) {
		this.$wrapper = $(wrapper);
		this.page = page;
		this.react_instance = null;

		try {
			console.log('ProductionTVDashboard: Initializing dashboard...');
			this.init();
		} catch (error) {
			console.error('ProductionTVDashboard: Initialization error:', error);
			this.show_error('Failed to initialize dashboard: ' + error.message);
		}
	}

	init() {
		this.setup_page_actions();
		this.setup_app();
	}

	setup_page_actions() {
		try {
			console.log('ProductionTVDashboard: Setting up page actions...');

			this.config_btn = this.page.set_secondary_action(__("Configure"), () => {
				console.log('ProductionTVDashboard: Configure button clicked');
				this.toggle_config_panel();
			});

			this.fullscreen_btn = this.page.set_secondary_action(__("Fullscreen"), () => {
				console.log('ProductionTVDashboard: Fullscreen button clicked');
				this.toggle_fullscreen();
			});

			console.log('ProductionTVDashboard: Page actions set up successfully');
		} catch (error) {
			console.error('ProductionTVDashboard: Error setting up page actions:', error);
		}
	}

	setup_app() {
		try {
			console.log('ProductionTVDashboard: Setting up React app...');
			const container = this.$wrapper.get(0);

			if (!container) {
				throw new Error('Container element not found');
			}

			const root = createRoot(container);
			root.render(<App pageInstance={this} />);
			this.$production_tv_dashboard = root;

			console.log('ProductionTVDashboard: React app rendered successfully');
		} catch (error) {
			console.error('ProductionTVDashboard: Error setting up React app:', error);
			this.show_error('Failed to render dashboard: ' + error.message);
		}
	}

	toggle_config_panel() {
		try {
			console.log('ProductionTVDashboard: Toggling config panel, react_instance:', this.react_instance);
			if (this.react_instance && typeof this.react_instance.toggleConfig === 'function') {
				this.react_instance.toggleConfig();
			} else {
				console.warn('ProductionTVDashboard: React instance not ready or toggleConfig method not available');
			}
		} catch (error) {
			console.error('ProductionTVDashboard: Error toggling config panel:', error);
		}
	}

	toggle_fullscreen() {
		try {
			console.log('ProductionTVDashboard: Toggling fullscreen');
			if (document.fullscreenElement) {
				document.exitFullscreen();
			} else {
				this.$wrapper.get(0).requestFullscreen();
			}
		} catch (error) {
			console.error('ProductionTVDashboard: Error toggling fullscreen:', error);
		}
	}

	show_error(message) {
		this.$wrapper.html(`
			<div style="padding: 40px; text-align: center; color: #721c24; background: #f8d7da; border: 1px solid #f5c6cb; border-radius: 8px; margin: 20px;">
				<h3>Dashboard Error</h3>
				<p>${message}</p>
				<button onclick="location.reload()" style="padding: 8px 16px; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer;">
					Reload Page
				</button>
			</div>
		`);
	}
}

frappe.provide("frappe.ui");
frappe.ui.ProductionTVDashboard = ProductionTVDashboard;
export default ProductionTVDashboard;