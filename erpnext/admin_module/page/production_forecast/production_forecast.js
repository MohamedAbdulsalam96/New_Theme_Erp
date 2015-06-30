
frappe.pages['production-forecast'].onload = function(wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Production Forecast',
		single_column: true
	});
	new frappe.MakeCalendar(wrapper)
}

frappe.MakeCalendar = Class.extend({
	init: function(wrapper){
		frappe.require('assets/frappe/js/lib/fullcalendar/fullcalendar.css');
		frappe.require('assets/frappe/js/lib/fullcalendar/fullcalendar.js');
		this.wrapper = wrapper;
		this.make_calendar();
	},

	make_calendar: function(){
		var me = this
		$(this.wrapper).find('.layout-main').empty()
		$(this.wrapper).find('.layout-main').html('<div id="calendar"></div>')
		this.item_code = this.wrapper.appframe.add_field({fieldtype:"Link", label:"Item Code",
			fieldname:"item_code", options:'Item'});
		this.search = this.wrapper.appframe.add_field({fieldtype:"Button", label:"Search",
			fieldname:"search", input_css: {"z-index": 3}});
		$(this.search.wrapper).click(function(){ 
			if(me.item_code.$input.val()){
				me.render_data();	
			}else{
				alert("Select Item Code")
			}
			 
		})
	},

	render_data: function(){
		var me = this;
		frappe.call({
			method: 'erpnext.admin_module.page.production_forecast.production_forecast.get_event_details',
			args:{
				item_code: me.item_code.$input.val()
			},
			callback:function(r){
				if(r.message){
					me.create_calendar(r.message)
				}
			}
		})
	},

	create_calendar: function(args){
		var me = this;
		$(me.wrapper).find('#calendar').fullCalendar({
			header: {
				left: 'prev,next today',
				center: 'title',
				right: 'month,agendaWeek,agendaDay'
			},
			editable: true,
			events: args
		});
	}
})