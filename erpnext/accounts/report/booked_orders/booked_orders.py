# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns, data = [], []
	data = frappe.db.sql(""" select     
			    si.name AS sales_invoice,
			    si.customer_name,
			    si.customer_group,
			    sii.item_name,
			    sii.delivery_date,
			    si.posting_date as booking_date,
			    tt.trial_no,
			    tt.trial_date,
			    case when  si.delivery_date <= current_date() then 'High Priority' when si.delivery_date between DATE_ADD(current_date(), INTERVAL 1 DAY) and DATE_ADD(current_date(), INTERVAL 2 DAY) then 'Priority 1' when si.delivery_date between DATE_ADD(current_date(), INTERVAL 3 DAY) and DATE_ADD(current_date(), INTERVAL 4 DAY) then 'Priority 2' else 'No hurry' end  as order_consideration
			from
			  `tabSales Invoice` si 
			inner join  `tabSales Invoice Item`  sii on si.name=sii.parent
			left join `tabProduction Dashboard Details` pd on pd.sales_invoice_no=si.name  and pd.fabric_code=sii.item_code
			left join `tabTrials` tm on tm.sales_invoice=si.name and tm.item_code=sii.item_code
			left join  `tabTrial Dates` tt on tt.parent=tm.name where tt.work_status = 'Open' and ifnull(tt.production_status, '') !='Closed'""")
	columns = get_columns()
	return columns, data

def get_columns():
	return [
			"Sales Invoice.:Link/Sales Invoice:80", "Customer Name::150",
			"Customer Group::110", "Item Name::120","Delivery Date:Date:120",
			"Posting Date:Date:80",  
			"Trial No::80", "Trial Date::100", 
			"Status::100"
		]