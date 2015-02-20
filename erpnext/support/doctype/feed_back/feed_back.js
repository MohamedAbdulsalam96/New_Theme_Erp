cur_frm.cscript.send = function(doc, cdt, cdn) {
		frappe.call({
			method:"erpnext.selling.doctype.email_template.email_template.send_email",
			args: {
				notification_type:doc.raised_by,
				message:doc.reply_to_feedback				
				},
		});

}

$.extend(cur_frm.cscript, {
	onload: function(doc, dt, dn) {
                var usr=''
                if(doc.__islocal && user=='Administrator') {
                                frappe.call({
                                method: "erpnext.support.doctype.support_ticket.support_ticket.get_admin",
                                args: {
                                        name: cur_frm.doc.name
                                },
                                callback: function(r) {
                                        usr=r.message;
                                        doc.raised_by=r.message;
                                        refresh_field('raised_by');
                                }
                                })
                        cur_frm.toggle_display("send", false);
			cur_frm.toggle_display("reply_to_feedback", false);    
        		cur_frm.toggle_display("assign_to", false);

                }
                else if (doc.__islocal && user!='Administrator'){
                        doc.raised_by=user;
                }
  		
	}
})
