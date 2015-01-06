from frappe import _

def get_data():
	return [
		{
			"label": _("Documents"),
			"icon": "icon-star",
			"items": [
				{
					"type": "page",
					"name": "admin-charts",
					"icon": "icon-dashboard",
					"label": _("Dashboard"),
					"link": "admin-charts",
					"description": _("Dashboard"),
				},
				{
					"type": "doctype",
					"label":"Authentication Approval",
					"icon" :"icon-check",	
					"name": "Admin Signature",
					"description": _("Admin Signature"),
				},
				{
					"type": "doctype",
					"name": "Pricing Rule",
					"label": _("Pricing Rule"),
					"description": _("List of offer"),
				},
				{
					"type":"page",
					"name":"report-template",
					"icon": "icon-book",
					"label": _("External Product Catalog"),
					"link": "report-template",
					"description": _("External Product Catalog"),
				},
				{
					"type": "page",
					"name": "production-forecast",
					"icon": "icon-bullseye",
					"label": _("Production Forecast"),
					"link": "production-forecast",
					"description": _("Production Forecast"),
				},
			]
		},
		
		{
			"label": _("Master"),
			"icon": "icon-suitcase",
			"items": [
				{
					"type": "doctype",
					"name": "Customer",
					"description": _("Customer Details"),
				},
				{
					"type": "doctype",
					"name": "Supplier",
					"description": _("Supplier Details"),
				},
				{
					"type": "doctype",
					"name": "Measurement",
					"label" : _("Measurement Fields"),
					"description": _("List of Measurement"),
				},
				{
					"type": "doctype",
					"name": "Measurement Template",
					"description": _("Collection of Measurement Fields"),
				},
				{
					"type": "doctype",
					"name": "Measurement Formula",
					"description": _("Measurement Formula"),
				},
				{
					"type": "doctype",
					"name": "Style",
					"description": _("Style"),
				},
				{
					"type": "doctype",
					"name": "Item",
					"description": _("All types of Product like Tailoring, Merchandise etc."),
				},
			]
		},
		{
			"label": _("Setup"),
			"icon": "icon-cog",
			"items": [
				{
					"type": "doctype",
					"name": "Company",
					"description": _("Company Details"),
				},
				{
					"type": "doctype",
					"name": "Branch",
					"description": _("Branch Details"),
				},
				{
					"type": "doctype",
					"name": "Service",
					"label": _("Services"),
					"description": _("List of Services"),
				},
				{
					"type": "doctype",
					"name": "Process",
					"description": _("List of Process"),
				},
				{
					"type": "doctype",
					"name": "Size",
					"description": _("Size"),
				},
				{
					"type": "doctype",
					"name": "Width",
					"description": _("Width"),
				},
				{
					"type": "doctype",
					"name": "Notification Settings",
					"label":"Notification Settings",
					"description": _("Notification Template"),
				},
			]
		},
		{
			"label": _("Main Reports"),
			"icon": "icon-list",
			"items": [
				{
					"type": "report",
					"is_query_report": True,
					"name": "Booked Orders",
					"doctype": "Sales Invoice",
					"icon":"icon-file-text"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Sales Details",
					"doctype": "Sales Invoice",
					"icon":"icon-file-text"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Outstanding Amount",
					"doctype": "Sales Invoice",
					"icon":"icon-file-text"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Extra Raw Material Used",
					"doctype": "Process Allotment",
					"icon":"icon-file-text"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Worker Details",
					"doctype": "Employee",
					"icon":"icon-file-text"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Customer History",
					"doctype": "Customer",
					"icon":"icon-file-text"
				},
			]
		},
		{
			"label": _("Standard Reports"),
			"icon": "icon-list",
			"items": [
				{
					"type": "report",
					"is_query_report": True,
					"name": "Items To Be Requested",
					"doctype": "Item",
					"icon":"icon-file-text"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Requested Items To Be Ordered",
					"doctype": "Material Request",
					"icon":"icon-file-text"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Material Requests for which Supplier Quotations are not created",
					"doctype": "Material Request",
					"icon":"icon-file-text"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Item-wise Purchase History",
					"doctype": "Item",
					"icon":"icon-file-text"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Item-wise Last Purchase Rate",
					"doctype": "Item",
					"icon":"icon-file-text"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Purchase Order Trends",
					"doctype": "Purchase Order",
					"icon":"icon-file-text"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Supplier Addresses and Contacts",
					"doctype": "Supplier",
					"icon":"icon-file-text"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Supplier-Wise Sales Analytics",
					"doctype": "Stock Ledger Entry",
					"icon":"icon-file-text"
				}
			]
		},
	]
