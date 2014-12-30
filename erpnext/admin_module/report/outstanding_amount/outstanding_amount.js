// Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors and contributors
// For license information, please see license.txt
// Change label name Invoice List
frappe.query_reports["Outstanding Amount"] = {
	"filters": [
			{
			"fieldname":"branch",
			"label": __("Branch"),
			"fieldtype": "Link",
			"options": "Branch",
			"default": window.branch_name || ''
		},
		{
			"fieldname":"type_of_invoices",
			"label": __("Invoice Type"),
			"fieldtype": "Select",
			"options": "All\nOutstanding",
		},
	]
}
