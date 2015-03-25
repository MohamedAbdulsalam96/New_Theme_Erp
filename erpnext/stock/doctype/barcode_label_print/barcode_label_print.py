# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import cint, cstr

class BarcodeLabelPrint(Document):
	
	def get_serial_nos(self,x=None):
		if x == 'search':
			self.offset = 0
		if x == 'onload':
			self.offset = 0
			frappe.db.sql(""" delete from `tabSerial No Details`  """)
			frappe.db.commit()


		sql_query =""" SELECT
		    sn.name,
		    sn.item_code,
		    sn.work_order,
		    ifnull(sn.barcode_image,'')as barcode,
		    ifnull(sn.qrcode,'') as qrcode,
		    sn.sales_invoice,
		    ifnull(wo.customer_name,'') as customer_name,
		    ifnull(wo.trial_no,'No') as trial_no,
		    CASE
		        WHEN wo.trial_date<= now()
		        THEN date_format(wo.trial_date,'%d-%b-%y')
		        ELSE
		              (
		              SELECT
		                  MAX(tailoring_delivery_date)
		              FROM
		                  `tabSales Invoice Items` sii
		              WHERE
		                  sii.parent = sn.sales_invoice
		              AND sii.tailoring_item_code =sn.item_code )
		    END as trial_date
		FROM
		    `tabSerial No` sn
		JOIN
		    `tabWork Order` wo
		ON
		    wo.name = sn.work_order
		JOIN
    		`tabSales Invoice` si        
		ON
    		si.name = sn.sales_invoice
		WHERE
		  sn.status = 'Available' and si.docstatus= 1 
		  {0}  order by sn.creation desc limit 20 {1}  """.format(self.get_conditions(),self.get_offset()) 
		

		result = frappe.db.sql(sql_query,as_dict=1)
		if result:
			self.render_serial_nos(result,x)
		
		self.offset = len(self.get('serial_no_details'))
		offset_no =self.offset
		return{
		'offset':offset_no
		}	



	def get_conditions(self):
		conditions = ''
		if self.from_serial_no and self.to_serial_no:
			conditions = conditions + " and sn.name BETWEEN '{0}' AND '{1}'".format(self.from_serial_no,self.to_serial_no)
		if self.sales_invoice:
			conditions = conditions + " and sn.sales_invoice = '%s' "%(self.sales_invoice)
		return conditions

	def get_offset(self):
		offset = ''
		if self.offset:
			frappe.errprint(self.offset)
			offset = "offset %s"%(self.offset)
			frappe.errprint(offset)
			return offset
		else:
			return ''


	def render_serial_nos(self,result,x):
		if x == 'search' or x == 'onload':
			self.set('serial_no_details',[])	
		for row in result:
			serial_no = self.append('serial_no_details',{})
			serial_no.serial_no = row.get('name')
			serial_no.item_code = row.get('item_code')
			serial_no.sales_invoice = row.get('sales_invoice')
			serial_no.work_order = row.get('work_order')
			serial_no.trial_no = row.get('trial_no')
			serial_no.trial_date = row.get('trial_date') or ''
			serial_no.barcode = row.get('barcode')
			serial_no.qr_code = row.get('qrcode')
			serial_no.customer_name = row.get('customer_name')


	
	def update_data(self):
		self.save()	

	

		 
			


