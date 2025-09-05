frappe.pages["warehouse-builder"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Warehouse Builder"),
		single_column: true,
	});
};

frappe.pages["warehouse-builder"].on_page_show = function (wrapper) {
	load_desk_page(wrapper);
};

function load_desk_page(wrapper) {
	let $parent = $(wrapper).find(".layout-main-section");
	$parent.empty();

	frappe.require("warehouse_builder.bundle.jsx").then(() => {
		frappe.warehouse_builder = new frappe.ui.WarehouseBuilder({
			wrapper: $parent,
			page: wrapper.page,
		});
	});
}