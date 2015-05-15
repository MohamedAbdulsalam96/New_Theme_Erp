cur_frm.cscript.onload = function(doc, cdt, cdn){
	var x='onload'
	doc.sales_invoice = ''
	doc.from_serial_no = ''
	doc.to_serial_no = ''
	get_server_fields('get_serial_nos',x,'',doc,cdt,cdn,1,function(){
		refresh_field('offset')
		refresh_field('serial_no_details')
		
	})
}



cur_frm.cscript.search = function(doc,cdt,cdn){
	var obj = {'From Serial No':doc.from_serial_no,'To serial No':doc.to_serial_no}
	
	$.each(obj,function(key,value){
		if(!value){
			alert("Please Enter in  '%s' Field".replace(/%s/g,key))
			return false
		}

	})
	var x='search'
	get_server_fields('get_serial_nos',x,'',doc,cdt,cdn,1,function(){
		refresh_field('offset')
		refresh_field('serial_no_details')
		
	})

}


cur_frm.cscript.more = function(doc,cdt,cdn){
	var x = 'more'
	get_server_fields('get_serial_nos',x,'',doc,cdt,cdn,1,function(){
		refresh_field('offset')
		refresh_field('serial_no_details')

	})

}

cur_frm.fields_dict.from_serial_no.get_query = function(doc) {
	if (doc.sales_invoice){

	return{
	  filters:{
			   'sales_invoice': doc.sales_invoice
		      }
	      }

	}
	
}
cur_frm.fields_dict.to_serial_no.get_query = function(doc) {
	if (doc.sales_invoice){

	return{
		filters:{
			'sales_invoice': doc.sales_invoice
	    	}
     	}

   }
}


cur_frm.cscript.select = function(doc, cdt, cdn){
	return get_server_fields('update_data', '','', doc, cdt, cdn, 1, function(){
		refresh_field('serial_no_details')
	})
}