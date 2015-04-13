# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from tools.custom_data_methods import get_user_branch, get_branch_warehouse

class GiftVoucher(Document):
	
	def validate(self):
		self.validate_user_branch()
		self.make_stock_entry()
		pass


	def validate_user_branch(self):
		branch = get_user_branch()
		if not branch:
			frappe.throw(_("Current Session User must have Branch"))	

	def on_update(self):
		pass

	def on_submit(self):
		self.set_gift_voucher_link()
		pass		

	def set_gift_voucher_link(self):
		my_doc = frappe.get_doc('Serial No',self.serial_no)
		my_doc.gift_voucher_no = self.name
		my_doc.gift_voucher_amount = self.gift_voucher_amount
		my_doc.save(ignore_permissions=True)	

	def make_stock_entry(self):
		if not self.serial_no:
			ste = frappe.new_doc('Stock Entry')
	 		ste.purpose_type = 'Material Receipt'
	 		ste.purpose ='Material Receipt'
	 		ste.branch = get_user_branch()
	 		self.make_stock_entry_of_child(ste)
			ste.save(ignore_permissions=True)
			st = frappe.get_doc('Stock Entry', ste.name)
	 		st.submit()


	def make_stock_entry_of_child(self,obj):
		series = frappe.db.get_value('Item',self.gift_voucher_item_name, 'serial_no_series')
		if not series:
			series = str(self.gift_voucher_item_name) + '-.#####'
 		st = obj.append('mtn_details',{})
		st.t_warehouse = frappe.db.get_value('Branch',get_user_branch(),'warehouse')
		st.item_code = self.gift_voucher_item_name
		st.serial_no = make_autoname(series)
		st.item_name = frappe.db.get_value('Item', self.gift_voucher_item_name, 'item_name')
		st.description = frappe.db.get_value('Item', self.gift_voucher_item_name, 'description')
		st.uom = frappe.db.get_value('Item', self.gift_voucher_item_name, 'stock_uom')
		st.conversion_factor = 1
		st.qty = 1
		st.transfer_qty =  1
		st.incoming_rate = 1.00
		company = frappe.db.get_value('Global Defaults', None, 'default_company')
		st.expense_account = 'Stock Adjustment - '+frappe.db.get_value('Company', company, 'abbr')
		st.cost_center = 'Main - '+frappe.db.get_value('Company', company, 'abbr')
		self.serial_no = st.serial_no
 		return True







@frappe.whitelist()
def get_gift_voucher_item_name(item_code):
	if item_code:
		return frappe.db.get_value('Item',item_code,['item_name','redeem_amount'])
