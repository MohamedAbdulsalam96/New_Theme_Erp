# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import throw, msgprint, _
from frappe.model.document import Document

class SiteMaster(Document):
	pass



def multitenanct(from_test=False):
   res=frappe.db.sql("""select name from `tabSite Master` where flag=0 limit 1 """)
   if res:
	sites=''
	sites = frappe.db.sql("""select sites from  `tabUser` where name='administrator'""")
	#print sites
	auto_commit = not from_test
	ste=res[0][0]
	from frappe.utils import cstr  
	import os
	import sys
	import subprocess
	import getpass
	import logging
	import json
	from distutils.spawn import find_executable
	cwd= '/home/gangadhar/workspace/smarttailor/frappe-bench/'
        cmd='bench new-site '+ste
	 
	sites=cstr(sites[0][0])+' '+ste
	#print sites
	frappe.db.sql("update `tabUser` set sites= %s where name='administrator'",sites)
        try:
		subprocess.check_call(cmd, cwd=cwd, shell=True)
	except subprocess.CalledProcessError, e:
		print "Error:", e.output
		raise
        cmd='bench frappe --install_app erpnext '+ste              
        try:
		subprocess.check_call(cmd, cwd=cwd, shell=True)
	except subprocess.CalledProcessError, e:
		print "Error:", e.output
		raise
        cmd='bench frappe --install_app shopping_cart '+ste             
        try:
		subprocess.check_call(cmd, cwd=cwd, shell=True)
	except subprocess.CalledProcessError, e:
		print "Error:", e.output
		raise
        nginx="""
		upstream frappe {
    		server 127.0.0.1:8000 fail_timeout=0;
		}
		server {
			listen 80 ;
			client_max_body_size 4G;
			server_name %s;
			keepalive_timeout 5;
			sendfile on;
			root /home/gangadhar/workspace/smarttailor/frappe-bench/sites;
			location /private/ {
				internal;
				try_files /$uri =424;
			}
			location /assets {
				try_files $uri =404;
			}

			location / {
				try_files /test/public/$uri @magic;
			}

			location @magic {
				proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
				proxy_set_header Host $host;
				proxy_set_header X-Use-X-Accel-Redirect True;
				proxy_read_timeout 120;
				proxy_redirect off;
				proxy_pass  http://frappe;
			}
		}"""%(sites)
	with open("/home/gangadhar/workspace/smarttailor/frappe-bench/config/nginx.conf","w") as conf_file:
			conf_file.write(nginx)
        cwd='/home/'
        cmd='echo indictrans | sudo service nginx reload'
        try:
		subprocess.check_call(cmd, cwd=cwd, shell=True)
	except subprocess.CalledProcessError, e:
		print "Error:", e.output
		raise
	host="""
		127.0.0.1       localhost
		127.0.1.1       gangadhar-OptiPlex-360
		127.0.0.1       %s


		# The following lines are desirable for IPv6 capable hosts
		::1     ip6-localhost ip6-loopback
		fe00::0 ip6-localnet
		ff00::0 ip6-mcastprefix
		ff02::1 ip6-allnodes
		ff02::2 ip6-allrouters
       """%(sites)
	with open("/home/gangadhar/workspace/smarttailor/frappe-bench/config/hosts","w") as hosts_file:
			hosts_file.write(host)
        os.system('echo indictrans | sudo -S cp /home/gangadhar/workspace/smarttailor/frappe-bench/config/hosts /etc/hosts')
    	from frappe.utils import nowdate,add_months,cint
    	en_dt=add_months(nowdate(),1)
	qry="update `tabSite Master` set flag=1 ,expiry_date='"+en_dt+"' where name='"+cstr(res[0][0])+"'"
	frappe.db.sql(qry, auto_commit=auto_commit)
	qry1="select email_id__if_administrator from `tabSite Master` where name='"+cstr(ste)+"'"
	rr=frappe.db.sql(qry1)
	eml=rr and rr[0][0] or ''
	frappe.get_doc({
			"doctype":"SubAdmin Info",
			"parent": "SUB0001",
			"parentfield": "subadmins_information",
			"parenttype":"Admin Details",
			"admin": eml,
			"site_name":ste
		}).insert()




def validate_validity(doc, method):
	from frappe.utils import get_url, cstr
	if doc.get("__islocal") and get_url()!='http://demo.tailorpad.com':
		#res =''
	 	res = frappe.db.sql("select name,user_name,validity from `tabUser Validity` where  user_name > 0",as_list=1)
	 	frappe.errprint(res)
	 	if  res:
	 		res1 = frappe.db.sql("select count(name) from `tabUser`")
	 		if res1 and res1[0][0]==2:
	 			frappe.db.sql("update `tabUser Validity` set user_name=user_name-2  where name='%s'" %(res[0][0]))
			else:
	 			frappe.db.sql("update `tabUser Validity` set user_name=user_name-1  where name='%s'" %(res[0][0]))
	 		from frappe.utils import nowdate,add_months,cint, getdate 
	 		doc.validity_start_date=nowdate()
	 		doc.validity_end_date=add_months(getdate(nowdate()), cint(res[0][2]))
		else:
			# 	#pass
			# 	#Comment by rohit
	 		frappe.throw(_("Your User Creation limit is exceeded . Please contact administrator"))

	# elif(get_url()!='http://admin.tailorpad.com'):
	# 	frappe.errprint("updating existing user not admin.tailorpad.com")
		

def update_users(doc, method):
	#doc.add_validity=''
	from frappe.utils import get_url, cstr
	if get_url()=='http://admin.tailorpad.com':
		if not doc.enabled :
			abc=frappe.db.sql("""select name from `tabUser` where name=%s and enabled=0""", doc.name)
			if abc:
				frappe.db.sql("""update `tabSupport Ticket` set assign_to='Administrator' where assign_to=%s""",doc.name)

def create_support():
	import requests
	import json
	pr2 = frappe.db.sql("""select site_name from `tabSubAdmin Info` """)
	for site_name in pr2:
		db_name=cstr(site_name[0]).split('.')[0]
		db_name=db_name[:16]
		abx="select name from `"+cstr(db_name)+"`.`tabSupport Ticket` where flag='false'"
		pr3 = frappe.db.sql(abx)
		for sn in pr3:
		 		login_details = {'usr': 'Administrator', 'pwd': 'admin'}
		 		url = 'http://smarttailor/api/method/login'
		 		headers = {'content-type': 'application/x-www-form-urlencoded'}
		 		response = requests.post(url, data='data='+json.dumps(login_details), headers=headers)
		 		test = {}
		 		url="http://"+cstr(site_name[0])+"/api/resource/Support Ticket/"+cstr(sn[0])
		 		response = requests.get(url)
				support_ticket = eval(response.text).get('data')
				del support_ticket['name']
				del support_ticket['creation']
				del support_ticket['modified']
				del support_ticket['company']
				url = 'http://smarttailor/api/resource/Support Ticket'
				headers = {'content-type': 'application/x-www-form-urlencoded'}
				response = requests.post(url, data='data='+json.dumps(support_ticket), headers=headers)
				url="http://"+cstr(site_name[0])+"/api/resource/Support Ticket/"+cstr(sn[0])
				support_ticket={}
				support_ticket['flag']='True'
				response = requests.put(url, data='data='+json.dumps(support_ticket), headers=headers)

def create_feedback():
	import requests
	import json
	pr2 = frappe.db.sql("""select site_name from `tabSubAdmin Info`""")
	for site_name in pr2:
		db_name=cstr(site_name[0]).split('.')[0]
		db_name=db_name[:16]
		abx="select name from `"+cstr(db_name)+"`.`tabFeed Back` where flag='false'"
		pr3 = frappe.db.sql(abx)
		for sn in pr3:
		 		login_details = {'usr': 'Administrator', 'pwd': 'admin'}
		 		url = 'http://smarttailor/api/method/login'
		 		headers = {'content-type': 'application/x-www-form-urlencoded'}
		 		response = requests.post(url, data='data='+json.dumps(login_details), headers=headers)
		 		test = {}
		 		url="http://"+cstr(site_name[0])+"/api/resource/Feed Back/"+cstr(sn[0])
		 		response = requests.get(url)
				support_ticket = eval(response.text).get('data')
				del support_ticket['name']
				del support_ticket['creation']
				del support_ticket['modified']
				url = 'http://smarttailor/api/resource/Feed Back'
				headers = {'content-type': 'application/x-www-form-urlencoded'}
				response = requests.post(url, data='data='+json.dumps(support_ticket), headers=headers)
				url="http://"+cstr(site_name[0])+"/api/resource/Feed Back/"+cstr(sn[0])
				support_ticket={}
				support_ticket['flag']='True'
				response = requests.put(url, data='data='+json.dumps(support_ticket), headers=headers)

def add_validity():
		import requests
		import json
		from frappe.utils import nowdate, cstr,cint, flt, now, getdate, add_months
		pr1 = frappe.db.sql("""select site_name from `tabSite Master` """)
		for pr in pr1:
			if pr[0].find('.')!= -1:
				db=pr[0].split('.')[0][:16]
			else:
				db=pr[0][:16]
			qry="select validity from `"+cstr(db)+"`.`tabUser` where name='administrator' and validity>0 "
			pp1 = frappe.db.sql(qry)
			if pp1 :
				headers = {'content-type': 'application/x-www-form-urlencoded'}
				sup={'usr':'administrator','pwd':'admin'}
				url = 'http://'+pr[0]+'/api/method/login'
				response = requests.get(url, data=sup, headers=headers)
				qry1="select name from `"+cstr(db)+"`.`tabUser` where validity_end_date <CURDATE()"
				pp2 = frappe.db.sql(qry1)
				for pp in pp2:
					dt=add_months(getdate(nowdate()), cint(pp1[0][0]))
					vldt={}				
					vldt['validity_start_date']=cstr(nowdate())
					vldt['validity_end_date']=cstr(dt)
					url = 'http://'+pr[0]+'/api/resource/User/'+cstr(name)
					response = requests.put(url, data='data='+json.dumps(vldt), headers=headers)
				qry2="select name,validity_end_date from `"+cstr(db)+"`.`tabUser` where validity_end_date >=CURDATE()"
				pp3 = frappe.db.sql(qry2)
				for name,validity_end_date in pp3:
					dt=add_months(getdate(validity_end_date), cint(pp1[0][0]))
					vldt={}				
					vldt['validity_end_date']=cstr(dt)
					url = 'http://'+pr[0]+'/api/resource/User/'+cstr(name)
					response = requests.put(url, data='data='+json.dumps(vldt), headers=headers)
				vldt={}
				vldt['validity']='0'
				url = 'http://'+pr[0]+'/api/resource/User/administrator'
				response = requests.put(url, data='data='+json.dumps(vldt), headers=headers)		

def disable_user():
	import requests
	import json
	pr2 = frappe.db.sql("""select site_name from `tabSubAdmin Info`""")
	for site_name in pr2:
		db_name=cstr(site_name[0]).split('.')[0]
		db_name=db_name[:16]
		abx="select name from `"+cstr(db_name)+"`.`tabUser` where validity_end_date<=CURDATE()"
		pr3 = frappe.db.sql(abx)
		for sn in pr3:
				headers = {'content-type': 'application/x-www-form-urlencoded'}
				sup={'usr':'administrator','pwd':'admin'}
				url = 'http://'+cstr(site_name[0])+'/api/method/login'
				response = requests.get(url, data=sup, headers=headers)
		 		url="http://"+cstr(site_name[0])+"/api/resource/User/"+cstr(sn[0])
		 		support_ticket={}
				support_ticket['enabled']=0
				response = requests.put(url, data='data='+json.dumps(support_ticket), headers=headers)


def assign_support():
	from frappe.utils import get_url, cstr
	if get_url()=='http://smarttailor':
		check_entry = frappe.db.sql("""select name,raised_by from `tabSupport Ticket` where assign_to is null and raised_by is not null and status<>'Closed'""")
		for name,raised_by in check_entry :
			assign_to = frappe.db.sql("""select assign_to from `tabAssing Master` where name= %s""",raised_by)
			if assign_to :
				aa="update `tabSupport Ticket` set assign_to='"+cstr(assign_to[0][0])+"' where name = '"+name+"'"
				frappe.db.sql(aa)	
			else :
				aa="update `tabSupport Ticket` set assign_to='Administrator' where name = '"+name+"'"
				frappe.db.sql(aa)

def superadmin():
	from frappe.utils import get_url, cstr
	if get_url()=='http://smarttailor':
		#self.superadmin()
		import requests
		import json
		pr1 = frappe.db.sql("""select site_name,email_id__if_administrator,country from `tabSite Master` where client_name=%s""",self.customer)
		st=pr1 and pr1[0][0] or ''
		eml=pr1 and pr1[0][1] or ''
		cnt=pr1 and pr1[0][2] or ''
		val=usr=0
		headers = {'content-type': 'application/x-www-form-urlencoded'}
		sup={'usr':'administrator','pwd':'admin'}
		url = 'http://'+st+'/api/method/login'
		response = requests.get(url, data=sup, headers=headers)
		if st.find('.')!= -1:
			db=st.split('.')[0][:16]
		else:
			db=st[:16]
		item_code = frappe.db.sql("""select item_code from `tabSales Order Item` where parent = %s """, self.name)
		for ic in item_code:
			qr="select no_of_users,validity from `tabItem` where name = '"+cstr(ic[0])+"'"
			pro = frappe.db.sql(qr)
			if (pro [0][0]== 0) and (pro[0][1]>0):
				vldt={}
				vldt['validity']=pro[0][1]
				vldt['country']=cnt
				vldt['email_id_admin']=eml
				url = 'http://'+st+'/api/resource/User/Administrator'
				response = requests.put(url, data='data='+json.dumps(vldt), headers=headers)
			elif (pro [0][0]>0 ) and (pro[0][1]==0):
				vldtt={}
				vldtt['no_of_users']=pro[0][0]
				vldtt['country']=cnt
				vldtt['email_id_admin']=eml
				url = 'http://'+st+'/api/resource/User/Administrator'
				response = requests.put(url, data='data='+json.dumps(vldtt), headers=headers)
			elif (pro [0][0]> 0) and (pro[0][1]>0):
				user_val={}
				user_val['validity']=pro [0][1]
				user_val['user_name']=pro [0][0]
				user_val['flag']='false'
				url = 'http://'+st+'/api/resource/User Validity'
				response = requests.post(url, data='data='+json.dumps(user_val), headers=headers)
