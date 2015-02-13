cur_frm.cscript.payment_type= function(doc, cdt, cdn){
	return $c('runserverobj',args={'method':'calc_emi', 'docs':doc}, function(r,rt) {
			refresh_field(['emi','total_loan_amount', 'pending_amount'])
		})
}



cur_frm.cscript.period =function(doc,cdt,cdn){

       if (doc.from_date){
       	period =parseInt(doc.period)
       	to_date=frappe.datetime.add_months(doc.from_date,period)

		doc.to_date=to_date
		cur_frm.set_df_property("to_date", "read_only",1);



       }
      

}