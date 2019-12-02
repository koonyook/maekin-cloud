import sys, time
import subprocess,shlex
import re
import cherrypy
from mainDaemon import Daemon

from util import connection,network
from local import testMethod,generalMethod,guestMethod,alertMethod,dbMethod,pkiMethod,globalMethod,nfsMethod,hostMethod,dhcpMethod,rawMethod,templateMethod,distroMethod
from scheduling import workerMethod

from util.general import getCommandDict

from webapi.interface import Interface

from local import currentInfo
from planning import planner

import setting
import libvirt

#this is an example
class MyDaemon(Daemon):
	def run(self):
		while True:
			time.sleep(1)


class mklocd(Daemon):
	'''
	Maekin local daemon
	'''
	def waitLocalPort(self):
		print "Waiting for port . .",
		while True:
			result = subprocess.Popen(shlex.split("netstat -p -a -t"), stdout=subprocess.PIPE)
			result.wait()
			output=result.communicate()[0]
			found = re.search(r"%s:%s\s"%(str(network.getMyIPAddr()),str(setting.LOCAL_PORT)),output)
			if found==None:
				break
			time.sleep(1)
			print '.',
		
		print '.'

	def run(self):
		#open socket and wait for command
		#connection.runServer(mainPort=50000,portPool=range(50001,65535),commandDict=getCommandDict(method))
		#import getpass
		#print getpass.getuser()
		network.renewIPAddr()
		connection.runServer(mainPort=setting.LOCAL_PORT,commandDict=getCommandDict(testMethod,generalMethod,guestMethod,alertMethod,dbMethod,pkiMethod,globalMethod,nfsMethod,hostMethod,dhcpMethod,workerMethod,rawMethod,templateMethod,distroMethod))

class mklocm(Daemon):
	'''
	Maekin local monitoring
		- write result to target file every 1 second
	'''
	def run(self):
		result = subprocess.Popen(shlex.split('''mkdir -p %s'''%(setting.CURRENT_INFO_PATH)), stdout=subprocess.PIPE)
		result.wait()
		
		currentInfo.runMonitor()	#infinite loop


#class mkglod(Daemon):
class mkapi(Daemon):
	'''
	Maekin global daemon : API
	'''
	def run(self):
		#branch to two thread
		cherrypy.config.update({'engine.autoreload_on':False})
		cherrypy.config.update({'server.thread_pool':10})
		cherrypy.config.update({'server.socket_host': '0.0.0.0','server.socket_port': 8080}) 
		cherrypy.quickstart(Interface())
"""
class mkworker(Daemon):
	'''
	Maekin global daemon : get task from queue to work
	'''
	def waitWorkerPort(self):
		print "Waiting for port . .",
		while True:
			result = subprocess.Popen(shlex.split("netstat -p -a -t"), stdout=subprocess.PIPE)
			result.wait()
			output=result.communicate()[0]
			found = re.search(r":%s\s"%(str(setting.WORKER_PORT)),output)
			if found==None:
				break
			time.sleep(1)
			print '.',
		
		print '.'

	def run(self):
		#open socket and wait for command
		connection.runServer(mainPort=setting.WORKER_PORT,commandDict=getCommandDict(workerMethod))
"""	
		
class mkplanner(Daemon):
	'''
	run like crontab and try to manage resource automaticaly
	'''
	def run(self):
		planner.runCollector()
