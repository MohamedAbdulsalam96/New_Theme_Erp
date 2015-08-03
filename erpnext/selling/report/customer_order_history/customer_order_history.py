# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
			"Invoice No.:Link/Sales Invoice:130","Booking Date:Date:80", 
			"Customer Id:Link/Customer:100", "Customer Name:Data:80",
			"Branch:Link/Branch:80", "Amount:Currency:100", 
			"Qty:Int:100", "Amount Due:Currency:120", "Paid Amount:Currency:120"
		]

def get_data(filters):
	cond = get_conditions(filters)
	return frappe.db.sql(''' select a.name, a.posting_date, a.customer, a.customer_name, a.branch , a.grand_total_export, 
		sum(b.qty), ifnull(a.outstanding_amount,0), ifnull(a.grand_total_export,0) - ifnull(a.outstanding_amount,0) from `tabSales Invoice` a, `tabSales Invoice Item` b
		where b.parent = a.name and a.status = 'Submitted' and a.posting_date between '{0}' and '{1}' {2} group by b.parent'''.format(filters.get('from_date'), filters.get('to_date'), cond), as_list=1)

def get_conditions(filters):
	conditions = []
	for key in filters:
		if filters.get(key) and key not in ['from_date', 'to_date']:
			conditions.append("a.%s = '%s'"%(key, filters.get(key)))

	return " and {}".format(" and ".join(conditions)) if conditions else ""

