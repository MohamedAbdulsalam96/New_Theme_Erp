cur_frm.cscript.gift_voucher_item_name = function (doc,dt,dn){



    	frappe.call({
		method:"erpnext.selling.doctype.gift_voucher.gift_voucher.get_gift_voucher_item_name",
		args:{'item_code':doc.gift_voucher_item_name},
		callback:function(r){
			if(r.message){
				doc.item_name = r.message[0]
				doc.gift_voucher_amount = r.message[1]
				refresh_field('item_name')
				refresh_field('gift_voucher_amount')
			}
		}

		})



}


cur_frm.fields_dict.gift_voucher_item_name.get_query= function(doc){

	return{
		filters:{
			'item_group':'Gift Voucher'
		}
	} 
}