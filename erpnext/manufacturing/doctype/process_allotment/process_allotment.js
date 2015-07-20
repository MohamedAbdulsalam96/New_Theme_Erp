cur_frm.add_fetch('raw_material_item_code', 'item_name', 'raw_material_item_name')
cur_frm.add_fetch('raw_material_item_code', 'stock_uom', 'uom')
doc = cur_frm.doc
cur_frm.fields_dict['sales_invoice_no'].get_query = function(doc) {
	return {
		filters: {
			"docstatus": 1,
		}
	}
}

/*cur_frm.cscript.item = function(doc, cdt, cdn){
	get_server_fields('get_details',doc.item,'',doc ,cdt, cdn,1, function(){
		refresh_field('wo_process')
	})
}*/


cur_frm.cscript.status = function(doc, cdt, cdn){
	var d = locals[cdt][cdn]
	d.trial_change_status='Yes'
	refresh_field('trials_transaction')
	// get_server_fields('on_status_trigger_method',d,'',doc, cdt, cdn, 1, function(){
	// 	refresh_field('wo_process')
	// })
}

// var sn_list=[]
cur_frm.cscript.refresh = function(doc, cdt, cdn){
	sn_list=[];
	cur_frm.cscript.toogle_field(doc)
	// get_server_fields('show_trials_details', '','',doc, cdt, cdn, 1, function(){
	// 	refresh_field('trials_transaction')
	// })
}

// cur_frm.cscript.add = function(doc ,cdt , cdn){
// 	s = check_serial_exist(sn_list, doc.serial_no)
// 	if(s=='Done')
// 	{
// 		if (doc.serial_no && doc. serials_data){
// 			doc.serials_data = doc.serials_data + '\n' + doc.serial_no
// 		}
// 		else{
// 			doc.serials_data = doc.serial_no
// 		}
// 		sn_list.push(doc.serial_no)
// 	}
// 	else{
// 		alert("Serial no already exist")
// 	}
// 	refresh_field('serials_data')

// }

cur_frm.cscript.check_serial_exist= function(sn_list, serial_no){
	msg = "Done"
	sn_list = (sn_list).split('\n')
	$.each(sn_list, function(i){
		if (sn_list[i] == serial_no){
	 		msg="False"
	 	} 
	})
	return msg
}

cur_frm.cscript.process_status= function(doc, cdt, cdn){
	doc.process_status_changes = 'Yes'
	refresh_field('process_status_changes')
}

cur_frm.cscript.emp_status= function(doc, cdt, cdn){
	doc.process_status = 'Open'
	cur_frm.cscript.toogle_field(doc)
 if (doc.emp_status == 'Completed'){
		get_server_fields('find_to_time','','',doc, cdt, cdn, 1, function(r,rt){
			doc.end_date = r['end_date']
			doc.completed_time = r['completed_time']
			refresh_field('end_date')
			refresh_field('completed_time')
		get_server_fields('calculate_wage','','', doc, cdt, cdn, 1, function(){
			refresh_field(['wages','wages_for_single_piece'])
			})
	})
		


	}

if (doc.emp_status == 'Assigned' ||  doc.emp_status == 'Reassigned')
		{

			doc.wages = ''
			doc.wages_for_single_piece = ''
			// doc.process_tailor = ''
			doc.serial_no = ''
			doc.serial_no_data = ''
			doc.start_date =''
			doc.completed_time =''
			doc.task = ''
			doc.work_qty = ''
	}


	refresh_field(['process_status', 'completed_time', 'start_date', 'work_qty','wages','wages_for_single_piece','process_tailor','serial_no','serial_no_data','employee_name','process_tailor','end_date','task'])
}

cur_frm.cscript.process_tailor=function(doc,cdt,cdn){
	cur_frm.cscript.emp_status(doc, cdt, cdn)
	if(doc.emp_status == 'Assigned' ||  doc.emp_status == 'Reassigned'){
		get_server_fields('find_start_time','','', doc, cdt, cdn, 1, function(){
			refresh_field('start_date')
		})


	}

	
		
}

cur_frm.cscript.clear_field= function(doc){
	// if(doc.emp_status == 'Completed'){
	// 	doc.start_date = ''
	// 	doc.work_qty = ''
	// 	doc.estimated_time = ''
 // 		doc.serial_no = ''
	// 	doc.serial_no_data = ''
		
	// }
	//refresh_field(['process_status', 'start_date', 'work_qty', 'end_date', 'estimated_time', 'serial_no', 'serial_no_data','wages'])
}

cur_frm.cscript.toogle_field = function(doc){
	hide_field(['wages', 'extra_charge_amount', 'latework', 'cost'])
	if (doc.emp_status=='Completed')
	{
		doc.process_status = 'Closed'
		// hide_field([ 'start_date', 'end_date']);
		unhide_field([ 'completed_time', 'payment', 'extra_charge', 'deduct_late_work','wages_for_single_piece']);
		payment_dict = {'wages': doc.payment, 'latework': doc.deduct_late_work, 'cost': doc.deduct_late_work, 'extra_charge': doc.extra_charge}
		for (key in payment_dict){

			if (payment_dict[key] == 'Yes'){
				unhide_field(key)
			}else{
				hide_field(key)
			}
			refresh_field(key)
		}
	}else if(doc.emp_status=='Assigned' || doc.emp_status=='Reassigned' || doc.emp_status==''){
		unhide_field(['start_date', 'end_date', 'estimated_time'])
		hide_field([ 'completed_time', 'payment', 'extra_charge', 'deduct_late_work','wages_for_single_piece']);
		// doc.end_date = ''
		// doc.task =''
		

		refresh_field(['process_tailor', 'employee_name', 'start_date', 'end_date', 'estimated_time', 'serial_no', 'serial_no_data', 'work_qty'])
	}
	
}

cur_frm.cscript.assigned= function(doc, cdt, cdn){
	if(doc.emp_status){
		status = cur_frm.cscript.validate_mandatory_fields(doc)
		cur_frm.cscript.validate_serial_no_qty(doc)
		if(status=='true')
		{
			get_server_fields('assign_task_to_employee','','',doc, cdt, cdn,1, function(){
				refresh_field('employee_details')
				refresh_field('task')
			})	
		}
	}else{
		alert("Select status")
	}
	
}


cur_frm.cscript.validate_serial_no_qty = function  (doc) {
	if (doc.serial_no_data){
		my_array = doc.serial_no_data.split('\n')
		my_array = $.map(my_array,function(key){
			key = key.trim()
			return (key!='' ? key : null)			
		})
		if(my_array.length != doc.work_qty){
			doc.work_qty = my_array.length
			refresh_field('work_qty')
		} 


	}
}


cur_frm.cscript.validate_mandatory_fields= function(doc){
	data = {'Tailor': doc.process_tailor, 'Start Date': doc.start_date, 'End Date': doc.end_date,'Employee Name':doc.employee_name,'Serial No Data':doc.serial_no_data,'Qty':doc.work_qty}

	if(doc.emp_status=='Completed'){
		data['Completed Time']=doc.completed_time
		data['Payment']=doc.payment
		data['Deduct Late Work']=doc.deduct_late_work
		data['Extra charge']=doc.extra_charge

		}
	status = 'true'

	for(key in data){
		if(!data[key]){
			alert("Mandatory Fields: "+key+"")
			status = 'false';
			break;
		}
	}

	return status
}

cur_frm.cscript.deduct_late_work = function(doc){
	if(doc.deduct_late_work == 'Yes'){
		unhide_field(['latework', 'cost']);		
	}else{
		doc.latework = 0.0
		doc.cost = 0.0
		refresh_field(['latework','cost'])
		hide_field(['latework', 'cost']);
	}
}

cur_frm.cscript.work_qty = function(doc, cdt, cdn){
	get_server_fields('calculate_estimates_time','','',doc, cdt, cdn,1, function(){
		refresh_field(['estimated_time', 'end_date'])	
	})
	
}

cur_frm.cscript.payment = function(doc, cdt, cdn){
	if(doc.payment == 'Yes'){
		unhide_field('wages');		
	}else{
		doc.wages = 0.0
		refresh_field('wages')
		hide_field('wages');	
	}
	
	get_server_fields('calculate_wages','','',doc, cdt, cdn,1, function(){
		refresh_field('wages')	
	})
}

cur_frm.cscript.latework = function(doc, cdt, cdn){
	get_server_fields('calc_late_work_amt','','',doc, cdt, cdn,1, function(){
		refresh_field('cost')	
	})
	
}

cur_frm.cscript.validate = function(doc, cdt, cdn){
	setTimeout(function(){refresh_field(['employee_details', 'task']); cur_frm.cscript.clear_field(doc);},1000)
	
}

cur_frm.cscript.extra_charge = function(doc, cdt, cdn){
	if(doc.extra_charge == 'Yes'){
		get_server_fields('cal_extra_chg','','',doc, cdt, cdn,1, function(){
			unhide_field('extra_charge_amount');
			refresh_field('extra_charge_amount')	
	})
				
	}else{
		doc.extra_charge_amount = 0.0
		refresh_field('extra_charge_amount')
		hide_field('extra_charge_amount');	
	}
}

cur_frm.cscript.end_date = function(doc, cdt, cdn){
	get_server_fields('find_to_time','manual','',doc, cdt, cdn, 1, function(){
			refresh_field(['end_date', 'completed_time'])
	})
}


cur_frm.cscript.process_trials = function(doc, cdt, cdn){
	if(doc.process_trials){
		get_server_fields('get_trial_serial_no', '', '', doc, cdt, cdn, 1, function(){
			refresh_field(['serial_no_data', 'work_qty'])
		})
	}
}

cur_frm.fields_dict['serial_no'].get_query = function(doc) {
	return{
		query: "erpnext.accounts.accounts_custom_methods.get_serial_no",
		filters: {'branch': doc.branch, 'process': doc.process, 'work_order': doc.process_work_order, 'trial_no':doc.process_trials, 'item_code': doc.item}
	}
}

cur_frm.cscript.serial_no = function(doc, cdt, cdn){
	status = 'Done'
	if(doc.serial_no_data){
		status = cur_frm.cscript.check_serial_exist(doc.serial_no_data, doc.serial_no)	
	}
	
	if (status=='Done') {
		if(doc.serial_no_data){
			doc.serial_no_data = doc.serial_no_data+'\n'+doc.serial_no
		}else{
			doc.serial_no_data = doc.serial_no
		}
	}else{
		alert("Serial no already exist")
	}
	
	cur_frm.cscript.calculate_qty(doc)
	refresh_field(['serial_no_data', 'work_qty'])
	get_server_fields('calculate_estimates_time','','',doc, cdt, cdn,1, function(){
		refresh_field(['estimated_time', 'end_date','completed_time'])	
	})
}

cur_frm.cscript.start_date = function(doc, cdt, cdn){
	get_server_fields('calculate_estimates_time','','',doc, cdt, cdn,1, function(){
		refresh_field(['estimated_time', 'end_date','completed_time'])	
	})
}

cur_frm.cscript.calculate_qty = function(doc){
	qty = 0
	if(doc.serial_no_data){
		sn_list = doc.serial_no_data.split('\n')
		$.each(sn_list, function(i){
			if(sn_list[i]){
				qty = qty + 1;
			}
		})
	}
	doc.work_qty = qty
	refresh_field('work_qty')
}


cur_frm.cscript.add_all_serial_no= function(doc, cdt, cdn){
	frappe.call({
		method:"erpnext.accounts.accounts_custom_methods.get_all_serial_no",
		args:{'filters': {'branch': doc.branch, 'process': doc.process, 'work_order': doc.process_work_order, 'trial_no':doc.process_trials, 'item_code': doc.item}},
		callback:function(r){
			if (r.message){
				doc.serial_no_data = ''
				$.each(r.message,function(key,value){
					doc.serial_no_data = doc.serial_no_data+value[0] +'\n'
					 
				})
				doc.work_qty = r.message.length
				refresh_field('serial_no_data')
				refresh_field('work_qty')
				get_server_fields('calculate_estimates_time','','',doc, cdt, cdn,1, function(){
					refresh_field(['estimated_time', 'end_date','completed_time'])	
				})
			}
		}

	})


}

cur_frm.cscript.clear_all= function(doc, cdt, cdn){

  var clear_list = ['serial_no_data','emp_status','process_tailor','employee_name','serial_no','start_date','end_date','estimated_time','completed_time','wages_for_single_piece','wages','latework','cost']
  $.each(clear_list,function(key,value){
  	doc[value] = ''
  	refresh_field(value)
  })

}