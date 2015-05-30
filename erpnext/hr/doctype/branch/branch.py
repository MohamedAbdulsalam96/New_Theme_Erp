# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cstr

from frappe.model.document import Document

class Branch(Document):
	def validate(self):
		special_char_list = ['@',"'",'"','$',"\\\\","\\",'#','%','*','&','^']
		for key in special_char_list:
			if key in cstr(self.branch_abbreviation):
				frappe.throw(("Special Character {0} not allowed in Branch Abbreviation").format(key))