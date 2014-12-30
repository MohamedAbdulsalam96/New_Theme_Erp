# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns, data = [], []
	cond = outstanding = "1=1"
	if filters:
		if filters.get('branch'):
			cond = "branch='%s'"%(filters.get('branch'))
		if filters.get('type_of_invoices') == 'Outstanding':
			outstanding = "ifnull(outstanding_amount,0)>0"
	data = frappe.db.sql("""select name, customer_name, posting_date, outstanding_amount, branch
		from `tabSales Invoice` where %s and %s and docstatus=1 order by posting_date desc"""%(cond, outstanding), as_list=1)
	columns = ["Sales Invoice:Link/Sales Invoice:150","Customer Name::150","Order Date:Date:90", "Outstanding Amount:Currency:110","Ordered Branch:Link/Branch:150"]
	return columns, data