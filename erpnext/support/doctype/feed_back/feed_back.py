# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class FeedBack(Document):
		def on_submit(self):
			from frappe.utils import get_url, cstr
			from frappe.utils.user import get_user_fullname
			full_name = get_user_fullname(frappe.session['user'])
			if full_name == "Guest":
				full_name = "Administrator"
			first_name = frappe.db.sql_list("""select first_name from `tabUser` where name='%s'"""%(self.raised_by))
			if first_name[0]!='Administrator' :
				msg="Dear "+self.raised_by+"!<br><br>Thank you for your precious feedback. <br><br>We are continuously working to improve the system ,your feedback is essential for improvement of system. <br><br>Regards,  <br>Team TailorPad."
				from frappe.utils.user import get_user_fullname
				from frappe.utils import get_url
				#sender = frappe.session.user not in STANDARD_USERS and frappe.session.user or None
				frappe.sendmail(recipients=self.raised_by, sender='info@tailorpad.com', subject='Thank you for Feed Back',message=msg)			
	


