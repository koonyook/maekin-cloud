from util import connection,general
from util import shortcut
from scheduling import queue

import cherrypy

class AddTaskA(object):
	'''
	add a simple task (opcode=999) to queue
	'''
	def index(self):
		taskID=queue.enqueue({
			'command':'task_a',
		})

		return shortcut.responseTaskID(taskID)

	index.exposed = True

class AddTaskB(object):
	'''
	add a simple task (opcode=999) to queue
	'''
	def index(self):
		taskID=queue.enqueue({
			'command':'task_b',
		})

		return shortcut.responseTaskID(taskID)

	index.exposed = True

class AddTask(object):
	'''
	add a simple task (opcode=999) to queue
	'''
	def index(self,waitTime='5'):
		taskID=queue.enqueue({
			'command':'simple_task',
			'waitTime':waitTime,
		})

		return shortcut.responseTaskID(taskID)

	index.exposed = True

class AddMission(object):
	'''
	add a simple mission (opcode=900) to queue
	'''
	def index(self,subTask='5'):
		taskID=queue.enqueue({
			'command':'simple_mission',
			'subTask':subTask,
		})

		return shortcut.responseTaskID(taskID)

	index.exposed = True

class GlobalDaemon(object):
	def index(self,message='this is default message'):		
		return "GLOBAL : this is your message?\n"+message
	index.exposed = True

class LocalDaemon(object):
	def index(self,message='this is default message'):
		result=connection.socketCall(host='127.0.0.1',mainPort=50000,command='hello',argv=[message,"abcdefg"])
		return result
	index.exposed = True

class LongRun(object):
	def index(self):
		result=connection.socketCall(host='127.0.0.1',mainPort=50000,command='test_long_run')
		return result
	index.exposed = True

class ShowXML(object):
	def index(self):
		#cherrypy.response.headers['Content-Type']= 'text/xml'
		#return '''<?xml version="1.0"?>
		content='''
<abc len="def">
	<tttt>hello</tttt>
</abc>
		'''
		return shortcut.response('success', content, "this is a message")

	index.exposed = True

class Relibvirt(object):
	def index(self):
		#result=connection.socketCall('127.0.0.1',50000,'restart_libvirtd',['{socket_connection}'])
		result=connection.socketCall('158.108.34.12',50000,'you_are_ca_server')
		result=connection.socketCall('158.108.34.12',50000,'update_pki',['{socket_connection}','158.108.34.12'])
		result=connection.socketCall('158.108.34.13',50000,'update_pki',['{socket_connection}','158.108.34.12'])
		return result
	index.exposed = True

class Test(object):
	a = AddTaskA()
	b = AddTaskB()
	addMission = AddMission()
	addTask = AddTask()
	globalDaemon = GlobalDaemon()
	localDaemon = LocalDaemon()
	longRun = LongRun()
	showXML = ShowXML()
	relibvirt = Relibvirt()
