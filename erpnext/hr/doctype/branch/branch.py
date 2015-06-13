# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cstr

from frappe.model.document import Document

class Branch(Document):
	def validate(self):
		self.validate_for_duplicate_abbreviation()
		self.validate_for_abbreviations()
		
	def validate_for_abbreviations(self):
		my_dict = {'Branch Abbreviation':self.branch_abbreviation,'Stock Entry Bundle Abbreviation':self.stock_entry_bundle_abbreviation}
		special_char_list = ['@',"'",'"','$',"\\\\","\\",'#','%','*','&','^','.']
		for key in special_char_list:
			for field_label,value in my_dict.items():
				if key in cstr(value):
					frappe.throw(("Special Character {0} not allowed in {1} field").format(key,field_label))
				
	def validate_for_duplicate_abbreviation(self):
		abbr_dict = frappe.db.sql(""" select name,branch_abbreviation as br_abbr,stock_entry_bundle_abbreviation as ste_abbr from `tabBranch` where name != '%s' """%(self.name),as_dict=True)
		for row in abbr_dict:
			if cstr(row.get('br_abbr')) == cstr(self.branch_abbreviation) or cstr(row.get('br_abbr')) == cstr(self.stock_entry_bundle_abbreviation)  and cstr(row.get('br_abbr')):
				frappe.throw(" Abbreviation '{0}' is alreay used for Branch '{1}'' in Branch Abbreviation field.Please use another Abbreviation.".format(row.get('br_abbr'),row.get('name') ))
			if cstr(row.get('ste_abbr')) == cstr(self.branch_abbreviation) or cstr(row.get('ste_abbr')) == cstr(self.stock_entry_bundle_abbreviation) and cstr(row.get('ste_abbr')):
				frappe.throw(" Abbreviation '{0}' is alreay used for Branch '{1}' in Stock Entry Bundle Abbreviation field.Please use another Abbreviation.".format(row.get('ste_abbr'),row.get('name') ))	