frappe.pages["process-map-builder"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("process-map-builder"),
		single_column: true,
	});
};

frappe.pages["process-map-builder"].on_page_show = function (wrapper) {
	load_desk_page(wrapper);
};

function load_desk_page(wrapper) {
	let $parent = $(wrapper).find(".layout-main-section");
	$parent.empty();

	frappe.require("process_map_builder.bundle.jsx").then(() => {
		frappe.process_map_builder = new frappe.ui.ProcessMapBuilder({
			wrapper: $parent,
			page: wrapper.page,
		});
	});
}