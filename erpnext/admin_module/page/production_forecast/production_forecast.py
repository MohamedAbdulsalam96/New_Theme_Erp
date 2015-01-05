from __future__ import unicode_literals
import frappe
import frappe.defaults

from frappe.utils import add_days, cint, cstr, date_diff, flt, getdate, nowdate, \
	get_first_day, get_last_day
from frappe import _, msgprint, throw

@frappe.whitelist()
def get_event_details(item_code):
	if item_code:
		frappe.db.sql("truncate table `temp_forecast_analysis`")
		frappe.db.sql("select production_forecast('%s')"%(item_code))
		data = frappe.db.sql("""select distinct parent_date as start,return_code as title,color as className from temp_forecast_analysis order by parent_date """, as_dict=1)
		return data
