# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import msgprint, _, throw
from frappe.model.document import Document

class NotificationSettings(Document):
	def validate(self):
		if len([d.name for d in self.get('notification_details') if not d.subject]) > 0:
			frappe.throw(_('Subject is mandatory field'))
