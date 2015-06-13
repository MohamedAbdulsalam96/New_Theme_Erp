cur_frm.cscript.branch_abbreviation = function (doc,dt,dn){
	special_char_list = ['@',"'",'"','$',"\\\\","\\",'#','%','*','&','^','.']

	$.each(special_char_list,function(key,value){
		if(doc.branch_abbreviation.indexOf(value) > -1){
			msgprint("Special Character {0} not allowed".replace('{0}',value))
			return false
		}
	})
}


cur_frm.cscript.stock_entry_bundle_abbreviation = function (doc,dt,dn){
	special_char_list = ['@',"'",'"','$',"\\\\","\\",'#','%','*','&','^','.']

	$.each(special_char_list,function(key,value){
		if(doc.stock_entry_bundle_abbreviation.indexOf(value) > -1){
			msgprint("Special Character {0} not allowed".replace('{0}',value))
			return false
		}
	})
}