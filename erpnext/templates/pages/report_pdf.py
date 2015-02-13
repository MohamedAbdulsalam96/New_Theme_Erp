from __future__ import unicode_literals
import frappe
from frappe.utils.pdf import get_pdf
import os
import sys
import random
from tools.custom_data_methods import get_site_name
from erpnext.support.page.report_scheduler import delete_report_folder


@frappe.whitelist(allow_guest=True)
def download_report_pdf(html):
	site_name = get_site_name()
	frappe.errprint(site_name)
	path = os.path.abspath(os.path.join('.',site_name, 'public', 'files'))
	report_path=path+'/Report_PDF'
	if not os.path.exists(report_path):
		os.makedirs(report_path,0755)
	if os.path.exists(report_path):
		filename=random.randrange(10,100000,2)
		filename=str(filename)
		html_path=report_path+'/'+filename+'.html'
		pdf_path=report_path+'/'+filename+'.pdf'
		data = open(html_path, 'w')
		frappe.errprint(type(html))
		data.write(html)
		data.close()
		os.system("wkhtmltopdf "+report_path+"/"+filename+".html "+report_path+"/"+filename+".pdf")
		return pdf_path