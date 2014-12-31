cur_frm.cscript.send = function(doc, cdt, cdn) {
//console.log("in tjhe sen js");
		frappe.call({
			method:"erpnext.selling.doctype.email_template.email_template.send_email",
			args: {
				notification_type:doc.raised_by,
				message:doc.reply_to_feedback				
				},
			// callback: function(r) {
				// console.log(r.message);
			// }
		});

}

$.extend(cur_frm.cscript, {
	onload: function(doc, dt, dn) {
                var usr=''
                if(doc.__islocal && user=='Administrator') {
                                //console.log("local and admin");
                                frappe.call({
                                method: "erpnext.support.doctype.support_ticket.support_ticket.get_admin",
                                args: {
                                        name: cur_frm.doc.name
                                },
                                callback: function(r) {
                                        //alert(r.message);
                                        usr=r.message;
                                        doc.raised_by=r.message;
                                        //console.log(doc.raised_by)
                                        //console.log(r.message)
                                        refresh_field('raised_by');
                                }
                                })
                        cur_frm.toggle_display("send", false);
			cur_frm.toggle_display("reply_to_feedback", false);    
        		cur_frm.toggle_display("assign_to", false);

                }
                else if (doc.__islocal && user!='Administrator'){
                       // console.log("local and not admin");
                        doc.raised_by=user;
                }
  		
	}
})
