# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.widgets.reportview import get_match_cond
from frappe.utils import add_days, cint, cstr, date_diff, rounded, flt, getdate, nowdate, \
	get_first_day, get_last_day,money_in_words, now, nowtime
from frappe import _
from frappe.model.db_query import DatabaseQuery
from frappe import msgprint, _, throw
from frappe.model.naming import make_autoname
from erpnext.stock.utils import get_incoming_rate
from tools.custom_data_methods import get_user_branch, get_branch_cost_center, get_branch_warehouse, find_next_process
from tools.tools_management.custom_methods import cut_order_generation
import random
import string
import datetime

def create_production_process(doc, method):
	for d in doc.get('work_order_distribution'):
		process_allotment = create_process_allotment(doc, d)
		if process_allotment:
			create_dashboard(process_allotment,d,doc)

def create_work_order(doc, data, serial_no, item_code, qty, parent_item_code):
	wo = frappe.new_doc('Work Order')
	wo.item_code = item_code
	wo.customer = doc.customer
	wo.parent_item_code = parent_item_code
	wo.sales_invoice_no = doc.name
	wo.customer_name = frappe.db.get_value('Customer',wo.customer,'customer_name')
	wo.item_qty = qty
	# if doc.trial_date and frappe.db.get_value('Process Item', {'parent': item_code, 'trials':1}, 'name'):
	# 	wo.trial_no = 1
	# 	wo.trial_date = doc.trial_date
	wo.fabric__code = get_dummy_fabric(item_code) or data.fabric_code
	wo.serial_no_data = serial_no
	wo.branch = data.tailoring_warehouse
	wo.delivery_date = data.tailoring_delivery_date or ''
	create_work_order_style(data, wo, item_code)
	create_work_order_measurement(data, wo, item_code)
	create_process_wise_warehouse_detail(data, wo, item_code)
	wo.save(ignore_permissions=True)
	return wo.name

def create_work_order_style(data, wo_name, item_code):
	if wo_name and item_code:
		styles = frappe.db.sql(""" SELECT 
									    si.style,
									    si.abbreviation,
									    si.process_wise_tailor_cost
									FROM
									    `tabStyle Item` AS si
									WHERE
									    parent = '%s'
									group by si.style     """%(item_code),as_dict=1)
		if styles:
			table_view = 'Right'
			for s in styles:
				image_viewer, default_value = get_styles_DefaultValues(s.style, item_code)  #Newly Added
				ws = wo_name.append('wo_style', {})
				ws.field_name = s.style
				ws.abbreviation  = s.abbreviation
				ws.image_viewer = image_viewer
				ws.default_value = default_value
				ws.process_wise_tailor_cost = s.process_wise_tailor_cost
				# ws.parent = wo_name
				# ws.parentfield = 'wo_style'
				# ws.parenttype = 'Work Order'
				ws.table_view = 'Left' if table_view =='Right' else 'Right'
				table_view = ws.table_view
				# ws.save(ignore_permissions =True)
	return True

@frappe.whitelist(allow_guest=True)
def get_styles_DefaultValues(style, item_code):            #Newly Added Method
	default_item= frappe.db.sql(""" select image_viewer, default_value from `tabStyle Item` as a 
		where a.default_values =1 and a.parent='%s' and a.style='%s'"""%(item_code, style),as_list=1)
	if default_item:
		return default_item[0][0], default_item[0][1]
	else:
		return '', ''

def create_work_order_measurement(data, wo_name, item_code):
	style_parm=[]
	if wo_name and item_code:
		measurements = frappe.db.sql(""" select * from `tabMeasurement Item` where parent = '%s' order by idx
			"""%(item_code),as_dict=1)
		if measurements:
			for s in measurements:
				if not s.parameter in style_parm:
					mi = wo_name.append('measurement_item', {})
					mi.parameter = s.parameter
					mi.abbreviation = s.abbreviation
					mi.image_view = s.image_view
					mi.idx = s.idx
					# mi.parent = wo_name
					# mi.parentfield = 'measurement_item'
					# mi.parenttype = 'Work Order'
					# mi.save(ignore_permissions =True)
					style_parm.append(s.parameter)
	return True

def create_process_wise_warehouse_detail(data, wo_name, item_code):
	if wo_name:
		previous_process_branch = get_user_branch()
		for proc_wh in frappe.db.sql("""select process_name, warehouse, idx, actual_fabric,branch_list from `tabProcess Item`
			where parent = '%s'"""%item_code,as_list=1):
			warehouse_list = []
			if proc_wh[4]:
				warehouse_list = proc_wh[4].split('\n')
				warehouse_list = [warehouse for warehouse in warehouse_list if warehouse]	
			mi = wo_name.append('process_wise_warehouse_detail', {})
			mi.process = proc_wh[0]
			if previous_process_branch in warehouse_list:
				mi.warehouse = previous_process_branch
			else:
				mi.warehouse = proc_wh[1]
			previous_process_branch = mi.warehouse
			mi.idx = proc_wh[2]
			mi.actual_fabric = cint(proc_wh[3])
			# mi.parent = wo_name
			# mi.parentfield = 'process_wise_warehouse_detail'
			# mi.parenttype = 'Work Order'
			# mi.save(ignore_permissions =True)
	return True

def create_process_allotment(doc, data):
	process_list=[]
	i = 1
	process = frappe.db.sql(""" select distinct process_name,idx, quality_check,trials from `tabProcess Item` where parent = '%s' order by idx asc
		"""%(data.tailoring_item),as_dict = 1)
	if process:
		trials_process = frappe.db.sql(""" select group_concat(process_name),trials from `tabProcess Item` where parent = '%s' and trials=1 group by trials
									"""%(data.tailoring_item),as_list = 1)
		for s in process:
			pa = frappe.new_doc('Process Allotment')
		 	pa.sales_invoice_no = data.parent
		 	pa.process_no = i
		 	pa.process = s.process_name
		 	pa.process_work_order = data.tailor_work_order
		 	pa.qc = cint(s.quality_check)
		 	pa.work_order = data.tailor_work_order
		 	if data.expense:
			 	pa.total_expense = flt(data.expense) / flt(data.tailor_qty)
			pa.total_invoice_amount = frappe.db.get_value('Sales Invoice Items', {'parent': doc.name, 'tailoring_item_code': data.clubbed_product_name}, 'tailoring_rate') or 0.0
		 	# Suyash 'Customer name field added in process allotment'
		 	pa.customer_name = doc.customer
		 	pa.status = 'Pending'
		 	pa.item = data.tailoring_item
		 	if cint(s.trials) == 1 and i == 1 and data.trials:
		 		pa.process_trials = 1
		 		pa.emp_status = 'Assigned'
		 		pa.qc = cint(frappe.db.get_value('Trial Dates', {'parent': data.trials, 'trial_no':1, 'process': pa.process}, 'quality_check')) or 0
		 		i= i + 1
		 	pa.branch = frappe.db.get_value('Process Wise Warehouse Detail',{'parent':data.tailor_work_order,'process':pa.process}, 'warehouse')
		 	pa.serials_data = data.serial_no_data
		 	pa.processwise_trial_details = "Trials are assigned for process %s"%(trials_process[0][0]) if trials_process and frappe.db.get_value('Work Order',data.tailor_work_order,'trial_date') else "Trials are not assigned"
		 	
		 	pa.finished_good_qty = data.tailor_qty
		 	create_material_issue(data, pa)
		 	create_trials(data, pa)
		 	pa.save(ignore_permissions=True)
		 	
		 	process_list.append((pa.name).encode('ascii', 'ignore'))
 	return process_list

def create_material_issue(data, obj):
 	if data.tailoring_item:
 		rm = frappe.db.sql("""select * from `tabRaw Material Item` where parent='%s' and raw_process='%s'"""%(data.tailoring_item, obj.process),as_dict=1)
 		if rm:
 			for s in rm:
 				d = obj.append('issue_raw_material',{})
 				d.raw_material_item_code = s.raw_item_code
 				d.raw_material_item_name = frappe.db.get_value('Item',s.raw_item_code,'item_name')
 				d.raw_sub_group = s.raw_item_sub_group or frappe.db.get_value('Item',s.raw_item_code,'item_sub_group')
 				d.uom = frappe.db.get_value('Item',s.raw_item_code,'stock_uom')
 				d.qty = s.qty
 	return True

def create_trials(data, obj):
 	if data.trials:
 		trials = frappe.db.sql("select * from `tabTrial Dates` where parent='%s' and process='%s' order by idx"%(data.trials, obj.process), as_dict=1)
 		if trials:
 			for trial in trials:
 				s = obj.append('trials_transaction',{})
				s.trial_no = trial.trial_no
				s.trial_date = trial.trial_date
				s.work_order = data.tailor_work_order
				s.status= 'Pending'
	return "Done"

def make_trial(data, item_code, parent):
	s= frappe.new_doc('Trials Master')
	s.sales_invoice_no = data.parent
	s.customer = frappe.db.get_value('Sales Invoice',data.parent,'customer')
	s.item_code = item_code
	s.item_name = frappe.db.get_value('Item',s.item_code,'item_name')
	s.process = parent
	s.save(ignore_permissions=True)
	return s.name

# def make_trial_transaction(data, args, trial):
# 	s = frappe.new_doc('Trials Transaction')
# 	s.trial_no = trial.trial_no
# 	s.trial_date = trial.trial_date
# 	s.work_order = data.tailor_work_order
# 	s.status= 'Pending'
# 	s.parent = args.get('parent')
# 	s.parenttype = args.get('parenttype')
# 	s.parentfield = 'trials_transaction'
# 	s.save(ignore_permissions=True)
# 	return "Done"

# def make_raw_material_entry(data, args):
# 	if args.get('type') =='invoice':
# 		raw_material = retrieve_fabric_raw_material(data, args)
# 	else:
# 		raw_material = frappe.db.sql("select raw_trial_no, raw_item_code, raw_item_sub_group from `tabRaw Material Item` where raw_process='%s' and raw_trial_no=%s and parent='%s'"%(args.get('process_name'),args.get('trial_no'),args.get('item')),as_dict=1)
# 	if raw_material:
# 		make_entry(raw_material, args)
# 	return "Done"

# def retrieve_fabric_raw_material(data, args):
# 	return frappe.db.sql("""select '', name as raw_item_code, '' from `tabItem` 
# 	where name = '%s' union  
# 	select raw_trial_no, raw_item_code, raw_item_sub_group 
# 	from `tabRaw Material Item` where parent = '%s'"""%(args.get('item'),args.get('item')), as_dict=1)

# def make_entry(raw_material, args):
# 	for d in raw_material:
# 		s = frappe.new_doc('Issue Raw Material')
# 		s.issue_trial_no = d.raw_trial_no
# 		s.raw_material_item_code = d.raw_item_code
# 		s.raw_material_item_name = frappe.db.get_value('Item',s.raw_material_item_code,'item_name')
# 		s.raw_sub_group = d.raw_item_sub_group
# 		s.parent = args.get('parent')
# 		s.parenttype = args.get('parenttype')
# 		s.parentfield = 'issue_raw_material'
# 		s.uom = frappe.db.get_value('Item',s.raw_material_item_code,'stock_uom')
# 		s.save(ignore_permissions=True)
# 		return "Done"

def create_stock_entry(doc, data):
 	ste = frappe.new_doc('Stock Entry')
 	ste.purpose_type = 'Material Receipt'
 	ste.purpose ='Material Receipt'
 	ste.branch = get_user_branch()
 	make_stock_entry_of_child(ste,data,doc)
 	ste.save(ignore_permissions=True)
 	st = frappe.get_doc('Stock Entry', ste.name)
 	st.submit()
 	return ste.name

def make_stock_entry_of_child(obj, data,doc):
 	if data.tailoring_item:
 		st = obj.append('mtn_details',{})
		st.t_warehouse = frappe.db.get_value('Branch',get_user_branch(),'warehouse')
		st.item_code = data.tailoring_item
		st.serial_no = data.serial_no_data
		st.item_name = frappe.db.get_value('Item', st.item_code, 'item_name')
		st.description = frappe.db.get_value('Item', st.item_code, 'description')
		st.uom = frappe.db.get_value('Item', st.item_code, 'stock_uom')
		st.conversion_factor = 1
		st.qty = data.tailor_qty or 1
		st.transfer_qty = data.tailor_qty or 1
		st.incoming_rate = 1.00
		st.sales_invoice_no = doc.name
		company = frappe.db.get_value('Global Defaults', None, 'default_company')
		st.expense_account = 'Stock Adjustment - '+frappe.db.get_value('Company', company, 'abbr')
		st.cost_center = 'Main - '+frappe.db.get_value('Company', company, 'abbr')
 	return True

def create_stock(name, item_code, warehouse, warehouse_type , qty=None):
 	if item_code:
		ste = frappe.new_doc('Stock Entry Detail')
		if warehouse_type=='source':
			ste.s_warehouse = warehouse
		else:
			ste.t_warehouse = warehouse
		ste.item_code = item_code 
		ste.item_name = frappe.db.get_value('Item', ste.item_code, 'item_name')
		ste.description = frappe.db.get_value('Item', ste.item_code, 'description')
		ste.uom = frappe.db.get_value('Item', ste.item_code, 'stock_uom')
		ste.conversion_factor = 1
		ste.qty = qty or 1
		ste.transfer_qty=qty or 1
		ste.parent =name
		ste.parenttype='Stock Entry'
		ste.parentfield = 'mtn_details'
		ste.save(ignore_permissions=True)
	return True

def create_dashboard(process, d ,doc):
	pd = create_production_dashboard( process, d, doc)
	if pd:
		update_pdd(d, pd, process) # add production dashboard name on trials and process allotment form

def update_pdd(args, pdd, process_list):
		if args.trials:
			cond = "pdd='%s'"%(pdd)
			set_pdd_name('Trials', cond, args.trials)
		if process_list:
			for process_allotment in process_list:
				cond = "pdd='%s', trial_dates='%s'"%(pdd, args.trials)
				set_pdd_name('Process Allotment', cond, process_allotment)
		if args.tailor_work_order:
			cond = "pdd='%s'"%(pdd)
			set_pdd_name('Work Order', cond, args.tailor_work_order)

def set_pdd_name(table, cond, name):
	frappe.db.sql(""" update `tab%s` set %s where name = '%s'"""%(table, cond, name))

def create_production_dashboard( process, data, doc):
	validate_duplicate_work_order(data.tailor_work_order)
	pd = frappe.new_doc('Production Dashboard Details')
	pd.sales_invoice_no = doc.name
	pd.article_code = data.tailoring_item
	pd.tailoring_service = data.work_order_service
	pd.article_qty = data.tailor_qty
	pd.start_branch = get_user_branch()
	pd.end_branch = data.tailor_warehouse
	pd.fabric_code = data.tailor_fabric
	pd.work_order = data.tailor_work_order
	pd.dummy_fabric_code = get_dummy_fabric(data.tailoring_item)
	pd.fabric_qty = data.tailor_fabric_qty
	pd.serial_no = data.serial_no_data
	make_production_process_log(pd, process, data)
	# serial_no_log(pd, data)
	pd.save(ignore_permissions=True)
	create_stock_entry(doc, data)
	return pd.name

def get_dummy_fabric(item):
	dummy_fabric = frappe.db.sql("""select raw_item_code from `tabRaw Material Item` 
		where parent = '%s' and raw_item_code in 
		(select name from `tabItem` where item_group = 'Fabric')"""%(item), as_list=1)
	if dummy_fabric:
		return dummy_fabric[0][0]
	return ''

def make_production_process_log(obj, process_list, args):
	process_list =  "','".join(process_list)
	process = frappe.db.sql("""select a.name,a.sales_invoice_no, a.item, a.serials_data, 
		a.process, a.process_work_order, a.branch, b.trial_no, b.trial_date,
		b.work_order from `tabProcess Allotment` a left join `tabTrials Transaction` b on b.parent = a.name 
		where a.name in %s order by a.name, b.trial_no"""%("('"+process_list+"')"), as_dict=1)
	status = 'Pending'
	if process:
		for s in process:
			pl = obj.append('process_log',{})
			pl.process_data = s.name
			pl.process_name = s.process
			pl.branch = s.branch
			pl.trials = s.trial_no
			pl.actual_fabric = cint(frappe.db.get_value('Trial Dates', {'work_order': args.tailor_work_order, 'process': s.process, 'trial_no': s.trial_no}, 'actual_fabric')) or 0
			pl.status = status
			pl.pr_work_order = s.work_order or s.process_work_order

def serial_no_log(obj, data):
	sn = cstr(data.serial_no_data).split('\n')
	for s in sn:
		if s:
			sn = obj.append('production_status_detail', {})
			sn.item_code = data.tailoring_item
			sn.serial_no = s
			sn.branch = data.tailor_warehouse
			sn.status = 'Ready'

def delete_production_process(doc, method):
	for d in doc.get('entries'):
		production_dict = get_dict(doc.name)
		delte_doctype_data(production_dict)
	delete_work_distribution(doc)

def delete_work_distribution(self):
	wo_disct_list = []
	for d in self.get('work_order_distribution'):
		wo_disct_list.append(d)
	[self.remove(d) for d in wo_disct_list]

def get_dict(invoice_no):
	return {'Production Dashboard Details':{'sales_invoice_no':invoice_no}}

def delte_doctype_data(production_dict):
	for doctype in production_dict:
		for field in production_dict[doctype]:
			frappe.db.sql("Delete from `tab%s` where %s = '%s'"%(doctype, field, production_dict[doctype][field]))

def validate_sales_invoice(doc, method):
	validate_work_order_assignment(doc)

def add_data_for_deleted_rows(doc,d):
	if cint(d.check_split_qty)==1:
		split_qty = eval(d.split_qty_dict)
		for s in split_qty:
			if s:
				prepare_data_for_order(doc,d, split_qty[s]['qty'])
	else:
		prepare_data_for_order(doc, d, d.tailoring_qty)




def add_data_in_work_order_assignment(doc, method):
	validate_branch(doc)
	if not doc.get('work_order_distribution'):
		doc.set('work_order_distribution',[])	
	for d in doc.get('sales_invoice_items_one'):
		if not frappe.db.get_value('Work Order Distribution', {'clubbed_product_name':d.tailoring_item_code,'parent':doc.name},'name'):
			if cint(d.check_split_qty)==1:
				split_qty = eval(d.split_qty_dict)
				for s in split_qty:
					if s:
						prepare_data_for_order(doc,d, split_qty[s]['qty'])
			else:
				prepare_data_for_order(doc, d, d.tailoring_qty)
	validate_work_order_assignment(doc)
	return "Done"

def prepare_data_for_order(doc, d, qty):
	if cint(frappe.db.get_value('Item', d.tailoring_item_code, 'is_clubbed_product')) == 1:
		sales_bom_items = frappe.db.sql("""Select * FROM `tabSales BOM Item` WHERE 
			parent ='%s' and parenttype = 'Item'"""%(d.tailoring_item_code), as_dict=1)
		for item in sales_bom_items:
			make_order(doc, d, qty, item.item_code, item.parent)
	else:
		make_order(doc, d,qty, d.tailoring_item_code)

def make_order(doc, d, qty, item_code, parent=None):
		e = doc.append('work_order_distribution', {})
		e.tailoring_item = item_code
		e.tailor_item_name = frappe.db.get_value('Item', item_code, 'item_name')
		e.tailor_qty = qty
		e.work_order_service = d.tailoring_price_list
		# e.parenttype = 'Sales Invoice'
		# e.parentfield = 'work_order_distribution'
		# e.parent = doc.name
		e.serial_no_data = generate_serial_no(doc, item_code, qty)
		e.tailor_fabric= d.fabric_code
		e.tailor_fabric_qty = frappe.db.get_value('Size Item', {'parent':d.tailoring_item_code, 'size':d.tailoring_size, 'width':d.width }, 'fabric_qty')
		e.tailor_warehouse = d.tailoring_branch
		e.expense = d.total_expenses
		if parent:
			e.clubbed_product_name = parent
		else:
			e.clubbed_product_name = item_code	 
		if not e.tailor_work_order:
			e.tailor_work_order = create_work_order(doc, d, e.serial_no_data, item_code, qty, parent)
			update_serial_no_with_wo(e.serial_no_data, e.tailor_work_order)
		# if not e.trials and frappe.db.get_value('Process Item', {'parent':item_code, 'trials':1}, 'name') and doc.trial_date:
		# 	e.trials = make_schedule_for_trials(doc, d, e.tailor_work_order, item_code, e.serial_no_data)
		# #e.save()
		return "Done"

def make_schedule_for_trials(doc,method):
	if doc.trial_date and frappe.db.get_value('Process Item', {'parent':doc.item_code, 'trials':1}, 'name'):
		s =frappe.new_doc('Trials')
		s.item_code = doc.item_code
		s.trials_serial_no = s.trials_serial_no_status = get_first_serial_no(doc.serial_no_data)
		s.sales_invoice = doc.sales_invoice_no
		s.serial_no_data = doc.serial_no_data
		s.customer = doc.customer
		s.customer_name = doc.customer_name
		s.branch = get_user_branch()
		s.item_name = frappe.db.get_value('Item', doc.item_code, 'item_name')
		s.work_order = doc.name
		data = schedules_date(s, doc.item_code, doc.name,doc.trial_date,doc.customer_name)
		if data == 'True':
			s.save(ignore_permissions=True)	
			update_work_order_distribution(doc.item_code,doc.sales_invoice_no,doc.name,s.name)
			doc.trial_no = 1
			update_trial_date(doc)
			return s.name

def get_first_serial_no(serial_no_data):
	serial_no = ''
	sn = cstr(serial_no_data).split('\n')
	if sn:
		serial_no = sn[0]
	return serial_no

def update_trial_date(doc):
	if doc.parent_item_code:
		result = frappe.db.get_value('Sales Invoice Item',{'parent':doc.sales_invoice_no,'item_code':doc.parent_item_code},['name','trial_date'],as_dict=1)
	elif not doc.parent_item_code:
		result = frappe.db.get_value('Sales Invoice Item',{'parent':doc.sales_invoice_no,'item_code':doc.item_code},['name','trial_date'],as_dict=1)		
	update_for_recent_trial_date(doc,result)
	
def update_for_recent_trial_date(doc,result):
	if not result.get('trial_date') or convert_string_to_datetime(result.get('trial_date')) > convert_string_to_datetime(doc.trial_date):
		frappe.db.sql("""UPDATE
							    `tabSales Invoice Item`
							SET
							    trial_date ='%s'
							WHERE
							    name='%s' """%(doc.trial_date,result.get('name')))

def convert_string_to_datetime(date):
	date = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
	return date							    		


def update_work_order_distribution(item_code,sales_invoice,work_order,trial_name):
	wod_name = frappe.db.get_value('Work Order Distribution',{'parent':sales_invoice,'tailor_work_order':work_order},'name')
	if wod_name and trial_name:
		wo_doc = frappe.get_doc('Work Order Distribution',wod_name)
		wo_doc.trials = trial_name
		wo_doc.save(ignore_permissions=True)


def schedules_date(parent, item, work_order, trial_date, customer_name):
	trials = frappe.db.sql("select branch_dict from `tabProcess Item` where parent='%s' and trials=1  order by idx"%(item), as_dict=1)
	if trials:
		for index,t in enumerate(trials):
			if t.branch_dict:
				branch_dict = eval(t.branch_dict)
				for inner_index,s in enumerate(range(0, len(branch_dict))):
					d = parent.append('trial_dates',{})
					d.process = branch_dict.get(cstr(s)).get('process')
					d.trial_no = branch_dict.get(cstr(s)).get('trial')
					d.trial_date = trial_date if cint(d.trial_no) == 1 else ''
					d.work_status = 'Open' if cint(d.trial_no) == 1 and index == 0 and inner_index == 0 else 'Pending'
					d.subject = 'Customer %s: First Trial for Item %s'%(customer_name, frappe.db.get_value('Item', item, 'item_name')) if cint(d.trial_no) == 1 else ''
					d.actual_fabric = 1 if branch_dict.get(cstr(s)).get('actual_fabric') == 'checked' else 0
					d.quality_check = 1 if branch_dict.get(cstr(s)).get('quality_check') == 'checked' else 0
					d.amend = 1 if branch_dict.get(cstr(s)).get('amended') == 'checked' else 0
					d.trial_branch = get_user_branch()
					# d.idx = cstr(s + 1)
					# d.parent = parent
					d.work_order = work_order
					# d.parenttype = 'Trials'
					# d.parentfield = 'trial_dates'
					# d.save(ignore_permissions=True)		
		return 'True'
	else:
		return 'False'

def validate_work_order_assignment(doc):
# 	if doc.get('work_order_distribution') and doc.get('sales_invoice_items_one'):
# 		for d in doc.get('sales_invoice_items_one'):
# 			if d.tailoring_item_code and d.tailoring_qty:
	pass
				# check_work_order_assignment(doc, d.tailoring_item_code, d.tailoring_qty)

def check_work_order_assignment(doc, item_code, qty):
	count = 0
	for d in doc.get('work_order_distribution'):
		if d.tailoring_item == item_code:
			count += cint(d.tailor_qty)
	if cint(qty) !=  count:
		frappe.throw(_("Qty should be equal"))

def create_serial_no(doc, method):
	for d in doc.get('work_order_distribution'):
		if not d.serial_no_data:
			d.serial_no_data = generate_serial_no(doc,d.tailoring_item, d.tailor_qty)
			update_serial_no_with_wo(d.serial_no_data, d.tailor_work_order)

def generate_serial_no(doc, item_code, qty):
	series = frappe.db.get_value('Item', item_code, 'serial_no_series')
	if not series:
		series = str(doc.name) + '-.###'
	serial_no =''
	temp_qty = qty
	while cint(qty) > 0:
		sn = frappe.new_doc('Serial No')
		sn.name = make_autoname(series) 
		sn.serial_no = sn.name
		sn.process_status = 'Open'
		sn.item_code = item_code
		sn.sales_invoice = doc.name
		sn.status = 'Available'
		sn.save(ignore_permissions=True)
		if cint(temp_qty) == cint(qty) and sn.name:
			serial_no = sn.name
		elif sn.name:
			serial_no += '\n' + sn.name 
		qty = cint(qty) -1
	return serial_no

def update_serial_no_with_wo(serial_no_list, work_order):
	if serial_no_list and work_order:
		serial_no_list = cstr(serial_no_list).split('\n')
		for serial_no in serial_no_list:
			frappe.db.sql(""" update `tabSerial No` set work_order='%s' where
				name ='%s'"""%(work_order, serial_no))

@frappe.whitelist()
def get_process_detail(name):
	branch_cond = ''
	branch = get_user_branch()
	if branch:
		branch_cond = "and a.branch = '%s' "%(branch)
	return frappe.db.sql("""SELECT
				    a.process_data,
				    a.process_name,
				    ifnull(pa.process_trials,'') AS trials,
				    ifnull(pa.qi_status,'') as qi_status
				FROM
				    `tabProcess Log` a
				JOIN
				    `tabProcess Allotment` pa
				ON
				    a.process_data = pa.name
				WHERE
				    a.parent = '%s' %s
				group by a.process_name
				ORDER BY
				    a.process_data"""%(name,branch_cond),as_dict=1)

def invoice_validation_method(doc, method):
	if not doc.branch:
		doc.branch = frappe.db.get_value('User', frappe.session.user, 'branch')

@frappe.whitelist()
def get_work_order_details(sales_invoice_no):
	return frappe.db.sql(""" Select name, item_code, ifnull(status, 'Pending') as release_status 
		from `tabWork Order` where sales_invoice_no='%s' and status<>'Release'"""%(sales_invoice_no), as_dict=1)

@frappe.whitelist()
def update_status(sales_invoice_no, args):
	args = eval(args)
	for s in args:
		if s.get('status') == 'Release' and frappe.db.get_value('Work Order', s.get('work_order'), 'status')!='Release':
			validate_work_order(s)
			details = open_next_branch(frappe.db.get_value('Production Dashboard Details',{'work_order': s.get('work_order')}, 'name'), 1)
			# add_to_serial_no(details, s.get('work_order'))
			cut_order_generation(s.get('work_order'), sales_invoice_no)
			update_work_order_status(s.get('work_order'), s.get('status'))
			if not frappe.db.get_value('Stock Entry Detail', {'work_order': s.get('work_order'), 'docstatus':0}, 'name') and details:
				sn_list = frappe.db.get_value('Work Order', s.get('work_order'), 'serial_no_data')
				parent = stock_entry_for_out(s, details.branch, sn_list, frappe.db.get_value('Work Order', s.get('work_order'), 'item_qty'))
		elif s.get('status') == 'Hold' and frappe.db.get_value('Work Order', s.get('work_order'), 'status') != 'Release':
			update_work_order_status(s.get('work_order'), 'Hold')
		elif frappe.db.get_value('Work Order', s.get('work_order'), 'status') == 'Release' and s.get('status') in ('Release','Pending', 'Hold'):
			frappe.msgprint("Work order %s is already release"%(s.get('work_order')))
	return True

def get_status(work_order):
	process = frappe.db.sql("select process_name from `tabProcess Log` where pr_work_order='%s' and idx = 1"%(work_order), as_list=1)
	if process:
		return process[0][0]

def release_work_order(doc):
	if doc.status != 'Release' and cint(frappe.db.get_value('Sales Invoice', doc.sales_invoice_no, 'release')) == 1:
		s= {'work_order': doc.name, 'status': 'Release', 'item': doc.item_code}
		# details = open_next_branch(frappe.db.get_value('Production Dashboard Details',{'work_order': doc.name}, 'name'), 1)
		# add_to_serial_no(details, s.get('work_order'))
		update_work_order_status(doc.name, 'Release')
		branch = frappe.db.get_value('Process Wise Warehouse Detail',{'parent':doc.name, 'idx':1}, 'Warehouse')
		sn_list = frappe.db.get_value('Work Order', doc.name, 'serial_no_data')
		parent = stock_entry_for_out(s, branch, sn_list, frappe.db.get_value('Work Order', doc.name, 'item_qty'))
		cut_order_generation(doc.name, doc.sales_invoice_no)	

def add_to_serial_no(args, work_order, sn_list=None, qc=0, emp=None):
	if sn_list:
		serial_no_list = sn_list
	else:
		serial_no_list = frappe.db.get_value('Work Order', work_order, 'serial_no_data')
	if serial_no_list:
		serial_no_list = cstr(serial_no_list).split('\n')
		for serial_no in serial_no_list:
			make_serial_no_log(serial_no, args, work_order, qc, emp)

def stock_entry_for_out(args, target_branch, sn_list, qty):
	if target_branch != get_user_branch():
		parent = frappe.db.get_value('Stock Entry Detail', {'target_branch':target_branch, 'docstatus':0, 's_warehouse': get_branch_warehouse(get_user_branch())}, 'parent')
		if parent:
			obj = frappe.get_doc('Stock Entry', parent)
			stock_entry_of_child(obj, args, target_branch, sn_list, qty)
			obj.posting_date = nowdate()
			obj.posting_time = nowtime()
			obj.fiscal_year = frappe.db.get_value('Global Defaults',None,'current_fiscal_year')
			obj.save(ignore_permissions=True)
		else:
			parent = make_StockEntry(args, target_branch, sn_list, qty)
		return parent
	else:
		return "Completed"

def make_StockEntry(args, target_branch, sn_list, qty):
	ste = frappe.new_doc('Stock Entry')
 	ste.purpose_type = 'Material Out'
 	ste.purpose ='Material Issue'
 	ste.branch = get_user_branch()
 	ste.posting_date = nowdate()
 	ste.posting_time = nowtime()
 	ste.fiscal_year = frappe.db.get_value('Global Defaults',None,'current_fiscal_year')
 	ste.from_warehouse = get_branch_warehouse(get_user_branch())
 	ste.t_branch = target_branch
 	stock_entry_of_child(ste, args, target_branch, sn_list, qty)
 	ste.save(ignore_permissions=True)
 	return ste.name

def stock_entry_of_child(obj, args, target_branch, sn_list, qty):
	ste = obj.append('mtn_details', {})
	incoming_rate_args = get_args_list(args, get_branch_warehouse(get_user_branch()), qty, sn_list)
	ste.s_warehouse = get_branch_warehouse(get_user_branch())
	ste.target_branch = target_branch
	ste.t_warehouse = get_branch_warehouse(target_branch)
	ste.qty = qty
	ste.serial_no = sn_list
	ste.incoming_rate = get_incoming_rate(incoming_rate_args) or 1.0
	ste.conversion_factor = 1.0
	ste.work_order = args.get('work_order')
	# Suyash 'sales_invoice_no and customer_name are added in custom field in stock_entry child table'
	ste.sales_invoice_no = frappe.db.get_value('Work Order',args.get('work_order'),'sales_invoice_no') if args.get('work_order') else ''
	ste.customer_name = frappe.db.get_value('Work Order',args.get('work_order'),'customer_name') if args.get('work_order') else ''
	if args.get('work_order'):
		ste.trial_date = frappe.db.get_value('Work Order',args.get('work_order'),'trial_date') or ''
		ste.delivery_date = frappe.db.get_value('Work Order',args.get('work_order'),'delivery_date') or ''
	ste.item_code = args.get('item')
	ste.item_name = frappe.db.get_value('Item', ste.item_code, 'item_name')
	ste.stock_uom = frappe.db.get_value('Item', ste.item_code, 'stock_uom')
	company = frappe.db.get_value('Global Defaults', None, 'company')
	ste.expense_account = frappe.db.get_value('Company', company, 'default_expense_account')
	ste.cost_center = get_branch_cost_center(get_user_branch()) or 'Main - '+frappe.db.get_value('Company', company, 'abbr')
	return "Done"

def get_args_list(args, warehouse, qty, sn_list):
	return	frappe._dict({
				"item_code": args.get('item'),
				"warehouse": warehouse,
				"posting_date": nowdate(),
				"posting_time": nowtime(),
				"qty": qty,
				"serial_no": sn_list
			})


def validate_work_order(args):
	if args.get('work_order'):
		if cint(frappe.db.get_value('Work Order', args.get('work_order'), 'docstatus')) != 1:
			frappe.throw(_("You must have to submit the work order {0} for releasing").format(args.get('work_order')))
		else:
			sales_work_status = frappe.db.sql("""select a.name from `tabTrial Dates` a, `tabTrials` b
				where a.parent = b.name and a.work_status = 'Open' and b.work_order = '%s'"""%(args.get('work_order')))
			if not sales_work_status and frappe.db.get_value('Trials', {'work_order': args.get('work_order')}, 'name'):
				frappe.throw(_("You must have to open the Trials for work order {0}").format(args.get('work_order')))			

def get_target_branch(invoice_no, args):
	branch = frappe.db.sql(""" Select a.branch, a.name from `tabProcess Log` a, `tabProduction Dashboard Details` b 
		where a.parent = b.name and work_order='%s' and sales_invoice_no='%s' and a.idx=1"""%(args.get('work_order'), invoice_no))
	if branch:
		return branch[0][0], branch[0][1]

def update_work_order_status(work_order, status):
	frappe.db.sql("""update `tabWork Order` set status= '%s' 
		where name='%s'"""%(status, work_order)) 

def prepare_serial_no_list(serial_no_list, process, process_status):
	if serial_no_list:
		serial_no_list = cstr(serial_no_list).split('\n')
		for serial_no in serial_no_list:
			update_serial_no_status(serial_no, process, process_status)

def update_serial_no_status(serial_no, process, process_status):
	if process_status!='Pending':
		validate_status(serial_no, process_status)
	frappe.db.sql(""" update `tabSerial No` set process = '%s', process_status = '%s' 
		where name='%s'"""%(process, process_status, serial_no))

def get_serial_no(doctype, txt, searchfield, start, page_len, filters):
	return new_common_get_serial_no(filters)
	
def new_common_get_serial_no(filters):
	if filters.get('trial_no'):
		return frappe.db.sql(""" select name from `tabSerial No` where name in (select
			trials_serial_no_status from `tabTrials` where work_order='%s') and warehouse='%s'
			and (select status from `tabWork Order` where name='%s') = 'Release' and item_code='%s'"""%(filters.get('work_order'), get_branch_warehouse(get_user_branch()), filters.get('work_order'), filters.get('item_code')))
	else:
		filters_dict = {'wo':filters.get('work_order'),'process':filters.get('process'),'warehouse': get_branch_warehouse(get_user_branch()),'cond':'', 'item_code': filters.get('item_code')}
		idx_no = frappe.db.sql(""" select idx from  `tabProcess Wise Warehouse Detail` where parent='%(wo)s' and process='%(process)s'   """%(filters_dict),as_list=1)
		cond = ''
		if cint(idx_no[0][0]) !=1:
			cond = "WHERE\
						    (\
						        SELECT\
						            status\
						        FROM\
						            `tabSerial No Detail`\
						        WHERE\
						            parent=my_table.name\
						        AND process=\
						            (\
						                SELECT\
						                    process\
						                FROM\
						                    `tabProcess Wise Warehouse Detail`\
						                WHERE\
						                    parent='%(wo)s'\
						                AND idx <\
						                    (\
						                        SELECT\
						                            idx\
						                        FROM\
						                            `tabProcess Wise Warehouse Detail`\
						                        WHERE\
						                            parent='%(wo)s'\
						                        AND process = '%(process)s' )\
						                ORDER BY\
						                    idx DESC limit 1 )\
						        ORDER BY\
						            trial_no limit 1 ) = 'Completed'"%filters_dict
			filters_dict['cond'] = cond

		return frappe.db.sql(""" SELECT
							    my_table.name
							FROM
							    (
							        SELECT
							            name
							        FROM
							            `tabSerial No`
							        WHERE
							            warehouse = '%(warehouse)s'
							        AND work_order='%(wo)s' AND item_code = '%(item_code)s'
							        AND (
							                SELECT
							                    status
							                FROM
							                    `tabWork Order`
							                WHERE
							                    name='%(wo)s') = 'Release') AS my_table %(cond)s """%(filters_dict),as_list=1)


def validate_status(serial_no, process_status):
	mapper = {'Closed':'Open', 'Open': 'Closed'}
	data = frappe.db.get_value('Serial No', serial_no, 'process_status')
	if mapper[process_status] != data:
		frappe.throw(_("Either process is closed or last process is not completed"))

def open_next_branch(pdd, idx):
	if pdd and idx:
		return frappe.db.get_value('Process Log',{'parent':pdd, 'idx':idx}, '*')

def check_previous_is_closed(serial_no, args, work_order):
	if frappe.db.get_value('Trials', {'pdd': args.parent, 'work_order': work_order}, 'trials_serial_no_status') != serial_no:
		process = frappe.db.sql("""select process from `tabProcess Wise Warehouse Detail` where 
			parent='%s' and idx < (select idx from `tabProcess Wise Warehouse Detail` where 
			parent='%s' and process='%s') order by idx desc limit 1"""%(args.parent, args.parent, args.process_name), as_list=1)
		if process:
			serial_no_data = frappe.db.get_value('Serial No Detail', {'parent': serial_no, 'process': process[0][0]}, '*')
			if serial_no_data.status != 'Completed':
				frappe.throw(_('You have not closed previous process or trials'))
			elif cint(serial_no_data.has_qc) == 1 and qc_completed != 'Completed':
				frappe.throw(_('Quality checking is pending for previous process or trials'))
	else:
		check_previous_is_closed_for_trials(serial_no, args, work_order)

def check_previous_is_closed_for_trials(serial_no, args, work_order):
	cond = "1=1"
	if args.trials:
		cond = "trials='%s'"%(args.trials)
	process_detail = frappe.db.sql("""select process_name, trials from 
		`tabProcess Log` where parent='%s' and idx < (select idx from `tabProcess Log` 
		where parent='%s' and process_name='%s' and %s ) and skip_trial!=1 
		order by idx desc limit 1"""%(args.parent, args.parent, args.process_name, cond), as_list=1)

	if process_detail:
		if process_detail[0][1]:
			if frappe.db.get_value('Serial No Detail', {'parent': serial_no, 'process': process_detail[0][0], 'trial_no': process_detail[0][1]}, 'status') != 'Completed':
				frappe.throw(_('You have not closed previous process or trials'))
		elif frappe.db.get_value('Serial No Detail', {'parent': serial_no, 'process': process_detail[0][0]}, 'status') != 'Completed':
			frappe.throw(_('You have not closed previous process or trials'))


def make_serial_no_log(serial_no, args, work_order, qc, emp):
	if args:
		# if cint(args.idx)>1:
		# 	check_previous_is_closed(serial_no, args, work_order)
		if args.trials:
			if not frappe.db.get_value('Serial No Detail', {'parent':serial_no, 'process': args.process_name,'trial_no': args.trials,  'work_order': work_order}, 'name'):
				make_sn_detail(serial_no, args, work_order, qc, emp)
		elif not frappe.db.get_value('Serial No Detail', {'parent':serial_no, 'process': args.process_name, 'work_order': work_order}, 'name'):
			make_sn_detail(serial_no, args, work_order, qc, emp)		

def make_sn_detail(serial_no, args, work_order, qc, emp):
	snd = frappe.new_doc('Serial No Detail')
	snd.process_data = args.process_data
	snd.process = args.process_name
	snd.has_qc = cint(qc)
	snd.trial_no = args.trials
	snd.work_order = work_order
	snd.parenttype = 'Serial No'
	snd.parentfield = 'serial_no_detail'
	snd.assigned_person = emp
	snd.status = 'Assigned'
	# snd.idx_no = args.idx
	snd.parent = serial_no
	snd.save(ignore_permissions=True)

def update_status_to_completed(serial_no, process_data, trial_no, emp_status):
	cond = "1=1"
	if trial_no:
		cond = "trial_no = '%s'"%(trial_no)
	name = frappe.db.sql("""select name from `tabSerial No Detail` where parent='%s'
		and process_data='%s' and  %s"""%(serial_no, process_data, cond), as_list=1)
	if name:
		update_serial_no_log_status(name[0][0], emp_status)

def get_idx_for_serialNo(args, pdd, process):
	if args.tailor_process_trials:
		return frappe.db.get_value('Process Log' ,{'parent': pdd, 'process_name': process, 'trials':args.tailor_process_trials}, 'idx')
	else:
		return  frappe.db.get_value('Process Log' ,{'parent': pdd, 'process_name': process}, 'idx')

def check_for_reassigned(serial_no, args, process):
	cond = "1=1"
	if args.tailor_process_trials:
		cond = "trial_no='%s'"%(args.tailor_process_trials)

	name = frappe.db.sql("""select name from `tabSerial No Detail`
		where parent='%s' and process='%s' and status='Completed' and %s"""%(serial_no, process, cond), as_list=1)
	if name:
		update_serial_no_log_status(name[0][0], 'Assigned')
	else:
		frappe.throw(_("already completed"))

def update_serial_no_log_status(name, status):
	frappe.db.sql("Update `tabSerial No Detail` set status='%s' where name='%s'"%(status, name))


def make_stock_entry_against_qc(doc, method):
	if doc.get('qa_specification_details'):
		for data in doc.get('qa_specification_details'):
			if data.status == 'Rejected':
				frappe.throw(_('Quality checking is rejected at row {0}').format(data.idx))
			elif doc.serial_no_data:
				update_QI_for_SerialNo(doc, data)
		make_ste_for_QI(doc, data)
		update_trials_status(doc)

def update_trials_status(self):
	if self.trial_no and self.tdd and self.pdd:
		frappe.db.sql(""" update `tabTrial Dates` set production_status='Closed'
			where parent='%s' and trial_no='%s' and process='%s' """%(self.tdd, cint(self.trial_no),self.process))
		frappe.db.sql(""" update `tabProcess Log` set completed_status = 'Yes'
			where trials=%s and parent = '%s'	and process_name='%s' """%(cint(self.trial_no), self.pdd,self.process))

def update_QI_for_SerialNo(doc, data):
	sn_list = cstr(doc.serial_no_data).split('\n')
	cond = "1=1"
	if doc.process:
		cond = "process = '%s'"%(doc.process)
	elif doc.process and doc.trial_no:
		cond = "process = '%s' and trial_no='%s'"%(doc.process, doc.trial_no)
	for serial_no in sn_list:
		frappe.db.sql(""" update `tabSerial No Detail` set qc_completed='Completed' where 
			parent= '%s' and work_order='%s' and %s"""%(serial_no, doc.work_order, cond))

def make_ste_for_QI(self, data):
	details = find_next_process(self.pdd, self.process, self.trial_no)
	target_branch = get_branch(self, details)
	args = {'work_order': self.work_order, 'status': 'Release', 'item': self.item_code}
	parent = stock_entry_for_out(args, target_branch, self.serial_no_data, self.sample_size)

	if parent and self.tdd and self.trial_no:
		frappe.db.sql("""update `tabTrial Dates` set quality_check_status='Completed' where 
			parent='%s' and trial_no = '%s'"""%(self.tdd, self.trial_no))

def get_branch(self, pdlog):
	if pdlog:
		branch = pdlog.branch	
	elif not self.trial_no:
		branch = frappe.db.get_value('Production Dashboard Details', self.pdd, 'end_branch')
		update_serial_no_status_completed(self.serial_no_data)
	if self.trial_no and self.tdd:
		branch = frappe.db.get_value('Trial Dates', {'parent': self.tdd, 'trial_no': self.trial_no}, 'trial_branch')	
	return branch

def update_serial_no_status_completed(serial_no):
	sn = cstr(serial_no).split('\n')
	for serial_no in sn:
		if serial_no:
			frappe.db.sql("update `tabSerial No` set completed = 'Yes' where name = '%s'"%(serial_no))

def update_QI_status(doc, method):
	msg = get_QI_status(doc)
	frappe.db.sql("""update `tabProduction Dashboard Details` set 
		qi_status='%s' where name = '%s'"""%(msg, doc.pdd))
	frappe.db.sql("""update `tabProcess Allotment` set 
		qi_status='%s' where pdd = '%s' and process = '%s'"""%(msg, doc.pdd, doc.process))

def get_QI_status(self):
	msg = 'Accepted'
	for data in self.get('qa_specification_details'):
		if data.status == 'Rejected':
			msg = 'Rejected'
	return msg
	
#Rohit
def update_serial_noInto(self):
	try:
		serial_no_mapper = get_serial_no_mapper(self)
		for d in self.get('entries'):
			if serial_no_mapper.get(d.item_code):
				frappe.db.sql(""" update `tabSales Invoice Item` set serial_no='%s'
					where name = '%s'"""%(serial_no_mapper.get(d.item_code), d.name))
	except Exception:
		frappe.msgprint(Exception)

def get_serial_no_mapper(self):
	mapper_list = {}
	for d in self.get('work_order_distribution'):
		if d.serial_no_data:
			if mapper_list.get(d.tailoring_item):
				val = mapper_list.get(d.tailoring_item) + '\n' + d.serial_no_data
				if mapper_list.has_key(d.tailoring_item):
					del mapper_list[d.tailoring_item]
				mapper_list.setdefault(d.tailoring_item, val)
			else:
				mapper_list.setdefault(d.tailoring_item, d.serial_no_data)
	return mapper_list

# Rohit
def update_WoCount(doc, method):
	count = frappe.db.sql(""" select count(name) from `tabWork Order Distribution`
		where parent = '%s'	"""%(doc.name), as_list=1)
	if count:
		data = frappe.db.sql(""" select * from `tabWork Order Distribution` where
			parent = '%s'	"""%(doc.name), as_dict=1)
		if data:
			for d in data:
				frappe.db.sql(""" update `tabWork Order` set total_process = '%s', current_process='%s'
					where name = '%s'"""%(count[0][0], d.idx, d.tailor_work_order))

def validate_branch(doc):
	if not get_user_branch():
		frappe.throw(_("Define branch to user"))

def validate_duplicate_work_order(work_order):
	if frappe.db.get_value('Production Dashboard Details', {'work_order': work_order}, 'name'):
		frappe.throw(_('Duplicate work order found please contact to support team'))

def validations(doc, method):
	validate_trial_date(doc)

def validate_trial_date(self):
	if not self.trial_date:
		status = get_Trials_Info(self) # check has a trial
		if status == False:
			frappe.throw(_("Trial date is mandatory"))

def get_Trials_Info(self):
	if self.get('sales_invoice_items_one'):
		for d in self.get('sales_invoice_items_one'):
			data = frappe.db.sql(""" select name from `tabProcess Item` where parent = '%s' and trials = 1"""%(d.tailoring_item_code))
			if data:
				return False
	return True

def update_serial_no_for_gift_voucher(doc,method):
	if doc.is_pos == True:
		update_serial_no(doc,method)


def update_serial_no(doc,method):
	for row in doc.get('entries') if  doc.get('entries') else doc.get('delivery_note_details'):		
		item_group = frappe.db.get_value('Item',row.item_code,'item_group')
		if item_group == 'Gift Voucher':
			serial_no_list = row.serial_no.split('\n')
			for serial_no in serial_no_list:
				my_doc = frappe.get_doc('Serial No',serial_no)
				my_doc.gift_voucher_amount = row.rate
				my_doc.save(ignore_permissions=True)


def validation_for_jv_creation(doc,method):
	for row in doc.get('merchandise_item'):
		if frappe.db.get_value('Item',row.merchandise_item_code,'item_group') == 'Gift Voucher':
			check_gift_voucher_account()
			check_availability_of_gift_voucher(row.merchandise_item_code,row.merchandise_qty,doc.customer)
		if row.free == 'Yes':
			create_jv(doc.name,cint(row.merchandise_qty),row.merchandise_item_code)


def check_for_pos(doc,method):
	if doc.is_pos == True:
		for row in doc.get('entries'):
			if frappe.db.get_value('Item',row.merchandise_item_code,'item_group') == 'Gift Voucher' and row.amount==0:
				check_gift_voucher_account()
				check_availability_of_gift_voucher(row.merchandise_item_code,row.merchandise_qty,doc.customer)
				create_jv(doc.name,cint(row.merchandise_qty),row.merchandise_item_code)




def check_gift_voucher_account():
	company = frappe.db.get_value('Global Defaults',None,'default_company')
	gift_voucher_account = frappe.db.get_value('Company',company,'gift_voucher_account')
	if not gift_voucher_account:
		frappe.throw("Please Set Gift Voucher Account in default company")
	return gift_voucher_account	



def check_availability_of_gift_voucher(item_code,quantity,customer):
	if item_code and quantity:
		warehouse = frappe.db.get_value('Branch',get_user_branch(),'warehouse')
		count = frappe.db.sql(""" select count(sn.name) from `tabSerial No` sn join `tabGift Voucher` gv on sn.name = gv.serial_no
			where sn.item_code='{0}' and sn.warehouse='{1}' and sn.status='Available' and gv.to_date >curdate()  """.format(item_code,warehouse),as_list=True)
		if count[0][0] >= quantity:
			pass
		else:
			frappe.throw("Gift voucher Not available for {0} ".format(item_code))	




def create_jv(sales_invoice_no, quantity,item_code):
	company = frappe.db.get_value('Global Defaults',None,'default_company')
	cost_center = frappe.db.get_value('Company',company,'cost_center')
	marketing_account = frappe.db.sql("select name from `tabAccount` where name like '%Marketing Expenses%' limit 1 ",as_list=1)
	jv = frappe.new_doc('Journal Voucher')
	jv.voucher_type = 'Journal Entry'
	jv.cheque_no = ''.join(random.choice(string.ascii_uppercase) for i in range(7))
	jv.posting_date = nowdate()
	jv.fiscal_year = frappe.db.get_value('Global Defaults', None, 'current_fiscal_year')
	jv.cheque_date = nowdate()
	jv.save(ignore_permissions=True)
	other_details = [{'account':marketing_account[0][0],'debit':cint(frappe.db.get_value('Item',item_code,'redeem_amount')) * quantity,'cost_center':get_branch_cost_center(get_user_branch()) or cost_center },{'account':check_gift_voucher_account(),'credit':cint(frappe.db.get_value('Item',item_code,'redeem_amount')) * quantity,'cost_center':get_branch_cost_center(get_user_branch()) or cost_center}]
	make_gl_entry(jv.name, other_details)
	jv = frappe.get_doc('Journal Voucher', jv.name)
	jv.submit()
	return jv.name

def make_gl_entry(parent,args):
	for s in args:
		jvd = frappe.new_doc('Journal Voucher Detail')
		jvd.parent = parent
		jvd.parenttype = 'Journal Voucher'
		jvd.mode = s.get('mode')
		jvd.parentfield = 'entries'
		jvd.cost_center = s.get('cost_center')
		jvd.account = s.get('account')
		jvd.credit = s.get('credit')
		jvd.debit = s.get('debit')
		jvd.against_invoice = s.get('invoice')
		jvd.save()
	return "Done"

def get_earning_type(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql(""" select name from `tabEarning Type` where docstatus != 2 and name not in ('Extra Charges','Overtime','Wages') """)						


def get_deduction_type(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql(""" select name from `tabDeduction Type` where docstatus != 2 and name not in ('Late Work','Drawings','Loan') """)						


@frappe.whitelist()
def get_all_serial_no(filters):
	filters = eval(filters)
	return new_common_get_serial_no(filters)


def validate_all_wo_submitted(doc,method):
	wo_details = frappe.db.sql("select name from `tabWork Order` where sales_invoice_no = '{0}'  ".format(doc.name),as_list=1)
	for work_order in wo_details:
		if frappe.db.get_value("Work Order",work_order[0],'docstatus') != 1:
			frappe.throw("Sales Invoice {0} can not be Submiited beacause Work order {1} is not Submitted".format(doc.name,work_order[0]))


def validate_for_item_qty(doc,method):
	for row in doc.get('sales_invoice_items_one'):
		if row.previous_quantity:
			if cint(row.previous_quantity) != cint(row.tailoring_qty):
				frappe.throw("{0} item quantity has been edited from {1} to {2} for Row {3} .Please Reset it to Previous quantity {4} ".format(row.tailoring_item_code,row.previous_quantity,row.tailoring_qty,row.idx,row.previous_quantity))
		else:
			total_qty = frappe.db.sql("select sum(tailor_qty) as qty from `tabWork Order Distribution` where  parent='%s' and clubbed_product_name='%s' "%(doc.name,row.tailoring_item_code),as_list=1)
			if total_qty[0][0]:

				if cint(total_qty[0][0]) != cint(row.tailoring_qty) and not frappe.db.get_value('Item',row.tailoring_item_code,'is_clubbed_product'):
					frappe.throw("{0} item quantity has been edited from {1} to {2} for Row {3} .Please Reset it to Previous quantity {4} ".format(row.tailoring_item_code,cint(total_qty[0][0]),row.tailoring_qty,row.idx,cint(total_qty[0][0])))
			
				if frappe.db.get_value('Item',row.tailoring_item_code,'is_clubbed_product'):
					
					sales_bom_items = frappe.db.sql("""Select item_code,qty FROM `tabSales BOM Item` WHERE 
						parent ='%s' and parenttype = 'Item' """%(row.tailoring_item_code), as_list=1)
					
					single_bom_qty = 0.0
					for row1 in sales_bom_items:
						single_bom_qty += cint(row1[1])
					original_qty = cint(total_qty[0][0]) / cint(single_bom_qty)	
					if cint(total_qty[0][0]) != ( cint(row.tailoring_qty) * cint(single_bom_qty) ):		
						frappe.throw(" Clubbed Product {0} item quantity has been edited from {1} to {2} for Row {3} .Please Reset it to Previous quantity {4} ".format(row.tailoring_item_code,original_qty,row.tailoring_qty,row.idx,original_qty ))
						

def validate_for_duplicate_item(doc,method):
	item_list = []
	for row in doc.get('sales_invoice_items_one'):
		if row.tailoring_item_code in item_list:
			frappe.throw("Duplicate Entry Of Item {0} not allowed".format(row.tailoring_item_code))
		else:
			item_list.append(row.tailoring_item_code)

def validate_for_split_qty(doc,method):
	for row in doc.get('sales_invoice_items_one'):
		if row.check_split_qty and not row.split_qty_dict:
			frappe.throw("Split Quantity is not booked against item '{0}' for row {1}.Please click on 'Split Qty' Button for Booking purpose Else uncheck option 'Check Split Qty' on row {2} ".format(row.tailoring_item_code,row.idx,row.idx))
		if not row.check_split_qty and  row.split_qty_dict:
			frappe.throw("Please check option 'Check Split Qty' for row {0} because Split quantity is booked against item '{1}'".format(row.idx,row.tailoring_item_code))
		total_qty = 0.0
		if row.check_split_qty and  row.split_qty_dict:
			split_qty_dict = eval(row.split_qty_dict)
			for split_row in split_qty_dict:
				qty = split_qty_dict.get(split_row).get('qty')
				total_qty += cint(qty)
			if total_qty != row.tailoring_qty:
				frappe.throw("Split Qty booked for item '{0}' on row {1} is not equal to Quantity {2}".format(row.tailoring_item_code,row.idx,row.tailoring_qty))



def validation_for_deleted_rows(doc,method):
	wo_dict = validate_for_wod_deleted_rows(doc,method)
	validate_for_sales_item_one_deleted_rows(doc,method,wo_dict)
	

def validate_for_wod_deleted_rows(doc,method):
	wo_dict ={}
	for wo_row in doc.get('work_order_distribution'):
		new_qty =0.0
		if not wo_dict.has_key(cstr(wo_row.clubbed_product_name)):
			wo_dict[wo_row.clubbed_product_name] = {'qty':cint(wo_row.tailor_qty),'row_idx':[cstr(wo_row.idx)]} 	
			continue
		if wo_dict.has_key(cstr(wo_row.clubbed_product_name)):
			new_qty   =  wo_dict[wo_row.clubbed_product_name].get('qty') +  cint(wo_row.tailor_qty)
			wo_dict[wo_row.clubbed_product_name]['qty'] = new_qty
			wo_dict[wo_row.clubbed_product_name].get('row_idx').append(cstr(wo_row.idx))
	return wo_dict		


def validate_for_sales_item_one_deleted_rows(doc,method,wo_dict):
	sales_dict={}
	for sales_row in doc.get('sales_invoice_items_one'):
		sales_dict[sales_row.tailoring_item_code] = [sales_row.tailoring_qty,sales_row.idx]
	new_validations(doc,method,sales_dict,wo_dict)	


def new_validations(doc,method,sales_dict,wo_dict):			
	for sales_item,value in sales_dict.items():
		if wo_dict.has_key(sales_item):
			if cint(value[0]) != cint(wo_dict.get(sales_item)['qty']) and not frappe.db.get_value('Item',sales_item,'is_clubbed_product'):
				frappe.throw("You have deleted rows against item {0} from Work Order distribution table.Please delete rows against item {1} from Work Order Distribution table for rows {2} and  row {3} in Tailoring Product table ".format(sales_item,sales_item, ','.join( wo_dict.get(sales_item)['row_idx'] ),value[1] ))
			
			if frappe.db.get_value('Item',sales_item,'is_clubbed_product'):
				
				sales_bom_items = frappe.db.sql("""Select item_code,qty FROM `tabSales BOM Item` WHERE 
							parent ='%s' and parenttype = 'Item' """%(sales_item), as_list=1)
			
				single_bom_qty = 0.0
				for row in sales_bom_items:
					single_bom_qty += cint(row[1])	

				if (cint(value[0]) * single_bom_qty) != cint(wo_dict.get(sales_item)['qty']):	
					frappe.throw("You have deleted rows for clubbed product {0} from Work Order Distribution table. Please delete rows {1} from  Work Order Distribution table and row no {2} from Tailoring Product table".format(sales_item,','.join( wo_dict.get(sales_item)['row_idx'] ),value[1] ))
		
		if not wo_dict.has_key(sales_item):			
			
			for row in doc.get('sales_invoice_items_one'):
				if row.tailoring_item_code == sales_item:
					add_data_for_deleted_rows(doc,row)

	for wo_item,value in wo_dict.items():				
		if not sales_dict.has_key(wo_item):
			if not frappe.db.get_value('Item',wo_item,'is_clubbed_product'):
				frappe.throw("You have deleted Item {0} from Tailoring Product table.Please delete row {1} from  Work Order Distribution table".format(wo_item, ','.join( wo_dict.get(wo_item)['row_idx'] ) ))
			elif frappe.db.get_value('Item',wo_item,'is_clubbed_product'):	
				frappe.throw("You have deleted clubbed product {0} from Tailoring Product table.Please delete rows {1} from  Work Order Distribution table".format(wo_item, ','.join( wo_dict.get(wo_item)['row_idx'] ) ))



# def validate_for_wod_deleted_rows(doc,method):
# 	for sales_row in doc.get('sales_invoice_items_one'):
# 		if not frappe.db.get_value('Item',sales_row.tailoring_item_code,'is_clubbed_product'):
# 			total_qty = 0.0
# 			idx_list = []
# 			flag_for_new_item = True
# 			for wo_row in doc.get('work_order_distribution'):
# 				if wo_row.tailoring_item == sales_row.tailoring_item_code and wo_row.tailoring_item == wo_row.clubbed_product_name:
# 					flag_for_new_item = False
# 					total_qty += cint(wo_row.tailor_qty)
# 					idx_list.append(cstr(wo_row.idx))	
# 			if cint(total_qty) != cint(sales_row.tailoring_qty) and flag_for_new_item == False:
# 				idx_string = ''
# 				if idx_list:
# 					idx_string = "for row no %s in Work Order Distribution Table &"%(','.join(idx_list))
# 				frappe.throw("Difference between quantity in Tailoring Product table & Work Order Distribution table for Item  '{0}' because you have deleted some rows from Work Order Distribution table.Please delete rows against item '{1}' {2} for row no {3} in Tailoring Product Table".format(sales_row.tailoring_item_code,sales_row.tailoring_item_code,idx_string,sales_row.idx))				
		
# 		elif frappe.db.get_value('Item',sales_row.tailoring_item_code,'is_clubbed_product'):
# 			total_qty = 0.0
# 			idx_list = []
# 			flag_for_new_item = True
			
# 			for wo_row in doc.get('work_order_distribution'):
# 				if wo_row.clubbed_product_name == sales_row.tailoring_item_code:
# 					flag_for_new_item = False
# 					total_qty += cint(wo_row.tailor_qty)
# 					idx_list.append(cstr(wo_row.idx))

# 			sales_bom_items = frappe.db.sql("""Select item_code,qty FROM `tabSales BOM Item` WHERE 
# 							parent ='%s' and parenttype = 'Item' """%(sales_row.tailoring_item_code), as_list=1)
			
# 			single_bom_qty = 0.0
			
# 			for row in sales_bom_items:
# 				single_bom_qty += cint(row[1])		
			
# 			if cint(total_qty) !=  ( cint(sales_row.tailoring_qty) * cint(single_bom_qty) ) and flag_for_new_item == False:		
# 				idx_string = ''
# 				if idx_list:
# 					idx_string = "for row no %s in Work Order Distribution Table &"%(','.join(idx_list))
# 				frappe.throw("Clubbed Product Qty for item {0} does not match with Qty in Work Order Distribution table beacause you have deleted rows from Work Order Distribution table.Please delete rows against item '{1}' {2} for row no {3} in Tailoring Product Table".format(sales_row.tailoring_item_code,sales_row.tailoring_item_code,idx_string,sales_row.idx))					

# def validate_for_sales_item_one_deleted_rows(doc,method):
# 	wo_dict = {}
# 	for wo_row in doc.get('work_order_distribution'):
# 		if not wo_dict.has_key(cstr(wo_row.tailoring_item)) and not wo_dict.has_key(cstr(wo_row.clubbed_product_name)):
# 			if wo_row.clubbed_product_name == wo_row.tailoring_item: 
# 				wo_dict[cstr(wo_row.tailoring_item)] = wo_row.tailor_qty
# 			elif wo_row.clubbed_product_name != wo_row.tailoring_item:
# 				wo_dict[cstr(wo_row.clubbed_product_name)] = wo_row.tailor_qty
# 		else:

# 			if wo_row.clubbed_product_name == wo_row.tailoring_item: 
# 				wo_dict[wo_row.tailoring_item] = cint(wo_dict[wo_row.tailoring_item]) + cint(wo_row.tailor_qty)
# 			elif wo_row.clubbed_product_name != wo_row.tailoring_item:
# 				wo_dict[wo_row.clubbed_product_name] = cint(wo_dict[wo_row.clubbed_product_name]) + cint(wo_row.tailor_qty)
			
# 	for key,value in wo_dict.items():
# 		total_qty = 0.0
# 		clubbed_product = ''
# 		clubbed_qty = 0.0
# 		for sales_row in doc.get('sales_invoice_items_one'):
# 			if key == sales_row.tailoring_item_code and not frappe.db.get_value('Item',sales_row.tailoring_item_code,'is_clubbed_product'):				
# 				total_qty = cint(sales_row.tailoring_qty)
# 				break	
# 			if key == sales_row.tailoring_item_code and frappe.db.get_value('Item',sales_row.tailoring_item_code,'is_clubbed_product'):				
# 				clubbed_product = sales_row.tailoring_item_code
# 				clubbed_qty = sales_row.tailoring_qty
# 				break	
		
# 		if frappe.db.get_value("Item",key,'is_clubbed_product'):
# 			sales_bom_items = frappe.db.sql("""Select item_code,qty FROM `tabSales BOM Item` WHERE 
# 							parent ='%s' and parenttype = 'Item' """%(key), as_list=1)
			
# 			single_bom_qty = 0.0
# 			item_list = []
# 			for row in sales_bom_items:
# 				single_bom_qty += cint(row[1])
# 				item_list.append(cstr(row[0])) 
# 			item_string = "for item %s in Work Order Distribution Table"%(','.join(item_list))
				
# 			total_qty = cint(clubbed_qty)  * cint(single_bom_qty)
# 			if total_qty != cint(value):
# 				frappe.throw("Clubbed Product Qty for item '{0}' does not match with Qty in Work Order Distribution table beacause you have deleted rows from Tailoring Product table.Please delete rows against Item {1} from Work Order Distribution table".format(key,item_string))
						
# 		elif not clubbed_product and not frappe.db.get_value("Item",key,'is_clubbed_product'):
# 			if total_qty != cint(value):
# 				frappe.throw("Difference between quantity in Tailoring Product table & Work Order Distribution table for Item  '{0}' because you have deleted rows from Tailoring Product table.Please delete rows against item '{1}' From Work Order Distribution table. ".format(key,key))



def validate_for_reserve_qty(doc,method):
	for row in doc.get('sales_invoice_items_one'):
		if row.fabric_code and frappe.db.get_value('Item', row.fabric_code, 'item_group')=='Fabric':
			if not row.reserve_fabric_qty:
				frappe.throw("Fabric is not Reserved for Item {0} for row {1}".format(row.tailoring_item_code,row.idx))	



def create_event_on_sales_invoice_submission(doc,method):
	for row in doc.get('sales_invoice_items_one'):
		create_event_for_item(row,doc)		


def create_event_for_item(row,my_doc):
	evt = frappe.new_doc('Event')
	evt.branch = my_doc.branch 
	evt.subject = "Customer {0}:Delivery For Item {1}".format(my_doc.customer_name,row.tailoring_item_code)
	evt.description = 'Dear %s, your delivery date for item "%s" with us today. Kindly Collect your item "%s". Thank you.'%(my_doc.customer_name, row.tailoring_item_code,row.tailoring_item_code)
	evt.starts_on = row.tailoring_delivery_date or ''
	evt.sales_invoice_no = my_doc.name
	evt.item_name = row.tailoring_item_code 
	make_appointment_list(evt,my_doc.customer)
	evt.save(ignore_permissions = True)


def make_appointment_list(obj,customer):
	if customer:
		apl = obj.append('appointment_list',{})
		apl.customer = customer
		return "Done"

def update_event_date(doc,method):
	for row in doc.get('sales_invoice_items_one'):
		frappe.db.sql("update `tabEvent` set starts_on = '%s' where sales_invoice_no='%s' and item_name ='%s' "%(row.tailoring_delivery_date,doc.name,row.tailoring_item_code))
		frappe.db.sql(" update `tabSales Invoice Item` set delivery_date ='%s' where parent='%s' and item_code='%s' "%(row.tailoring_delivery_date,doc.name,row.tailoring_item_code))	
		update_delivery_date_on_work_order(doc,row)

def update_delivery_date_on_work_order(doc,row):
	if frappe.db.get_value('Item',row.tailoring_item_code,'is_clubbed_product'):
		result = frappe.db.sql(""" select name from `tabWork Order` where sales_invoice_no='%s' and parent_item_code='%s' """%(doc.name,row.tailoring_item_code	),as_list=1)
	else:
		result = frappe.db.sql(""" select name from `tabWork Order` where sales_invoice_no='%s' and item_code='%s' and parent_item_code is null """%(doc.name,row.tailoring_item_code),as_list=1)	
	frappe.db.sql(""" update `tabWork Order` set delivery_date='%s' where name in (%s) """%(row.tailoring_delivery_date,','.join('"{0}"'.format(w[0]) for w in result)))





