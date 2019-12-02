from webapi.testAPI import Test
from webapi.alertAPI import Alert
from webapi.hostAPI import Host
from webapi.guestAPI import Guest
from webapi.cloudAPI import Cloud
from webapi.templateAPI import Template
from webapi.taskAPI import Task
from webapi.connectAPI import Connect

import cherrypy
import setting
from util import network

#######################
######## MAIN #########
#######################
def checkSource():
	if (cherrypy.request.headers["Remote-Addr"] in allowedIP) or ('*' in allowedIP):
		pass
	else:
		raise cherrypy.HTTPError(403, "Forbidden")

cherrypy.tools.filterIP=cherrypy.Tool('on_start_resource',checkSource)

@cherrypy.tools.filterIP()
class Interface(object):
	
	def __init__(self):
		global allowedIP
		allowedIP=[]
		try:
			aFile=open(setting.API_WHITELIST_FILE,'r')
			tmp=aFile.read().split('\n')
			aFile.close()
			for element in tmp:
				cur=element.strip()
				if cur=='*':
					allowedIP=['*']
					break
				else:
					try:
						currentIP=network.IPAddr(cur)
						allowedIP.append(str(currentIP))
					except:
						print "invalid ip:"+cur
		except:
			pass
		
		object.__init__(self)

	def index(self):
		return '<H1>Help for Maekin API usage</H1>\nbla bla bla...'
	index.exposed = True

	#testing branch
	test = Test()
	
	#real branch
	alert = Alert()
	host  = Host()
	guest = Guest()
	cloud = Cloud()
	template = Template()
	task = Task()
	connect = Connect()
