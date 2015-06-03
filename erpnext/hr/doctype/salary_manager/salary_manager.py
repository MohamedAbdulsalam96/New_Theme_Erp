# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, flt
from frappe import _

from frappe.model.document import Document
import pdb

class SalaryManager(Document):

	def get_emp_list(self):
		"""
			Returns list of active employees based on selected criteria
			and for which salary structure exists
		"""

		cond = self.get_filter_condition()
		cond += self.get_joining_releiving_condition()

		emp_list = frappe.db.sql("""
			select t1.name
			from `tabEmployee` t1, `tabSalary Structure` t2
			where t1.docstatus!=2 and t2.docstatus != 2
			and t1.name = t2.employee and t1.has_salary_structure='Yes'
		%s """% cond)
		return emp_list


	def get_filter_condition(self):
		self.check_mandatory()

		cond = ''
		for f in ['company', 'branch', 'department', 'designation']:
			if self.get(f):
				cond += " and t1." + f + " = '" + self.get(f).replace("'", "\'") + "'"

		return cond


	def get_joining_releiving_condition(self):
		m = self.get_month_details(self.fiscal_year, self.month)
		cond = """
			and ifnull(t1.date_of_joining, '0000-00-00') <= '%(month_end_date)s'
			and ifnull(t1.relieving_date, '2199-12-31') >= '%(month_start_date)s'
		""" % m
		return cond


	def check_mandatory(self):
		for f in ['company', 'month', 'fiscal_year']:
			if not self.get(f):
				frappe.throw(_("Please set {0}").format(f))

	def get_month_details(self, year, month):
		ysd = frappe.db.get_value("Fiscal Year", year, "year_start_date")
		if ysd:
			from dateutil.relativedelta import relativedelta
			import calendar, datetime
			diff_mnt = cint(month)-cint(ysd.month)
			if diff_mnt<0:
				diff_mnt = 12-int(ysd.month)+cint(month)
			msd = ysd + relativedelta(months=diff_mnt) # month start date
			month_days = cint(calendar.monthrange(cint(msd.year) ,cint(month))[1]) # days in month
			med = datetime.date(msd.year, cint(month), month_days) # month end date
			return {
				'year': msd.year,
				'month_start_date': msd,
				'month_end_date': med,
				'month_days': month_days
			}

	def create_sal_slip(self):
		"""
			Creates salary slip for selected employees if already not created

		"""
		emp_list = self.get_emp_list()
		ss_list = []
		for emp in emp_list:
			if not frappe.db.sql("""select name from `tabSalary Slip`
					where docstatus!= 2 and employee = %s and month = %s and fiscal_year = %s and company = %s
					""", (emp[0], self.month, self.fiscal_year, self.company)):
				ss = frappe.get_doc({
					"doctype": "Salary Slip",
					"fiscal_year": self.fiscal_year,
					"employee": emp[0],
					"month": self.month,
					"email_check": self.send_email,
					"company": self.company,
				})
				ss.insert()
				ss_list.append(ss.name)

		return self.create_log(ss_list)


	def create_log(self, ss_list):
		log = "<b>No employee for the above selected criteria OR salary slip already created</b>"
		if ss_list:
			log = "<b>Created Salary Slip has been created: </b>\
			<br><br>%s" % '<br>'.join(ss_list)
		return log


	def get_sal_slip_list(self):
		"""
			Returns list of salary slips based on selected criteria
			which are not submitted
		"""
		cond = self.get_filter_condition()
		ss_list = frappe.db.sql("""
			select t1.name from `tabSalary Slip` t1
			where t1.docstatus = 0 and month = %s and fiscal_year = %s %s
		""" % ('%s', '%s', cond), (self.month, self.fiscal_year))
		return ss_list


	def submit_salary_slip(self):
		"""
			Submit all salary slips based on selected criteria
		"""
		ss_list = self.get_sal_slip_list()
		not_submitted_ss = []
		for ss in ss_list:
			ss_obj = frappe.get_doc("Salary Slip",ss[0])
			try:
				ss_obj.email_check = self.send_email
				ss_obj.submit()
			except Exception,e:
				not_submitted_ss.append(ss[0])
				frappe.msgprint(e)
				continue

		return self.create_submit_log(ss_list, not_submitted_ss)


	def create_submit_log(self, all_ss, not_submitted_ss):
		log = ''
		if not all_ss:
			log = "No salary slip found to submit for the above selected criteria"
		else:
			all_ss = [d[0] for d in all_ss]

		submitted_ss = list(set(all_ss) - set(not_submitted_ss))
		if submitted_ss:
			mail_sent_msg = self.send_email and " (Mail has been sent to the employee)" or ""
			log = """
			<b>Submitted Salary Slips%s:</b>\
			<br><br> %s <br><br>
			""" % (mail_sent_msg, '<br>'.join(submitted_ss))

		if not_submitted_ss:
			log += """
				<b>Not Submitted Salary Slips: </b>\
				<br><br> %s <br><br> \
				Reason: <br>\
				May be company email id specified in employee master is not valid. <br> \
				Please mention correct email id in employee master or if you don't want to \
				send mail, uncheck 'Send Email' checkbox. <br>\
				Then try to submit Salary Slip again.
			"""% ('<br>'.join(not_submitted_ss))
		return log


	def get_total_salary(self):
		"""
			Get total salary amount from submitted salary slip based on selected criteria
		"""
		cond = self.get_filter_condition()
		tot = frappe.db.sql("""
			select sum(rounded_total) from `tabSalary Slip` t1
			where t1.docstatus = 1 and month = %s and fiscal_year = %s %s
		""" % ('%s', '%s', cond), (self.month, self.fiscal_year))

		return flt(tot[0][0])


	def get_total_salary_for_weekly(self):
		cond = self.get_filter_condition()
		tot = frappe.db.sql("""SELECT
									     ifnull(sum(rounded_total),0.0)
									FROM
									    `tabWeekly Salary Slip` t1
									WHERE
									 docstatus=1 AND salary_type='%(type_of_sal)s'
									AND from_date = STR_TO_DATE('%(from_date)s','%(format)s')
									AND to_date = STR_TO_DATE('%(to_date)s','%(format)s')
									AND fiscal_year = '%(fiscal_year)s'
									%(cond)s """%{'format':'%Y-%m-%d','from_date':self.from_date,'to_date':self.to_date,'fiscal_year':self.fiscal_year,'company':self.company,'type_of_sal':self.type_of_salary,'dept':self.department,'desig':self.designation,'branch':self.branch,'cond':cond},as_list=1)
		return flt(tot[0][0])



	def get_acc_details(self):
		"""
			get default bank account,default salary acount from company
		"""
		amt = 0
		if self.type_of_salary == 'Weekly' or self.type_of_salary == 'LumpSum':
			amt = self.get_total_salary_for_weekly()
		elif self.type_of_salary == 'Monthly':
			amt = self.get_total_salary()

		default_bank_account = frappe.db.get_value("Company", self.company,
			"default_bank_account")
		if not default_bank_account:
			frappe.msgprint(_("You can set Default Bank Account in Company master"))

		return {
			'default_bank_account' : default_bank_account,
			'amount' : amt
		}


	def create_weekly_sal_slip(self):
		cond = self.get_filter_condition()
		emp_list = self.get_emp_list_for_weekly_lumpsum()
		ss_list = []
		for emp in emp_list:
			if not frappe.db.sql("""SELECT
									    name
									FROM
									    `tabWeekly Salary Slip` t1
									WHERE
									    employee='%(employee)s'
									AND docstatus!=2 AND salary_type='%(type_of_sal)s'
									AND (
									        STR_TO_DATE('%(from_date)s','%(format)s') BETWEEN from_date AND to_date
									    OR  STR_TO_DATE('%(to_date)s','%(format)s') BETWEEN from_date AND to_date
									    OR  from_date BETWEEN STR_TO_DATE('%(from_date)s','%(format)s') AND STR_TO_DATE('%(to_date)s',
									        '%(format)s')
									    OR  to_date BETWEEN STR_TO_DATE('%(from_date)s','%(format)s') AND STR_TO_DATE('%(to_date)s',
									        '%(format)s')  )
									AND fiscal_year = '%(fiscal_year)s'
									%(cond)s """%{'format':'%Y-%m-%d','from_date':self.from_date,'to_date':self.to_date,'employee':emp[0],'fiscal_year':self.fiscal_year,'company':self.company,'type_of_sal':self.type_of_salary,'dept':self.department,'desig':self.designation,'branch':self.branch,'cond':cond}):
				ss = frappe.get_doc({
						"doctype": "Weekly Salary Slip",
						"salary_type":self.type_of_salary,
						"from_date":self.from_date,
						"to_date":self.to_date,
						"fiscal_year": self.fiscal_year,
						"employee": emp[0],
						"month": self.month,
						"email_check": self.send_email,
						"company": self.company,
						"department":self.department,
						"designation":self.designation,
						"branch":self.branch
				})
				
				ss.insert()
				ss_list.append(ss.name)			
		return self.create_log_for_weekly(ss_list)

	
	def create_log_for_weekly(self, ss_list):
		log = "<b>No Weekly salary slip  for {0} type and above selected criteria created</b>".format(self.type_of_salary)
		if ss_list:
			ss_list = [s for s in ss_list]
			log = "<b> Weekly Salary Slip has been created for type '%s' </b>\
			<br><br>%s"%(self.type_of_salary,'<br>'.join(ss_list))
		return log			


	def get_weekly_sal_slip_list(self):
		cond = self.get_filter_condition()
		ss_list = frappe.db.sql("""SELECT
									    name
									FROM
									    `tabWeekly Salary Slip` t1
									WHERE
									 docstatus=0 AND salary_type='%(type_of_sal)s'
									AND from_date = STR_TO_DATE('%(from_date)s','%(format)s')
									AND to_date = STR_TO_DATE('%(to_date)s','%(format)s')
									AND fiscal_year = '%(fiscal_year)s'
									%(cond)s """%{'format':'%Y-%m-%d','from_date':self.from_date,'to_date':self.to_date,'fiscal_year':self.fiscal_year,'company':self.company,'type_of_sal':self.type_of_salary,'dept':self.department,'desig':self.designation,'branch':self.branch,'cond':cond},as_list=1)
		return ss_list


	def submit_weekly_salary_slip(self):
		ss_list = self.get_weekly_sal_slip_list()
		not_submitted_ss = []
		for ss in ss_list:
			ss_obj = frappe.get_doc("Weekly Salary Slip",ss[0])
			try:
				ss_obj.email_check = self.send_email
				ss_obj.submit()
			except Exception,e:
				not_submitted_ss.append(ss[0])
				frappe.msgprint(e)
				continue

		return self.create_submit_log_for_weekly(ss_list, not_submitted_ss)


	def create_submit_log_for_weekly(self, all_ss, not_submitted_ss):
		log = ''
		if not all_ss:
			log = "No Weekly Salary slip found to submit for the above selected criteria"
		else:
			all_ss = [d[0] for d in all_ss]

		submitted_ss = list(set(all_ss) - set(not_submitted_ss))
		if submitted_ss:
			mail_sent_msg = self.send_email and " (Mail has been sent to the employee)" or ""
			log = """
			<b>Submitted Weekly Salary Slips%s:</b>\
			<br><br> %s <br><br>
			""" % (mail_sent_msg, '<br>'.join(submitted_ss))

		if not_submitted_ss:
			log += """
				<b>Not Submitted  Weekly Salary Slips: </b>\
				<br><br> %s <br><br> \
				Reason: <br>\
				May be company email id specified in employee master is not valid. <br> \
				Please mention correct email id in employee master or if you don't want to \
				send mail, uncheck 'Send Email' checkbox. <br>\
				Then try to submit Weekly Salary Slip again.
			"""% ('<br>'.join(not_submitted_ss))
		return log
	


	def get_emp_list_for_weekly_lumpsum(self):	
		cond = self.get_filter_condition()
		cond += self.get_joining_releiving_condition()

		emp_list = frappe.db.sql("""
			select t1.name
			from `tabEmployee` t1 where t1.docstatus!=2 and t1.has_salary_structure='No' and t1.type_of_salary='%s'
		%s """%(self.type_of_salary,cond),as_list=1)
		return emp_list

				