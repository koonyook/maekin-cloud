import setting

from util import network,cacheFile,ping,general
from util import debugger
from info import dbController
from storage import nfsController
from scheduling import queue
from scheduling.dbLocker import Locker

import os
import traceback
import socket
import time
import threading
import subprocess,shlex
import libvirt
import MySQLdb

class workingThread(threading.Thread):
	def run(self):
		closeSocketEvent.wait()
		#now this process is free from socket
		
		infoHost=cacheFile.getDatabaseIP()
		db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
		cursor = db.cursor()

		cursor.execute("SELECT `value` FROM `cloud_variables` WHERE `key`='global_lock'")
		global_lock=cursor.fetchone()[0]
		db.close()

		if global_lock=='1':
			return			#this thread should not do anything
		
		locker=Locker('dequeuing')
		if locker.lock()==False:
			return			#this thread should not do anything
		
		"""
		#check database to make sure that dequeue process will not do at the same time
		# cloud_variable -> dequeuing ={0,1}
		
		cursor.execute("SELECT `value` FROM `cloud_variables` WHERE `key`='dequeuing'")
		dequeuing=cursor.fetchone()[0]
		
		if dequeuing=='1':
			db.close()
			return			#this thread should not do anything
		else:
			cursor.execute("UPDATE `cloud_variables` SET `value`='1' WHERE `key`='dequeuing'")
			db.close()	
		"""

		#######################################
		#### find the next work from queue ####
		#### and test that Can it do now ? ####
		#######################################
		try:
			queue.doNextWork(locker)
		except:
			traceback.print_exc()
			locker.unlock()
			"""
			infoHost=cacheFile.getDatabaseIP()
			db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
			cursor = db.cursor()
			cursor.execute("UPDATE `cloud_variables` SET `value`='0' WHERE `key`='dequeuing'")
			db.close()
			"""

def start_work(argv):
	'''
	try to start the next work if it can
	'''
	global closeSocketEvent
	closeSocketEvent=argv[0][2]

	aThread=workingThread()
	aThread.start()			#start new thread to do work

	return "OK"
