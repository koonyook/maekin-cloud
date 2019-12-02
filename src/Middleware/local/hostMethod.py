import setting

from util import network,cacheFile,ping,general
from util import connection
from util import debugger
from info import dbController
from storage import nfsController

import os
import time
import threading
import subprocess,shlex
import libvirt
import MySQLdb
import json
import shutil

class standbyThread(threading.Thread):
	def run(self):
		closeSocketEvent.wait()
		#now this process is free from socket
		f=open("/sys/power/state",'w')
		f.write('mem')
		f.close()

class hibernateThread(threading.Thread):
	def run(self):
		closeSocketEvent.wait()
		#now this process is free from socket
		f=open("/sys/power/state",'w')
		f.write('disk')
		f.close()
		
class shutdownThread(threading.Thread):
	def run(self):
		closeSocketEvent.wait()
		#now this process is free from socket
		result = subprocess.Popen(shlex.split("shutdown -h now"),stdout=subprocess.PIPE)
		result.wait()
		

def close_your_host(argv):
	'''
	must sure that socket is closed before suspend
	'''
	global closeSocketEvent
	closeSocketEvent=argv[0][2]
	mode=argv[1]
	
	if mode=='standby':
		aThread=standbyThread()
	elif mode=='hibernate':
		aThread=hibernateThread()
	elif mode=='shutdown':
		aThread=shutdownThread()
	else:
		return "this line cannot happen"

	nfsController.umount()
	aThread.start()			#start new thread to do work

	return 'OK'
	
def ask_your_spec(argv):
	'''
	answer my spec (for init host, so cannot use complex things in this method)
	'''
	myIP=network.getMyIPAddr()
	specData=connection.socketCall("localhost",setting.MONITOR_PORT,"get_my_spec",[])
	return specData


class restartMklocdThread(threading.Thread):
	def run(self):
		closeSocketEvent.wait()
		#now this process is free from socket
		general.runDaemonCommand("service mklocd restart")

def remove_cache_and_restart_mklocd(argv):
	'''
	used when remove host from cloud
	'''
	global closeSocketEvent
	closeSocketEvent=argv[0][2]
	
	#remove cache file
	cacheFile.clearValue()

	aThread=restartMklocdThread()
	aThread.start()			#start new thread to do work

	return 'OK'

def assign_hostname(argv):
	'''
	change my hostname immediately
	'''
	hostName=argv[0]

	aFile=open('/proc/sys/kernel/hostname','w')
	aFile.write(hostName)
	aFile.close()

	aFile=open('/etc/sysconfig/network','w')
	aFile.write("NETWORKING=yes\nHOSTNAME=%s\n"%(hostName))
	aFile.close()

	return 'OK'