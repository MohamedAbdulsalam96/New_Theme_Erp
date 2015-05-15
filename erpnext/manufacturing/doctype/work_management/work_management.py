# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import add_days, cint, cstr, date_diff, flt, getdate, nowdate, \
	get_first_day, get_last_day

from frappe.model.document import Document

class WorkManagement(Document):
	def get_invoice_details(self, type_of_request=None):
		if type_of_request != 'more':
			self.set('production_details', [])
			self.offset = 0
			
		sales_invoices = self.get_invoice(self.sales_invoice_no)
		if sales_invoices:
			for si_no in sales_invoices:				
				si = self.append('production_details', {})
				self.create_invoice_bundle(si_no, si)
			self.offset = len(self.get('production_details'))
			offset_no =self.offset
			return{
				   'offset':offset_no
				}

	def get_invoice(self, invoice_no=None):
		branch_cond = ''
		cond = "and 1=1"
		if invoice_no and not self.services:
			cond = "and pdd.sales_invoice_no='%s'"%(invoice_no)
		elif self.services and not invoice_no:
			cond = "and pdd.tailoring_service='%s'"%(self.services)
		elif self.services and invoice_no:
			cond = "and pdd.sales_invoice_no='%s' and pdd.tailoring_service='%s'"%(invoice_no, self.services)
		branch = frappe.db.get_value('User',frappe.session.user,'branch')
		if branch:
			branch_cond = "and pl.branch ='%s' "%(branch)
		return frappe.db.sql("""SELECT
								    distinct(pdd.sales_invoice_no),
								    pdd.article_code,
								    pdd.article_qty,
								    pdd.work_order,
								    pdd.stock_entry,
								    pdd.name,
								    pdd.fabric_qty,
								    pdd.fabric_code,
								    pdd.serial_no,
								    pdd.size,
								    pdd.status,
								    pdd.trial_no

								FROM
								    `tabProduction Dashboard Details` pdd
								JOIN
								    `tabWork Order` wo
								ON
								    pdd.work_order = wo.name
								JOIN
								    `tabProcess Log` pl
								ON
								    pl.parent = pdd.name
								WHERE
								    wo.status = 'Release'
								{0}  {1}
								ORDER BY
								    pdd.creation DESC limit 10 {2}""".format(branch_cond,cond,self.get_offset()),as_dict=1)

	def create_invoice_bundle(self, invoice_detail, si):
		color = {'Completed':'green','Pending':'red', 'Trial':'#1F8C83'}
		value = '<h style="color:red">Pending</h>'
		si.sales_invoice = invoice_detail.sales_invoice_no
		si.customer_name = frappe.db.get_value('Sales Invoice', si.sales_invoice, 'customer_name')
		si.article_code = invoice_detail.article_code
		si.article_qty = invoice_detail.article_qty
		si.work_order = invoice_detail.work_order
		si.stock_entry = invoice_detail.stock_entry
		si.process_allotment = invoice_detail.name
		si.actual_qty = invoice_detail.fabric_qty
		si.fabric_code = invoice_detail.fabric_code
		si.serial_no = invoice_detail.serial_no
		si.size = invoice_detail.size
		if invoice_detail.status == 'Completed':
			value = '<h style="color:%s">%s</h>'%(color.get(invoice_detail.status), invoice_detail.status)
		elif cint(invoice_detail.trial_no) > 0:
			value = '<h style="color:%s">Ready For %s %s</h>'%(color.get(invoice_detail.status), invoice_detail.status, invoice_detail.trial_no)
		si.process_status = value
		si.cut_order_status ='<h style="color:%s">%s</h>'%(color.get(invoice_detail.cut_order_status), invoice_detail.cut_order_status)

	# def save_data(self, args):
	# 	for d in self.get('production_details'):
	# 		if cint(args.get('select')) ==1 and cint(d.idx)==cint(args.get('idx')):
	# 			self.save(ignore_permissions=True)
	# 		elif cint(args.get('select')) ==0 and cint(d.idx)==cint(args.get('idx')):
	# 			self.clear_data(args.get('sales_invoice'), args.get('article_code'))

	# def clear_data(self, inv_no=None, item_code=None):
	# 	self.get_invoice_details()
	# 	cond = "1=1"
	# 	if inv_no and item_code:
	# 		cond = "sales_invoice= '%s' and article_code='%s'"%(inv_no, item_code)
	# 	frappe.db.sql("delete from `tabProduction Details` where %s"%(cond))


	def get_offset(self):
		offset = ''
		if self.offset:
			offset = "offset %s"%(self.offset)
		return offset
