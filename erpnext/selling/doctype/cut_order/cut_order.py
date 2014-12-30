# Copyright (c) 2013, IndictransTech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, nowtime, nowdate
from frappe.model.document import Document
from tools.tools_management.custom_methods import get_fabric_details, get_warehouse, get_branch, get_series, get_fabric_details
from tools.custom_data_methods import get_user_branch, get_branch_cost_center, get_branch_warehouse, update_serial_no, find_next_process

class CutOrderDashboard(Document):
	def get_invoice_details(self):
		self.set('cut_order_item', [])
		for co in self.get_cut_order_details():
			coi = self.append('cut_order_item', {})
			coi.invoice_no = co['invoice_no']
			coi.article_code = co['article_code']
			coi.fabric_code = co['fabric_code']
			coi.fabric_qty = co['qty']
			coi.actual_site = co['actual_site']
			coi.fabric_site = co['fabric_site']
			coi.cut_order_id = co['name']

	def get_cut_order_details(self):
		branch = get_user_branch()
		cond = "1=1"
		if branch:
			cond = "fabric_site = '%s'"%(branch)
		return frappe.db.sql("""select invoice_no, article_code, 
				fabric_code, qty, 
				article_serial_no, 
				actual_site, fabric_site, name from `tabCut Order` 
			where ifnull(docstatus, 0) not in (1,2) and %s order by invoice_no desc"""%(cond), as_dict=1)

	def cut_order(self):
		issue_list, out_list = [], []
		for item in self.cut_order_item:
			if cint(item.select) == 1:
				if item.actual_site == item.fabric_site:
					self.make_material_issue_list(item, issue_list)
				else:
					self.make_material_out_list(item, out_list)
				self.submit_cut_order(item)
		self.make_stock_transfer(out_list)
		self.update_fabric_stock(issue_list)
		frappe.msgprint("Stock Entry for cutted fabric has drafted")

	def make_material_issue_list(self, item, issue_list):
		frappe.errprint(item.invoice_no)
		issue_list.append([item.invoice_no, item.article_code, 
				item.fabric_code, item.fabric_qty, 
				item.actual_site, item.fabric_site])


	def make_material_out_list(self, item, out_list):
		out_list.append([item.invoice_no, item.article_code, 
				item.fabric_code, item.fabric_qty, 
				item.actual_site, item.fabric_site])

	def make_stock_transfer(self, out_list):		
		se = frappe.new_doc('Stock Entry')
		se.naming_series =  get_series("Stock Entry")
		se.purpose_type = 'Material Out'
		se.purpose = 'Material Issue'
		se.branch = frappe.db.get_value('User', frappe.session.user, 'branch')
		se.posting_date = nowdate()
		se.posting_time = nowtime().split('.')[0]
		
		for item in out_list:
			frappe.errprint(item)
			fab_details = get_fabric_details(item[2])
			sed = se.append('mtn_details', {})
			sed.invoice_no = item[0]
			sed.s_warehouse = get_warehouse(item[4])
			sed.target_branch = get_branch(item[5])
			sed.item_code = item[2]
			sed.item_name = fab_details.get('item_name')
			sed.description = fab_details.get('description')
			sed.qty = cint(item[3])
			sed.stock_uom = fab_details.get('stock_uom')
			sed.uom = fab_details.get('stock_uom')
			sed.conversion_factor = 1
			sed.incoming_rate = 0.0
			sed.transfet_qty = cint(item[3]) * 1

		se.save()

	def update_fabric_stock(self, issue_list):pass

	def submit_cut_order(self, item):
		co = frappe.get_doc('Cut Order', item.cut_order_id)
		co.submit()