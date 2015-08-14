from __future__ import unicode_literals
import frappe
from frappe.widgets.reportview import get_match_cond
from frappe.utils import add_days, cint, cstr, date_diff, rounded, flt, getdate, nowdate, \
	get_first_day, get_last_day,money_in_words, now
from frappe import _
from frappe.model.db_query import DatabaseQuery
from frappe import msgprint, _, throw
from frappe.model.naming import make_autoname
from tools.custom_data_methods import get_user_branch, get_branch_cost_center, get_branch_warehouse, find_next_process
from tools.tools_management.custom_methods import cut_order_generation
from erpnext.setup.doctype.sms_settings.sms_settings import send_sms
import re

# All schedular
def welcome_notification():
	notification = has_template('Welcome')
	if notification:
		args = make_WelcomeMSG()
		for d in args:
			customer_data = get_customer_details(d.customer)
			branch = get_customer_details(d.branch)
			data = cstr(notification.template).replace('branch_phone', branch.phone_no_1)
			data = re.sub('customer_name', d.customer, data)
			if notification.email_template and customer_data:
				send_mail(customer_data.email_id, data, notification.subject)
			if notification.sms_template and customer_data:
				send_sms([customer_data.phone],data)
			if customer_data and notification:
				update_status(d.name, 'Welcome')

def get_branch_details(branch):
	branch_data = frappe.db.get_value('Branch', branch, '*') if branch else ""
	return branch_data

def make_WelcomeMSG():
	args = frappe.db.sql(""" select customer , customer_name, name, branch from `tabSales Invoice` a
		where name not in (select document_name from `tabNotification Log` where type='Welcome') and docstatus=1 and posting_date between DATE_FORMAT(NOW() ,'%Y-%m-01') AND NOW()""", as_dict=1)

# call completion of item, STE, process
def self_service(customer, serial_no):
	notification = has_template('Self Service')
	serial_no_details = frappe.db.get_value('Serial No', serial_no, '*')
	if notification:
		customer_data = get_customer_details(customer)
		data = cstr(notification.template).replace('customer_name', customer).replace('item_name', serial_no_details.item_name)
		if notification.email_template and customer_data:
			send_mail(customer_data.email_id, data, notification.subject)
		if notification.sms_template and customer_data:
			send_sms([customer_data.phone],data)


# call on submission of dn
def delivery_note(doc, method):
	customer = doc.customer
	notification = has_template('Home Delivery')
	if notification:
		customer_data = get_customer_details(customer)
		data = cstr(notification.template).replace('customer_name', customer)
		if notification.email_template and customer_data:
			send_mail(customer_data.email_id, data, notification.subject)
		if notification.sms_template and customer_data:
			send_sms([customer_data.phone],data)

# call completion of item, STE, process
def trial(customer, item_name, invoice_no):
	notification = has_template('Trial')
	if notification:
		customer_data = get_customer_details(customer)
		data = cstr(notification.template).replace('customer_name', customer).replace('item_name', item_name).replace('order_no', invoice_no)
		if notification.email_template and customer_data:
			send_mail(customer_data.email_id, data, notification.subject)
		if notification.sms_template and customer_data:
			send_sms([customer_data.phone],data)

# every day
def outstanding_amount():
	notification = has_template('Outstanding Amount')
	if notification:
		args = frappe.db.sql("""select * from `tabSales Invoice` where ifnull(outstanding_amount, 0) > 0 and docstatus=1""", as_dict=1)
		if args:
			for d in args:
				customer_data = get_customer_details(d.customer)
				symbol = frappe.db.get_value('Currency', d.currency, 'symbol')
				data = cstr(notification.template).replace('customer_name', d.customer).replace('currency_symbol', symbol).replace('outstanding_amount', d.outstanding_amount).replace('order_no', d.name)
				if notification.email_template and customer_data:
					send_mail(customer_data.email_id, data, notification.subject)
				if notification.sms_template and customer_data:
					send_sms([customer_data.phone],data)

# every day
def late_delivery():
	notification = has_template('Late Delivery')
	if notification:
		args = frappe.db.sql("""select * from `tabSales Invoice Item` 
			where ifnull(delivery_date, 0) < SYSDATE() group by parent""", as_dict=1)
		if args:
			for d in args:
				customer = frappe.db.get_value('Sales Invoice', d.parent, 'customer')
				customer_data = get_customer_details(customer)
				data = cstr(notification.template).replace('customer_name', customer).replace('order_no', d.parent)
				if notification.email_template and customer_data:
					send_mail(customer_data.email_id, data, notification.subject)
				if notification.sms_template and customer_data:
					send_sms([customer_data.phone],data)

# All schedular
def thank_you():
	notification = has_template('Thank You')
	if notification:
		args = frappe.db.sql("""select a.customer,a.name, a.modified from `tabSales Invoice` a, 
			`tabSerial No` b where ifnull(a.outstanding_amount, 0) = 0 and a.docstatus=1 
			and a.thank_you is null and b.sales_invoice = a.name and b.completed = 'Yes' 
			and a.posting_date between DATE_FORMAT(NOW() ,'%Y-%m-01') AND NOW()""", as_dict=1)
		if args:
			for d in args:
				if datetime.datetime.strptime(d.modified, '%Y-%m-%d %H:%M:%S') + datetime.timedelta(minutes = 30) > datetime.datetime.now():
					customer_data = get_customer_details(d.customer)
					data = cstr(notification.template).replace('customer_name', d.customer)
					if notification.email_template and customer_data:
						send_mail(customer_data.email_id, data, notification.subject)
					if notification.sms_template and customer_data:
						send_sms([customer_data.phone],data)
					frappe.db.sql(""" update `tabSales Invoice` set thank_you='Completed' where name='%s'"""%(d.name))

def get_customer_details(customer):
	return frappe.db.sql(""" select * from `tabAddress` where 
		customer ='%s' limit 1"""%(customer), as_dict=1)

def has_template(type_of_event):
	return frappe.db.get_value('Notification Details',{'select_event':'Welcome'}, '*')

def update_status(name, type_of_event):
	name = frappe.db.get_value('Notification Log', {'document_name': name, 'type': type_of_event}, 'name')
	if not name:
		s = frappe.new_doc('Notification Log')
		s.document_name = name
		s.type = type_of_event
		s.save(ignore_permissions= True)

def send_mail(recipient, message, sub):
	import itertools
	from frappe.utils.email_lib import sendmail
	emails = [value for key, value in recipient.items()]
	sendmail(list(itertools.chain(*emails)), subject=sub, msg=cstr(message))
	return "done"