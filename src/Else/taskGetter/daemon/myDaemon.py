import sys, os, time
from datetime import datetime
import subprocess,shlex
import re
from mainDaemon import Daemon

from util import connection
from local import loadMethod,transferMethod,manageMethod

from util.general import getCommandDict
from util.general import getCurrentTime

import setting

class mktaskd(Daemon):
	'''
	Maekin local daemon
	'''
	def waitLocalPort(self):
		print "Waiting for port . .",
		while True:
			result = subprocess.Popen(shlex.split("netstat -p -a -t"), stdout=subprocess.PIPE)
			result.wait()
			output=result.communicate()[0]
			found = re.search(r":%s\s"%(str(setting.LOCAL_PORT)),output)
			if found==None:
				break
			time.sleep(1)
			print '.',
		
		print '.'

	def run(self):
		#config time
		result=subprocess.Popen(shlex.split("hwclock -s -u"))
		result.wait()
		#put vm start time log file
		logfile=open(setting.TIME_LOG_FILE,'a')
		logfile.write("open %.7f\n"%(getCurrentTime()))
		logfile.close()
		#open socket and wait for command
		connection.runServer(mainPort=setting.LOCAL_PORT,commandDict=getCommandDict(loadMethod,transferMethod,manageMethod))

