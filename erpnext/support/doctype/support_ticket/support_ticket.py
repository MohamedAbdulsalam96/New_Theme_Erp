# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe

from erpnext.utilities.transaction_base import TransactionBase
from frappe.utils import now, extract_email_id
STANDARD_USERS = ("Guest", "Administrator")

class SupportTicket(TransactionBase):

	def get_sender(self, comm):
		return frappe.db.get_value('Support Email Settings',None,'support_email')

	def get_subject(self, comm):
		return '[' + self.name + '] ' + (comm.subject or 'No Subject Specified')

	def get_content(self, comm):
		signature = frappe.db.get_value('Support Email Settings',None,'support_signature')
		content = comm.content
		if signature:
			content += '<p>' + signature + '</p>'
		return content

	def get_portal_page(self):
		return "ticket"

	def validate(self):
		self.update_status()
		self.set_lead_contact(self.raised_by)

		if self.status == "Closed":
			from frappe.widgets.form.assign_to import clear
			clear(self.doctype, self.name)

	def on_update(self):
		self.send_email();

	def send_email(self):
		from frappe.utils.user import get_user_fullname
		from frappe.utils import get_url
		if not self.get("__islocal"):
			full_name = get_user_fullname(frappe.session['user'])
			if full_name == "Guest":
				full_name = "Administrator"

			first_name = frappe.db.sql_list("""select first_name from `tabUser` where name='%s'"""%(self.raised_by))
			if first_name[0]!='Administrator' :
				msg="Dear  "+first_name[0]+"!<br><br>Support Ticket is created successfully for '"+self.subject+"'<br><br>Your Support Ticket Number is '"+self.name+"' <br><br>Please note for further information. <br><br>Regards, <br>Team TailorPad."
				sender = frappe.session.user not in STANDARD_USERS and frappe.session.user or None
				frappe.sendmail(recipients=self.raised_by, sender=sender, subject=self.subject,	message=msg)



	def login(self):
		login_details = {'usr': 'Administrator', 'pwd': 'admin'}
		url = 'http://admin.tailorpad.com/api/method/login'
		headers = {'content-type': 'application/x-www-form-urlencoded'}
		response = requests.post(url, data='data='+json.dumps(login_details), headers=headers)

	def get_ticket_details(self):
		response = requests.get("""%(url)s/api/resource/Support Ticket/SUP-00001"""%{'url':get_url()})
		
		return eval(response.text).get('data')

	def call_del_keys(self, support_ticket):
		if support_ticket:
			if isinstance(support_ticket, dict):
				self.del_keys(support_ticket)

			if isinstance(support_ticket, list):
				for comm in support_ticket:
					self.del_keys(comm)

	def del_keys(self, support_ticket):
		del support_ticket['name']
		del support_ticket['creation']
		del support_ticket['modified']
		del support_ticket['company']

	def tenent_based_ticket_creation(self, support_ticket):
		url = 'http://admin.tailorpad.com/api/resource/Support Ticket'
		headers = {'content-type': 'application/x-www-form-urlencoded'}
		response = requests.post(url, data='data='+json.dumps(support_ticket), headers=headers)

	def set_lead_contact(self, email_id):
		import email.utils
		email_id = email.utils.parseaddr(email_id)
		if email_id:
			if not self.lead:
				self.lead = frappe.db.get_value("Lead", {"email_id": email_id})
			if not self.contact:
				self.contact = frappe.db.get_value("Contact", {"email_id": email_id})

			if not self.company:
				self.company = frappe.db.get_value("Lead", self.lead, "company") or \
					frappe.db.get_default("company")

	def update_status(self):
		status = frappe.db.get_value("Support Ticket", self.name, "status")
		if self.status!="Open" and status =="Open" and not self.first_responded_on:
			self.first_responded_on = now()
		if self.status=="Closed" and status !="Closed":
			self.resolution_date = now()
		if self.status=="Open" and status !="Open":
			# if no date, it should be set as None and not a blank string "", as per mysql strict config
			self.resolution_date = None

@frappe.whitelist()
def set_status(name, status):
	st = frappe.get_doc("Support Ticket", name)
	st.status = status
	st.save()

def auto_close_tickets():
	frappe.db.sql("""update `tabSupport Ticket` set status = 'Closed'
		where status = 'Replied'
		and date_sub(curdate(),interval 15 Day) > modified""")


def auto_close_tickets():
	frappe.db.sql("""update `tabSupport Ticket` set status = 'Closed'
		where status = 'Replied'
		and date_sub(curdate(),interval 15 Day) > modified""")

@frappe.whitelist()
def get_admin(name):
	admin = frappe.db.sql("select email_id_admin from tabUser  where name='administrator'")
	if admin and admin[0][0]:
		return admin[0][0]
	else:
	  	return frappe.session.get('user')


@frappe.whitelist()
def reenable(name):
	from frappe.utils import get_url, cstr
	if get_url()!='http://demo.tailorpad.com':
		from frappe.utils import get_url, cstr,add_months
		from frappe import msgprint, throw, _
		res = frappe.db.sql("select validity from `tabUser` where name='Administrator' and no_of_users >0")
		if res:
			res1 = frappe.db.sql("select validity_end_date from `tabUser` where '"+cstr(name)+"' and validity_end_date <CURDATE()")
			if res1:
				bc="update `tabUser` set validity_end_date=DATE_ADD((nowdate(), INTERVAL "+cstr(res[0][0])+" MONTH) where name = '"+cstr(name)+"'"
				frappe.db.sql(bc)
				frappe.db.sql("update `tabUser`set no_of_users=no_of_users-1  where name='Administrator'")
			else:
				ab="update `tabUser` set validity_end_date=DATE_ADD(validity_end_date,INTERVAL "+cstr(res[0][0])+" MONTH) where name = '"+cstr(name)+"' "
				frappe.db.sql(ab)
				frappe.db.sql("update `tabUser`set no_of_users=no_of_users-1  where name='Administrator'")
		else:
			frappe.throw(_("Your subscription plan expired .Please purchase an subscription plan and enable user."))
