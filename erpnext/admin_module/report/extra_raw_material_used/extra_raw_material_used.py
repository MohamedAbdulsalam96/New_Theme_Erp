# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns, data = [], []
	sales_invoice = product = from_date = to_date = branch= ''
	cond = "1=1"
	if filters:
		sales_invoice, product, from_date =  filters.get('sales_invoice') or '', filters.get('product') or '', filters.get('from_date') or ''
		to_date, branch = filters.get('to_date') or '', filters.get('branch') or ''
	data = frappe.db.sql(""" select * from 
								(
								SELECT
									sii.parent as sales_invoice,
									imp.item_name AS product,
									si.posting_date as booking_date,
									coalesce(rmi.qty,0) as bom_qty,
									coalesce(ir.qty,0)  AS issued_qty,
									ir.modified_by as issued_by,
									si.branch,
									si.creation							    
								FROM
								`tabSales Invoice` si
								    left join `tabSales Invoice Item` sii  on sii.parent=si.name
								    left join  `tabProcess Allotment` pa on pa.sales_invoice_no=sii.parent AND pa.item=sii.item_code
								    left join `tabIssue Raw Material` ir on ir.parent=pa.name
								    inner join tabItem imp on  sii.item_code=imp.name
								    inner join tabItem imr on ir.raw_material_item_code=imr.name
								    left join `tabRaw Material Item` rmi on rmi.parent=imp.name and rmi.raw_item_code=imr.name
								    where ir.raw_material_item_code is not null and si.docstatus=1						    
								 )foo  where
								sales_invoice=coalesce(nullif('%s', ''),foo.sales_invoice)
								 and foo.product=coalesce(nullif('%s', ''),foo.product)
								 and date(creation) between coalesce(nullif('%s', ''),'1970-11-13 15:46:52') and coalesce(nullif('%s', ''),'2050-11-13 15:46:52') 
								and coalesce(foo.branch) = coalesce(nullif('%s', ''),foo.branch)"""%(sales_invoice, product, from_date, to_date, branch), as_list=1)

	columns = ["Sales Invoice:Link/Sales Invoice:150", "Item Name::110", "Order Date:Date:100","Bom Qty:Int:70","Issued Qty:Int:70","Issued Buy::100", "Branch::60"]
	return columns, data