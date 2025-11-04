frappe.pages["production-tv-dashbo"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Production TV Dashboard"),
		single_column: true,
	});
};

frappe.pages["production-tv-dashbo"].on_page_show = function (wrapper) {
	load_desk_page(wrapper);
};

function load_desk_page(wrapper) {
	let $parent = $(wrapper).find(".layout-main-section");
	$parent.empty();

	frappe.require("production_tv_dashboard.bundle.jsx").then(() => {
		frappe.production_tv_dashboard = new frappe.ui.ProductionTVDashboard({
			wrapper: $parent,
			page: wrapper.page,
		});
	});
}