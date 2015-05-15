// Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

var display_activity_log = function(msg) {
	if(!pscript.ss_html)
		pscript.ss_html = $a(cur_frm.fields_dict['activity_log'].wrapper,'div');
	pscript.ss_html.innerHTML =
		'<div class="panel"><div class="panel-heading">'+__("Activity Log:")+'</div>'+msg+'</div>';
}

//Create salary slip
//-----------------------
cur_frm.cscript.create_salary_slip = function(doc, cdt, cdn) {

	var callback = function(r, rt){
		if (r.message)
			display_activity_log(r.message);
	}
	
	
	if (doc.type_of_salary == 'Monthly'){
		return $c('runserverobj', args={'method':'create_sal_slip','docs':doc},callback);
	}
	else if(doc.type_of_salary == 'Weekly' || doc.type_of_salary == 'LumpSum'){
		flag =  cur_frm.cscript.validate_for_weekly_lumpsum(doc,cdt,cdn)
		flag2 = cur_frm.cscript.date_validation(doc,cdt,cdn)
		
		if (flag == 0 && flag2== 0 && doc.type_of_salary == 'Weekly' ){
				return $c('runserverobj', args={'method':'create_weekly_sal_slip','docs':doc},callback);
		}else if(flag == 0  && doc.type_of_salary == 'LumpSum'){
				return $c('runserverobj', args={'method':'create_weekly_sal_slip','docs':doc},callback);
		}
		
	}
	else
	{
		msgprint("Please Select Type of Salary Option")
	}
}

cur_frm.cscript.submit_salary_slip = function(doc, cdt, cdn) {
	if (doc.type_of_salary == 'Monthly'){
		var check = confirm(__("Do you really want to Submit all {0} Salary Slip for month {1} and year {2}", [doc.type_of_salary,doc.month, doc.fiscal_year]));
	}else{
		var check = confirm(__("Do you really want to Submit all {0} Salary Slip for year {1} of week {2} to {3} ", [doc.type_of_salary,doc.fiscal_year,doc.from_date,doc.to_date]));	
	}
	
	if(check){
		var callback = function(r, rt){
			if (r.message)
				display_activity_log(r.message);
		}

	if (doc.type_of_salary == 'Monthly'){
		return $c('runserverobj', args={'method':'submit_salary_slip','docs':doc},callback);
	}
	else if(doc.type_of_salary == 'Weekly' || doc.type_of_salary == 'LumpSum'){
		flag =  cur_frm.cscript.validate_for_weekly_lumpsum(doc,cdt,cdn)
		flag2 = cur_frm.cscript.date_validation(doc,cdt,cdn)
		if (flag == 0 && flag2== 0 && doc.type_of_salary == 'Weekly'){
				return $c('runserverobj', args={'method':'submit_weekly_salary_slip','docs':doc},callback);
			}
		else if(flag == 0  && doc.type_of_salary == 'LumpSum'){
				return $c('runserverobj', args={'method':'submit_weekly_salary_slip','docs':doc},callback);
		}
	}
	else
		{
			msgprint("Please Select Type of Salary Option")
		}
		
	}
}

cur_frm.cscript.validate_for_weekly_lumpsum = function (doc,cdt,cdn){
	var flag = 0
	var my_obj = {'From Date':doc.from_date,'To Date':doc.to_date}
		$.each(my_obj,function(key,value){
			if (!value){
				msgprint("Please Select {0} Option".replace('{0}',key))
				flag = 1
				return false;
			}
		})
	return flag	
}


cur_frm.cscript.make_bank_voucher = function(doc,cdt,cdn){
    if(doc.company && doc.month && doc.fiscal_year){
    	cur_frm.cscript.make_jv(doc, cdt, cdn);
    } else {
  	  msgprint(__("Company, Month and Fiscal Year is mandatory"));
    }
}

cur_frm.cscript.make_jv = function(doc, dt, dn) {
	var call_back = function(r, rt){
		var jv = frappe.model.make_new_doc_and_get_name('Journal Voucher');
		jv = locals['Journal Voucher'][jv];
		jv.voucher_type = 'Bank Voucher';
		jv.user_remark = __('Payment of salary for the month {0} and year {1}', [doc.month, doc.fiscal_year]);
		jv.fiscal_year = doc.fiscal_year;
		jv.company = doc.company;
		jv.posting_date = dateutil.obj_to_str(new Date());

		// credit to bank
		var d1 = frappe.model.add_child(jv, 'Journal Voucher Detail', 'entries');
		d1.account = r.message['default_bank_account'];
		d1.credit = r.message['amount']

		// debit to salary account
		var d2 = frappe.model.add_child(jv, 'Journal Voucher Detail', 'entries');
		d2.debit = r.message['amount']

		loaddoc('Journal Voucher', jv.name);
	}
	if (doc.type_of_salary == 'Weekly'){
		flag = cur_frm.cscript.date_validation(doc,dt,dn)
		if (flag == 0){
			return $c_obj(doc, 'get_acc_details', '', call_back);
		 }

	}
	else{
		return $c_obj(doc, 'get_acc_details', '', call_back);
	}
	
}


cur_frm.cscript.from_date = function(doc,cdt,cdn){
	if(doc.type_of_salary == 'Weekly'){
	doc.to_date = frappe.datetime.add_days(doc.from_date,6)
	refresh_field('to_date')
	cur_frm.cscript.date_validation(doc,cdt,cdn)
	}

	
}

cur_frm.cscript.to_date = function(doc,cdt,cdn){
	// doc.from_date = frappe.datetime.add_days(doc.to_date,-6)
	// refresh_field('from_date')
	if(doc.type_of_salary == 'Weekly'){
	cur_frm.cscript.date_validation(doc,cdt,cdn)
    }
	
}



cur_frm.cscript.date_validation = function(doc,cdt,cdn){
	var flag = 0
	if (doc.from_date && doc.to_date){
		if(doc.type_of_salary == 'Weekly' && frappe.datetime.get_diff(doc.to_date, doc.from_date) != 6){
			flag = 1
			msgprint("Dates not in same week")
			
			
		}
		return flag
	}
	
}	