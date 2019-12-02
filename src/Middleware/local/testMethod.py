import setting

from util import network,cacheFile,ping,general
from util import debugger
from info import dbController
from storage import nfsController

import os
import socket
import time
import threading
import subprocess,shlex
import libvirt
import MySQLdb

import json
from threading import Timer
from util.general import getCurrentTime

########################################
### this zone is example and testing ###
########################################

def restart_libvirtd(argv):
	conn=argv[0][0]
	s=argv[0][1]

	general.runDaemonCommand("service libvirtd restart",conn,s)
	vconn=libvirt.open(None)
	time.sleep(1)
	vconn.close()

	return "OK"

def test_long_run(argv):
	'''
	this process take a long time to sleep
	can use to test capability of contain many connection
	'''
	print "sleep(10) was begin"
	time.sleep(10)
	print "end of sleep"
	return "OK"

class longThread(threading.Thread):
	def run(self):
		time.sleep(20)

def test_thread(argv):
	'''
	example of using thread
	'''
	longThread().start()	#start new thread

	return "OK"

class daemonThread(threading.Thread):
	def run(self):
		time.sleep(5)
		result = subprocess.Popen(shlex.split("service libvirtd restart"))
		result.wait()

def test_port(argv):
	'''
	for debug port usage when command "service ... restart"
	'''
	conn=argv[0][0]
	s=argv[0][1]

	pid=os.fork()
	if pid==0: #child
		###conn.shutdown(socket.SHUT_RDWR)
		conn.close()
		s.close()
		result = subprocess.Popen(shlex.split("service libvirtd restart"))
		result.wait()
		os._exit(0)
	else:
		os.waitpid(pid,0)	#block until child finish
	
	'''
	ddd=daemonThread()
	ddd.start()
	#ddd.join()
	'''
	'''
	result = subprocess.Popen(shlex.split("service libvirtd restart"))
	result.wait()
	'''
	#debugger.countdown(3,"test_port(libvirtd)")
	return "OK"

def test_long_message(argv):
	'''
	for get very long string argv and return very long string too
	'''
	print argv[0] #print long string
	print len(argv[0])

	return 'abc'*5000

def test_connection_bug(argv):
	return 'OK'

#############################################
######### this zone for do research #########
#############################################

def get_file(argv):
	try:
		targetFile=argv[0]
	
		aFile=open(targetFile,'r')
		content=aFile.read()
		aFile.close()
	except:
		content="File not found"

	return content

def logNetworkUsage():
	result=network.getInterfaceUsage('eth0')
	rx=result['rx']
	tx=result['tx']
	currentTime=getCurrentTime()
	logFile=open('/maekin/var/networkLog.txt','a')
	logFile.write('%.7f %s %s\n'%(currentTime,rx,tx))
	logFile.close()
	print 'log network data at',currentTime

class SetLogWork(threading.Thread):
	def __init__(self,howLong,closeConnEvent):
		threading.Thread.__init__(self)
		self.howLong=howLong
		self.closeConnEvent=closeConnEvent
	
	def run(self):
		self.closeConnEvent.wait()
		open('/maekin/var/networkLog.txt','w').close()
		Timer(0.0, logNetworkUsage,()).start()
		Timer(self.howLong, logNetworkUsage,()).start()
		time.sleep(self.howLong+5)
		print 'finish log_network'

def log_network(argv):
	'''
	argv[0]=howLong (sec)
	argv[1]={socket_connection}=[conn,s,closeConnEvent]
	'''
	howLong=int(argv[0])
	closeConnEvent=argv[1][2]

	SetLogWork(howLong,closeConnEvent).start()	#start new thread
	
	return "OK"
