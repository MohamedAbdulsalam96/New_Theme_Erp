from __future__ import unicode_literals
import frappe
from frappe.utils.file_manager import save_file
import os, base64, re
import random
import json

@frappe.whitelist()
def add_node():
	ctype = frappe.form_dict.get('ctype')
	parent_field = 'parent_' + ctype.lower().replace(' ', '_')
	name_field = ctype.lower().replace(' ', '_') + '_name'
	fname, content = get_uploadedImage_content(frappe.form_dict['filedata'], frappe.form_dict['filename'])
	if content:
		image = save_file(fname, content, 'Product Catalog', frappe.form_dict['name_field'])

	doc = frappe.new_doc(ctype)
	doc.update({
		name_field: frappe.form_dict['name_field'],
		parent_field: frappe.form_dict['parent'],
		"is_group": frappe.form_dict['is_group']
	})

	doc.save()	
	return "Done"

@frappe.whitelist()
def get_uploadedImage_content(filedata, filename):
	filedata = filedata.rsplit(",", 1)[1]
	uploaded_content = base64.b64decode(filedata)
	return filename, uploaded_content

@frappe.whitelist()
def view_image():
	name = frappe.form_dict.get('name')
	return frappe.db.sql(""" SELECT file_url FROM `tabFile Data` WHERE
		attached_to_name='%s' AND attached_to_doctype='Product Catalog'"""%(name))

@frappe.whitelist()
def webcam_img_upload(imgdata1,customer):
	data =json.loads(imgdata1)
	filename=random.randrange(1,100000,2)
	filename=str(filename)+'.png'

	fname, content = get_uploadedImage_content(imgdata1,filename)
	if content:
		image = save_file(fname, content,'Customer',customer)
	return fname	

