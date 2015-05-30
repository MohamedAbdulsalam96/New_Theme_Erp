import frappe
from frappe.templates.pages.style_settings import default_properties
from frappe.auth import _update_password

def execute():
	res=frappe.db.sql("""select name from tabUser where name='apiuser'""")
	if not res:
		install_docs = [
			{'doctype':'User', 'name':'apiuser', 'first_name':'apiuser',
				'email':'apiuser@example.com', 'enabled':1},
			{'doctype':'UserRole', 'parent': 'apiuser', 'role': 'Administrator',
				'parenttype':'User', 'parentfield':'user_roles'}
		]
		for d in install_docs:
			try:
				frappe.get_doc(d).insert()
			except frappe.NameError:
				pass
		#added by gangadhar for add all roles to guest
		frappe.get_doc("User", "apiuser").add_roles(*frappe.db.sql_list("""select name from tabRole"""))
		print "added all roles to apiuser"
		print frappe.db.sql_list("""select name from tabRole""")
		# gangadhar set password of guest
		_update_password("apiuser", "apiuser")
		print "updated password of apiuser"
		frappe.db.commit()