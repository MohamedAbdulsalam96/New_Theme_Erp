# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns, data = [], []
	employee = branch= ''
	cond = "1=1"
	if filters:
		employee, branch =  filters.get('employee') or '', filters.get('branch') or ''
	data = frappe.db.sql(""" select * from
									(
									SELECT
									    e.name as staff_code,
									    e.employee_name as staff_name,
									    e.branch,
									    'Employee' as role,
									    e.employment_type as type,
									    e.cell_number,
									    e.user_id as e_mail,
									    coalesce(ss.net_pay,0) as salary,
									   coalesce((select sum(total_loan_amount) from tabLoan where employee_id=e.name),0) as loan_amount,
									   coalesce((select sum(drawings) from `tabAD Details` where employee_id=e.name),0) as drawing_wages
									    
									FROM
									    `tabEmployee` e  left join `tabSalary Structure` ss on e.name=ss.employee 
									    left join `tabAD Details` w on w.employee_id=e.name
									    )foo
									    where branch = coalesce(nullif('%s', ''),foo.branch)
									    and staff_code = coalesce(nullif('%s', ''),foo.staff_code)"""%(branch, employee), as_list=1)

	columns = ["Employee:Link/Employee:150", "Employee Name::110", "Branch::100","Role::70","Employee Type::70","Cell No::100", "User Id::60", "Salary:Currency:100", "Loan Amount:Currency:100", "Drawings:Currency:100"]
	return columns, data
