from __future__ import unicode_literals
import frappe
import os
import subprocess
from tools.custom_data_methods import get_site_name


@frappe.whitelist(allow_guest=True)
def delete_report_folder():
	site_name = get_site_name()
	path = os.path.abspath(os.path.join('.',site_name, 'public', 'files','Report_PDF'))
	if os.path.exists(path):
		command='rm -rf {0}'.format(path)
		subprocess.check_call(command,shell=True)
