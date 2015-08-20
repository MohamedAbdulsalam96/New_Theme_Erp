# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import cint, cstr, flt, nowdate, nowtime
from frappe import _
from erpnext.accounts.accounts_custom_methods import stock_entry_for_out
import datetime
from tools.custom_data_methods import get_user_branch, get_branch_cost_center, get_branch_warehouse, update_serial_no

class Trials(Document):
	def validate(self):
		self.finished_all_trials_for_SelectedProcess()
		self.make_event_for_trials()
		self.autoOperation()
		self.update_trials_status()
		# self.update_branch_of_warehouse()

	def finished_all_trials_for_SelectedProcess(self):
		if self.finish_trial_for_process and not frappe.db.get_value('Completed Process Log', {'parent':self.name, 'completed_process': self.finish_trial_for_process}, 'completed_process'):
			response = self.make_process_completed_log()
			if response:
				frappe.db.sql("""update `tabProcess Allotment` set process_trials = (select name from `tabCustomer` where 1=2),
					emp_status='', start_date=(select name from `tabSupplier` where 1=2), qc=0 where pdd = '%s' 
					and process='%s'"""%(self.pdd, self.finish_trial_for_process))
				frappe.db.sql(""" update `tabWork Order` set trial_no = (select true from dual where 1=2), trial_date = (select true from dual where 1=2) where work_order_name ='%s'"""%(self.work_order))
				self.prepare_ste_for_finished_process()

	def make_process_completed_log(self):
		obj = self.append('completed_process_log', {})
		obj.completed_process = self.finish_trial_for_process
		idx = frappe.db.sql("select ifnull(max(idx),0) from `tabCompleted Process Log` where parent='%s'"%(self.name), as_list=1)
		obj.idx = cint(idx[0][0]) + 1
		return "Done"

	def prepare_ste_for_finished_process(self):
		for d in self.get('completed_process_log'):
			if d.completed_process and not d.ste_no:
				self.update_process_staus(d)
				branch = self.get_target_branch(d.completed_process)
				ste_status = self.allow_to_make_ste(branch)
				if branch != get_user_branch() and ste_status != 'True':
					s= {'work_order': self.work_order, 'status': 'Release', 'item': self.item_code}
					d.ste_no = stock_entry_for_out(s, branch, self.trials_serial_no_status, 1)

	def allow_to_make_ste(self, branch):
		data = frappe.db.sql(""" select name from `tabStock Entry Detail` where serial_no like '%%%s%%' and item_code = '%s'
			and work_order = '%s' and target_branch = '%s' and s_warehouse = '%s'"""%(self.trials_serial_no_status, self.item_code, self.work_order, branch, get_branch_warehouse(get_user_branch())), as_dict=1)
		msg = 'True' if data else 'False'
		return msg

	def update_process_staus(self, args):
		qc_status = 0
		self.skip_unfinished_trials()
		qc_status = frappe.db.get_value('Process Item', {'parent':self.item_code, 'process_name': args.completed_process}, 'quality_check')
		self.open_trial(qc_status, args.completed_process)

	def skip_unfinished_trials(self):
		for d in self.get('trial_dates'):
			if d.work_status != 'Open' and d.process == self.finish_trial_for_process:
				d.skip_trial = 1
				frappe.db.sql(""" update `tabProcess Log` set skip_trial = 1 where trials = '%s'
					and parent = '%s' and process_name ='%s' """%(d.trial_no, self.pdd,self.finish_trial_for_process))
		return "Done"

	def update_trials_status(self):
		for d in self.get('trial_dates'):
			if cint(d.skip_trial) == 1:
				frappe.db.sql("update `tabProcess Log` set status='Closed' where parent='%s' and trials is null and status!='Closed'"%(self.pdd))

	def autoOperation(self):
		for d in self.get('trial_dates'):
			self.make_auto_ste(d)

	def make_auto_ste(self, trial_data):
		args_obj = {}
		args_obj.setdefault(trial_data.idx, trial_data)
		data = frappe.db.get_value('Process Log', {'parent': self.pdd, 'process_name': trial_data.process, 'trials': trial_data.trial_no}, '*', as_dict=1)
		if data:
			reverse_entry = data.reverse_entry if data.reverse_entry else ''
			if trial_data.production_status == 'Closed' and cint(trial_data.skip_trial) != 1 and cint(self.finished_all_trials)!=1:
				pass
			else:
				self.validate_QI_completed(trial_data, args_obj)
				self.OpenNextTrial(trial_data)
				if trial_data.work_status == 'Open' and cint(trial_data.skip_trial)!=1 and trial_data.production_status!='Closed':
					self.update_trial_date_on_wo_si(trial_data)
					if reverse_entry == 'Pending':
						self.open_trial(trial_data.quality_check, trial_data.process, trial_data)
						if trial_data.trial_branch != data.branch:
							branch = data.branch
							msg = cstr(trial_data.trial_no) + ' ' +cstr(trial_data.production_status)
							self.prepare_for_ste(trial_data, branch, data, msg)

	def validate_QI_completed(self, args, args_obj):
		for obj in args_obj:
			if cint(args.idx) > cint(obj):
				obj = args_obj[obj]
				if cint(obj.quality_check) == 1 and obj.quality_check_status != 'Completed':
					frappe.throw(_("Can not open Trials {0}, because Trial {1} quality checking is pending").format(args.trial_no, obj.trial_no))
				elif obj.production_status != 'Closed':
					frappe.throw(_("Can not open Trials {0}, because Trial {1} was not completed").format(args.trial_no, obj.trial_no))

	def open_trial(self, quality_check, process, trial_data = None):
		cond = "process_trials = (select name from `tabCustomer` where 1=2)"
		if trial_data:
			cond = "process_trials = '%s'"%(trial_data.trial_no)
			self.update_work_order(trial_data)
		if self.pdd:
			frappe.db.sql("""update `tabProcess Allotment` set %s, emp_status='Assigned', start_date=(select name from `tabSupplier` where 1=2), qc=%s where pdd = '%s' 
				and process='%s'"""%(cond,cint(quality_check), self.pdd, process))

	def update_work_order(self, args):
		fabric = frappe.db.get_value('Production Dashboard Details', self.pdd, 'dummy_fabric_code')
		if cint(args.actual_fabric) == 1:
			fabric = frappe.db.get_value('Production Dashboard Details', self.pdd, 'fabric_code')
		if args.work_order:
			frappe.db.sql(""" update `tabWork Order` set trial_no='%s', fabric__code='%s'
				where name = '%s'"""%(args.trial_no, fabric, args.work_order))

	def update_trial_date_on_wo_si(self,args):
		clubbed_product = frappe.db.get_value('Work Order',self.work_order,'parent_item_code')		
		if clubbed_product:
			result = frappe.db.get_value('Sales Invoice Item',{'parent':self.sales_invoice,'item_code':clubbed_product},['name','trial_date'],as_dict=1)			
		elif not clubbed_product:
			result = frappe.db.get_value('Sales Invoice Item',{'parent':self.sales_invoice,'item_code':self.item_code},['name','trial_date'],as_dict=1)	
		self.update_for_recent_trial_date(args,result,clubbed_product)	

	def update_for_recent_trial_date(self,args,result,clubbed_product=None):
		if not result.get('trial_date') or self.convert_string_to_datetime(result.get('trial_date')) > self.convert_string_to_datetime(args.trial_date) if args.trial_date else '' and args.trial_date:
			frappe.db.sql("""UPDATE
							    `tabSales Invoice Item`
							SET
							    trial_date ='%s'
							WHERE
							    name='%s' """%(args.trial_date,result.get('name')))		
			if clubbed_product:
				self.update_all_wo_trial_date_for_clubbed_product(args,clubbed_product)
			if not clubbed_product:	
				self.update_all_wo_trial_date_for_normal_product(args)
	
	def convert_string_to_datetime(self,date):
		date = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
		return date



	def update_all_wo_trial_date_for_clubbed_product(self,args,clubbed_product):
		result = frappe.db.get_values('Work Order',{'sales_invoice_no':self.sales_invoice,'parent_item_code':clubbed_product},'name',as_dict=1)			
		frappe.db.sql(""" UPDATE
							    `tabWork Order`
							SET
							    trial_date='%s'
							WHERE
							    name IN (%s) """%(args.trial_date,','.join('"{0}"'.format(w.get('name')) for w in result )  ))
	
	def update_all_wo_trial_date_for_normal_product(self,args):
		wo_result = frappe.db.sql(""" SELECT
										    name
										FROM
										    `tabWork Order`
										WHERE
										    sales_invoice_no='%s'
										AND item_code='%s'
										AND parent_item_code IS NULL """%(self.sales_invoice,self.item_code),as_list=1)
		frappe.db.sql(""" UPDATE
							    `tabWork Order`
							SET
							    trial_date='%s'
							WHERE
							    name IN (%s) """%(args.trial_date,','.join('"{0}"'.format(w[0]) for w in wo_result)))

	def prepare_for_ste(self, trial_data, branch, data, msg):
		parent = frappe.db.get_value('Stock Entry Detail', {'target_branch':data.branch, 'docstatus':0, 's_warehouse': get_branch_warehouse(trial_data.trial_branch)}, 'parent')
		args = {'qty': 1, 'serial_data': self.trials_serial_no_status, 'work_order': self.work_order, 'item': self.item_code, 'trials': trial_data.next_trial_no}	
		if parent:
			st = frappe.get_doc('Stock Entry', parent)
			self.stock_entry_of_child(st, args, branch)
			st.save(ignore_permissions=True)
		else:
			parent = self.make_stock_entry(branch, args)
		if parent:
			update_serial_no(self.pdd, self.trials_serial_no_status, msg)
			frappe.db.sql(""" update `tabProcess Log` set reverse_entry = 'Done' where name ='%s'"""%(data.name))

	def get_target_branch(self, process):
		name = frappe.db.sql("""select branch from `tabProcess Log` where 
			idx > (select max(idx) from `tabProcess Log` where parent = '%s' and process_name = '%s' 
			order by idx) and parent = '%s' order by idx limit 1 """%(self.pdd, process, self.pdd), as_dict=1)
 		if name:
 			return name[0].branch
 		else:
 			end_branch = frappe.db.get_value("Production Dashboard Details", self.pdd, 'end_branch')
 			if end_branch:
 				frappe.db.sql("update `tabSerial No` set completed = 'Yes' where name = '%s'"%(self.trials_serial_no_status))
 				return end_branch

	def make_stock_entry(self, t_branch, args):
		ste = frappe.new_doc('Stock Entry')
		ste.purpose_type = 'Material Out'
		ste.branch = get_user_branch()
		ste.posting_date = nowdate()
		ste.posting_time = nowtime()
		ste.from_warehouse = get_branch_warehouse(get_user_branch())
		ste.t_branch = t_branch
		ste.purpose ='Material Issue' 		
		self.stock_entry_of_child(ste, args, t_branch)
		ste.save(ignore_permissions=True)
		return ste.name

	def stock_entry_of_child(self, obj, args, target_branch):
		ste = obj.append('mtn_details', {})
		ste.s_warehouse = get_branch_warehouse(get_user_branch())
		ste.target_branch = target_branch
		ste.t_warehouse = get_branch_warehouse(target_branch)
		ste.qty = args.get('qty')
		ste.serial_no = args.get('serial_data')
		ste.incoming_rate = 1.0
		ste.conversion_factor = 1.0
		ste.has_trials = 'Yes'
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
		company = frappe.db.get_value('GLobal Default', None, 'company')
		ste.expense_account = frappe.db.get_value('Company', company, 'default_expense_account')
		return "Done"

	def OpenNextTrial(self, args):
		if (not args.production_status or args.production_status != 'Closed') and args.work_status == 'Open' and cint(args.skip_trial) !=1 :
			frappe.db.sql(""" update `tabProcess Log` set status = 'Open' where parent = '%s'
				and process_name = '%s' and trials = '%s'"""%(self.pdd, args.process, args.trial_no))

	def update_status(self):
		if self.trial_serial_no:  
			self.trials_serial_no_status = self.trial_serial_no

	def make_event_for_trials(self):
		for d in self.get('trial_dates'):
			self.add_trials(d)
			self.create_event(d)

	def add_trials(self,args):
		name = frappe.db.get_value('Process Log', {'process_name': args.process, 'trials': args.trial_no, 'parent':self.pdd},'name')
		if name and args.trial_date:
			frappe.db.sql("update `tabProcess Log` set trials_date = '%s', skip_trial = %s, pr_work_order='%s' where name = '%s'"%(args.trial_date, cint(args.skip_trial), self.work_order, name))
		elif not name and args.trial_date:
			max_id = frappe.db.sql("select ifnull(max(idx),'') from `tabProcess Log` where parent='%s'"%(self.pdd), as_list =1)
			pl = frappe.new_doc('Process Log')
			pl.process_data = frappe.db.get_value('Process Log', {'process_name': args.process, 'trials': cstr(cint(args.trial_no) - 1), 'parent':self.pdd},'process_data')
			pl.skip_trial = cint(args.skip_trial)
			pl.process_name = args.process
			pl.trials_date = args.trial_date
			pl.branch = frappe.db.get_value('Process Wise Warehouse Detail', {'process': args.process, 'parent': self.work_order, 'actual_fabric':1}, 'warehouse') # to retrieve name of the branch where production is happened
			pl.trials = cint(args.trial_no)
			pl.trials_date = args.trial_date
			pl.parent = self.pdd
			if max_id:
				pl.idx = cint(max_id[0][0]) + 1
			pl.parenttype = 'Production Dashboard Details'
			pl.parentfield = 'process_log'
			pl.save(ignore_permissions=True)
	
	def create_event(self, args):
		if not args.event and args.work_status=='Open' and args.trial_date:
			time = datetime.datetime.strptime(args.trial_date, '%Y-%m-%d %H:%M:%S').strftime('%H:%M:%S')
			self.validate_mandatory_field(args)
			evt = frappe.new_doc('Event')
			evt.branch = args.trial_branch 
			evt.subject = args.subject
			evt.description = 'Dear %s, you have an appointment for trial with us at %s today. Kindly revert in case you need to re-schedule. Thank you.'%(self.customer_name, time)
			evt.starts_on = args.trial_date
			evt.ends_on = args.to_time
			self.make_appointment_list(evt)
			evt.save(ignore_permissions = True)
			args.event = evt.name
		else:
			frappe.db.sql("""update `tabEvent` set branch = '%s', starts_on = '%s', ends_on = '%s',
				subject = '%s' where name='%s'"""%(args.trial_branch, args.trial_date, args.to_time, args.subject, args.event))

	def make_appointment_list(self, obj):
		if self.customer:
			apl = obj.append('appointment_list',{})
			apl.customer = self.customer
			return "Done"

	def validate_mandatory_field(self, args):
		if not args.trial_date and not args.subject:
			frappe.throw(_("Mandatory Field: Start on, subject to make an event").format())

	def check_serial_no(self):
		warehouse = get_branch_warehouse(get_user_branch())
		if warehouse and frappe.db.get_value('Serial No', self.trials_serial_no_status, 'warehouse') != warehouse:
			frappe.throw(_('You can not open because serial no {0} is not availble in warehouse {1}'). format(self.trials_serial_no_status, warehouse))
		return True	

	def get_trial_no(self, args):
		trial_no = frappe.db.sql(""" Select max(trial_no) from `tabTrial Dates` where parent = '%s'
			and process = '%s'	"""%(self.name, args.get('process')), as_list=1)
		if trial_no:
			return {'trial_no': cstr(cint(trial_no[0][0])+1)}
		else:
			return {'trial_no': args.get('idx')}

	def PermissionException(self):
		frappe.throw(_("Not allowed to edit once it is closed"))


	def update_process_allotment(self,process):
		if process:
			frappe.db.sql("""update `tabProcess Allotment` set process_trials='' , qc=0 where pdd = '%s' 
				and process='%s'"""%(self.pdd, process))
			self.save()

@frappe.whitelist()
def get_serial_no_data(work_order):
	return frappe.db.get_value('Work Order', work_order, 'serial_no_data') if work_order else ''
