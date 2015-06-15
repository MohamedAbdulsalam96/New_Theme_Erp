
cur_frm.cscript.image = function(doc, cdt, cdn) {
	var d = locals[cdt][cdn]
	d.image_view = '<table style="width: 100%; table-layout: fixed;"><tr><td style="width:110px"><img src="'+d.image+'" width="100px"></td></tr></table>'
	refresh_field("measurement_item");
}

cur_frm.cscript.add_image = function(doc, cdt, cdn) {
	var d = locals[cdt][cdn]
	d.image_viewer = '<table style="width: 100%; table-layout: fixed;"><tr><td style="width:110px"><img src="'+d.add_image+'" width="100px"></td></tr></table>'
	refresh_field("wo_style");
}

cur_frm.cscript.item_code = function(doc, cdt, cdn){
	get_server_fields('get_details',doc.item_code,'',doc ,cdt, cdn,1, function(){
		refresh_field(['measurement_item','wo_process','raw_material'])
	})
}

cur_frm.cscript.validate = function(doc, cdt, cdn){
	refresh_field('work_order_name')
}

cur_frm.cscript.field_name=function(doc,cdt,cdn){
	var d=locals[cdt][cdn]
	if (d.field_name && doc.item_code){
		frappe.call({
		method:"erpnext.accounts.accounts_custom_methods.get_styles_DefaultValues",
		args:{style:d.field_name,item_code:doc.item_code},
		callback:function(r){
			d.default_value=r.message[1]
			d.image_viewer=r.message[0]
			refresh_field('image_viewer',d.name,'wo_style');
			refresh_field('default_value',d.name,'wo_style');

		}

	})

	}

}


cur_frm.cscript.value = function(doc, cdt, cdn){
	var d = locals[cdt][cdn]
	args = {'parameter':d.parameter, 'value':d.value, 'item':doc.item_code}
	get_server_fields('apply_rules',args,'',doc ,cdt, cdn,1, function(){
		refresh_field('measurement_item')
	})	
}

cur_frm.fields_dict.wo_style.grid.get_field("field_name").get_query = function(doc) {
      	return {
      		query : "tools.tools_management.custom_methods.get_style",
      		filters : {
      			'item_code':doc.item_code
      		}
      	}
}

cur_frm.fields_dict.process_wise_warehouse_detail.grid.get_field("warehouse").get_query = function(doc, cdt, cdn) {
		var d = locals[cdt][cdn]
      	return {
      		query : "tools.tools_management.custom_methods.get_branch_of_process",
      		filters : {
      			'item_code':doc.item_code,
      			'process' : d.process
      		}
      	}
}

cur_frm.cscript.view = function(doc, cdt, cdn){
	var e =locals[cdt][cdn]
	var image_data;
	var dialog = new frappe.ui.Dialog({
			title:__(e.field_name+' Styles'),
			fields: [
				{fieldtype:'HTML', fieldname:'styles_name', label:__('Styles'), reqd:false,
					description: __("")},
					{fieldtype:'Button', fieldname:'create_new', label:__('Ok') }
			]
		})
	var fd = dialog.fields_dict;

        // $(fd.styles_name.wrapper).append('<div id="style">Welcome</div>')
        return frappe.call({
			type: "GET",
			method: "tools.tools_management.custom_methods.get_styles_details",
			args: {
				"item": doc.item_code,
				"style": e.field_name
			},
			callback: function(r) {
				if(r.message) {
					
					var result_set = r.message;
					this.table = $("<table class='table table-bordered'>\
                       <thead><tr></tr></thead>\
                       <tbody></tbody>\
                       </table>").appendTo($(fd.styles_name.wrapper))

					columns =[['Style','10'],['Image','40'],['Value','40'],['Cost To Customer','50']]
					var me = this;
					$.each(columns, 
                       function(i, col) {                  
                       $("<th>").html(col[0]).css("width", col[1]+"%")
                               .appendTo(me.table.find("thead tr"));
                  }	);
					
					$.each(result_set, function(i, d) {
						var row = $("<tr>").appendTo(me.table.find("tbody"));
                       $("<td>").html('<input type="radio" name="sp" value="'+d[0]+'">')
                       		   .attr("style", d[0])
                               .attr("image", d[1])
                               .attr("value", d[2])
                               .attr("abbr", d[3])
                               .attr("customer_cost", d[4])
                               .attr("tailor_cost", d[5])
                               .attr("extra_cost", d[6])
                               .appendTo(row)
                               .click(function() {
                                      e.image_viewer = $(this).attr('image')
                                      e.default_value = $(this).attr('value')
                                      e.abbreviation = $(this).attr('abbr')
                                      e.cost_to_customer = $(this).attr('customer_cost')
                                      e.process_wise_tailor_cost = $(this).attr('tailor_cost')                           
                               });
                     
                       $("<td>").html($(d[1]).find('img')).appendTo(row);
                       $("<td>").html(d[2]).appendTo(row);
                       $("<td>").html(d[4]).appendTo(row);                     
               });
					
					dialog.show();
					$(fd.create_new.input).click(function() {						
						refresh_field('wo_style')	
						dialog.hide()
					})
				}
			}
		})		
}

cur_frm.fields_dict['trial_serial_no'].get_query = function(doc, cdt, cdn) {
		
      	return {
      		query : "tools.tools_management.custom_methods.get_serial_no",
      		filters : {
      			'serial_no':doc.serial_no_data
      		}
      	}
}

cur_frm.cscript.refresh = function(doc){
	refresh_field(['wo_style', 'measurement_item'])
	if(doc.docstatus==1){
		cur_frm.appframe.add_primary_action(__('Draw Canvas'), cur_frm.cscript['Draw Canvas'], "icon-edit")
	}
	 if(frappe.route_options) {
	 	  if (frappe.route_options.number == 1){
	 	  	window.location.reload();
	 	  }
            
    }
}

cur_frm.cscript['Draw Canvas'] = function(){
	
	frappe.call({
          "method": "frappe.core.page.imgcanvas.imgcanvas.get_img",
          args: {
            work_order: cur_frm.docname
          },
          callback:function(r){
          	if(r.message){
          		frappe.route_options = { work_order: cur_frm.docname};
				frappe.set_route("imgcanvas");

          	}
          	else if(!r.message){

             alert("No Attached file found for Item")

          	}
          }


      });
	
}

cur_frm.fields_dict['work_orders'].get_query = function(doc) {
	return {
		query: "erpnext.manufacturing.doctype.work_order.work_order.get_prev_wo",
    	filters: {
			"customer": doc.customer,
			"item_code": doc.item_code
		}
	}
}

cur_frm.cscript.work_orders = function(doc, cdt, cdn){
	if(doc.work_orders){
		return get_server_fields('fill_measurement_details', '', '', doc, cdt, cdn, 1, function(){
			refresh_field('measurement_item')
		});	
	}
}

cur_frm.cscript.fetch_measurement_details = function(doc, cdt, cdn){
	return get_server_fields('fill_cust_measurement_details', '', '', doc, cdt, cdn, 1, function(){
		refresh_field('measurement_item')
	});
}

cur_frm.cscript.style_work_order = function(doc, cdt, cdn){
	if(doc.style_work_order){
		return get_server_fields('fetch_previuos_Wo_Style', '', '', doc, cdt, cdn, 1, function(){
			refresh_field('wo_style')
		});	
	}
}

cur_frm.fields_dict['style_work_order'].get_query = function(doc) {
	return {
		query: "erpnext.manufacturing.doctype.work_order.work_order.get_prev_wo",
    	filters: {
			"customer": doc.customer,
			"item_code": doc.item_code
		}
	}
}

{% include 'stock/custom_items.js' %}
cur_frm.script_manager.make(erpnext.stock.CustomItem);


// cur_frm.cscript.define_cost_to_tailor = function(doc, cdt, cdn){
//         var d = locals[cdt][cdn]
//         init_cost_to_tailor(d)
//         render_cost_to_tailor_form(d)
//         add_cost_to_tailor(d)
//         save_tailor_cost(d)

//     }
// function init_cost_to_tailor(d){
//          this.dialog = new frappe.ui.Dialog({
//             title:__('Cost To Tailor'),
//             fields: [
//                 {fieldtype:'Link', fieldname:'process',options:'Process', label:__('Process'), reqd:false,
//                     description: __("")},
//                 {fieldtype:'Button', fieldname:'add_tailor_cost', label:__('Add'), reqd:false,
//                     description: __("")},
//                 {fieldtype:'HTML', fieldname:'tailor_cost_name', label:__('Styles'), reqd:false,
//                     description: __("")},
//                 {fieldtype:'Button', fieldname:'create_new', label:__('Ok') }
//             ]
//         })
//         $('.modal-content').css('width', '800px')
//         $('[data-fieldname = "create_new"]').css('margin-left','100px')
//         this.control_tailor_cost = this.dialog.fields_dict;
//         this.div = $('<div id="myGrid" style="width:100%;height:200px;margin:10px;overflow-y:scroll;"><table class="table table-bordered" style="background-color: #f9f9f9;height:10px" id="mytable">\
//                     <thead><tr ><td>Process</td><td>Tailor Cost</td><td>Remove</td></tr></thead><tbody></tbody></table></div>').appendTo($(this.control_tailor_cost.tailor_cost_name.wrapper))

//         this.dialog.show();


//   }
// function render_cost_to_tailor_form(d){
//         var me = this
//         if(d.process_wise_trial_cost_){
//             tailor_dict = JSON.parse(d.process_wise_trial_cost_)
//             console.log(tailor_dict)
//             $.each(tailor_dict,function(key,value){
//                 $(me.div).find('#mytable tbody').append('<tr id="my_row"><td>'+key+'</td>\
//                 <td><input class="text_box" data-fieldtype="Int" type="Textbox" value='+value+'>\
//                 </td><td>&nbsp;<button  class="remove">X</button></td></tr>')
//                  me.remove_row()
//             })
//         }   



//     }
// function add_cost_to_tailor(d){

//         var me = this;
//         this.table;
//         $(this.control_tailor_cost.add_tailor_cost.input).click(function(){
//             this.table = $(me.div).find('#mytable tbody').append('<tr id="my_row"><td>'+me.control_tailor_cost.process.input.value+'</td>\
//                 <td><input class="text_box" data-fieldtype="Int" type="Textbox">\
//                 </td><td>&nbsp;<button  class="remove">X</button></td></tr>')
//             me.remove_row()
//         })

//     }
// function save_tailor_cost(d){

//         var me = this;
       
//         $(this.control_tailor_cost.create_new.input).click(function(){
//              var tailor_cost_dict = {}
//              $('#mytable tr#my_row ').each(function(i,value){
//                 var $td = $(this).find('td')
//                   var process_name = ''
//                 $($td).each(function(inner_index){
                  
//                     if(inner_index == 0){
//                         process_name = $(this).text()
//                         tailor_cost_dict[$(this).text()]=''
//                     }
//                     if(inner_index == 1){
//                         tailor_cost_dict[process_name]=$(this).find('input').val()
//                     }
                   
//                 })

//              })
//         d.process_wise_trial_cost_ = JSON.stringify(tailor_cost_dict)
//         refresh_field('wo_style')
//         me.dialog.hide()

//         })
        
        
//     }


cur_frm.cscript.on_submit = function(doc, cdt, cdn) {
cur_frm.cscript.reload_doc()

}