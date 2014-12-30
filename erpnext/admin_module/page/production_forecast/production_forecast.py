from __future__ import unicode_literals
import frappe
import frappe.defaults

from frappe.utils import add_days, cint, cstr, date_diff, flt, getdate, nowdate, \
	get_first_day, get_last_day
from frappe import _, msgprint, throw

@frappe.whitelist()
def get_event_details(item_code):
	if item_code:
		frappe.db.sql("truncate table `temp_production_forecast`")
		frappe.db.sql("select forecast_fun('%s')"%(item_code))
		data = frappe.db.sql("""select date as start,case when type='buffer'
		 then 'Buffer Period' else concat('Deliverable:',delivery_qty,' \\n ','Capacity:',capacity)
		  end as title,color as className
		  from temp_production_forecast order by date asc """, as_dict=1)
		return data
