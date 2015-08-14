cur_frm.cscript.select_event = function(doc, cdt,cdn){
	var d = locals[cdt][cdn]
	d.template = get_mapper(d.select_event)
	refresh_field('notification_details')
}

function get_mapper(key){
	mapper = {
		"Welcome" : "Dear customer_name, thank you for the opportunity to serve you. You may contact us at branch_phone for any query. Thank you.",
		"Home Delivery" : "Dear customer_name, your garment(s) are dispatched for delivery. Kindly facilitate collection for the same. Thank you.",
		"Outstanding Amount" : "Dear customer_name, an amount of currency_symbol outstanding_amount is outstanding against your order no order_no. Kindly settle it as soon as possible. Thank you.",
		"Thank You" : "Dear customer_name, thank you for choosing us. We are delighted to serve you. See you soon again."
	}
	return mapper[key]
}