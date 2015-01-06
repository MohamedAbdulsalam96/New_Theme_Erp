// Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

cur_frm.fields_dict.customer.get_query = function(doc,cdt,cdn) {
	return{	query: "erpnext.controllers.queries.customer_query" } }

frappe.provide("erpnext.support");

cur_frm.add_fetch("customer", "customer_name", "customer_name")

$.extend(cur_frm.cscript, {

	onload: function(doc, dt, dn) {
		/*if(in_list(user_roles,'System Manager')) {
			cur_frm.footer.help_area.innerHTML = '<p><a href="#Form/Support Email Settings/Support Email Settings">'+__("Support Email Settings")+'</a><br>\
				<span class="help">'+__("Integrate incoming support emails to Support Ticket")+'</span></p>';
		}*/
		//console.log("local and admin");
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
					console.log(r.message)
					refresh_field('raised_by');
				}
				})
			//doc.raised_by=usr;
			//console.log(doc.raised_by)		
		}
		else if (doc.__islocal && user!='Administrator'){
			//console.log("local and not admin");	
			doc.raised_by=user;
		}
	},

	refresh: function(doc) {
		erpnext.toggle_naming_series();
		cur_frm.cscript.make_listing(doc);
		if(!doc.__islocal) {
			if(cur_frm.fields_dict.status.get_status()=="Write") {
				if(doc.status!='Closed') cur_frm.add_custom_button(__('Close'),
					cur_frm.cscript['Close Ticket'], "icon-ok", "btn-success");
				if(doc.status=='Closed') cur_frm.add_custom_button(__('Re-Open Ticket'),
					cur_frm.cscript['Re-Open Ticket'], null, "btn-default");
			}

			cur_frm.toggle_enable(["subject", "raised_by"], false);
			cur_frm.toggle_display("description", false);
		}
		refresh_field('status');
		if (in_list(user_roles, 'Super Admin')) {
			//alert("super admin logged in");	
			cur_frm.toggle_display("customer_name", false);
			cur_frm.toggle_display("contact", false);
			//cur_frm.toggle_display("purchase_details", false);
		}
		else{
			cur_frm.toggle_display("assign_in_future", false);
		}
	},


	make_listing: function(doc) {
		var wrapper = cur_frm.fields_dict['thread_html'].wrapper;

		var comm_list = frappe.get_list("Communication", {"parent": doc.name, "parenttype":"Support Ticket"})

		if(!comm_list.length) {
			comm_list.push({
				"sender": doc.raised_by,
				"creation": doc.creation,
				"subject": doc.subject,
				"content": doc.description});
		}

		cur_frm.communication_view = new frappe.views.CommunicationList({
			list: comm_list,
			parent: wrapper,
			doc: doc,
			recipients: doc.raised_by
		})

	},

	'Close Ticket': function() {
		cur_frm.cscript.set_status("Closed");
	},

	'Re-Open Ticket': function() {
		cur_frm.cscript.set_status("Open");
	},

	set_status: function(status) {
		return frappe.call({
			method: "erpnext.support.doctype.support_ticket.support_ticket.set_status",
			args: {
				name: cur_frm.doc.name,
				status: status
			},
			callback: function(r) {
				if(!r.exc) cur_frm.reload_doc();
			}
		})

	}

})
