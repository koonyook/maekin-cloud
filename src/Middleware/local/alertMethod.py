import setting

from util import network,cacheFile,ping,general,connection
from util import ha
from scheduling import queue
from info import dbController
from storage import nfsController
from service import dbService,caService

import os
import time
import threading
import subprocess,shlex
import libvirt
import MySQLdb

#################################################
### this zone is called by monitoring service ###
#################################################

class Repair( threading.Thread ):
	def run ( self ):
		closeSocketEvent.wait()
		network.configToStaticFromCacheFile() #(conn,s) #runServer may be error 

		currentDict=cacheFile.getCurrentDict()
		if currentDict['globalController']==currentDict['masterDB']:
			#masterDB is down
			if currentDict['slaveDB']==None:
				print "cloud is stopping service, cannot restore(no slave db)"
				return
			else:
				#try to connect to slave db
				while True:
					result=connection.socketCall(currentDict['slaveDB'], setting.LOCAL_PORT, 'hello')
					if result=='OK':
						break
					time.sleep(2)
				
				#must promote the slave db up
				print "wait 10 sec"
				time.sleep(10) #wait for every host to repair own ip
				dbService.promote()
				currentDict=cacheFile.getCurrentDict()	#get new masterDB
		
		else:
			#try to connect to master db
			while True:
				result=connection.socketCall(currentDict['masterDB'], setting.LOCAL_PORT, 'hello')
				if result=='OK':
					break
				time.sleep(2)
		
		infoHost=currentDict['masterDB']
		
		#lock dequeuing by global_lock
		db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
		cursor = db.cursor()
		cursor.execute("UPDATE `cloud_variables` SET `value`='1' WHERE `key`='global_lock'")	#don't forget to open when finish everything
		db.close()

		#config and start dhcp server
		dhcpInfo=dhcpController.getDHCPInfoFromDatabase()
		dhcpController.configAll(dhcpInfo['networkID'],dhcpInfo['subnetMask'],dhcpInfo['defaultRoute'],dhcpInfo['dns'],dhcpInfo['hostBindings'],conn,s)
		
		db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
		cursor = db.cursor()
		
		#must repair CA here
		cursor.execute("SELECT `IPAddress` FROM `hosts` WHERE `isCA`=1")
		caIP=cursor.fetchone()[0]
		if caIP==currentDict['masterDB']:
			#CA is down
			if caService.promote()==False:
				print "cannot promote CA, ending"
				return


		#update database
		cursor.execute("UPDATE `hosts` SET `status`=0, `isGlobalController`=0, `inInformationServer`=0, `isCA`=0  WHERE `IPAddress`=%s"%(currentDict['globalController']))
		cursor.execute("UPDATE `hosts` SET `isGlobalController`=1 WHERE `IPAddress`=%s"%(currentDict['myLastIP']))

		#broadcast new global controller
		cursor.execute("SELECT `IPAddress` FROM `hosts` WHERE `status`=1")
		activeHosts=cursor.fetchall()

		dataString=json.dumps({
			'globalController':str(currentDict['myLastIP'])
		})

		for host in activeHosts:
			#every host should be static as it can, in new system
			#if host[0]==currentDict['myLastIP']:
			#	option=[]
			#else:
			#	option=['dynamic']

			result=connection.socketCall(host[0], setting.LOCAL_PORT, 'update_cloud_info', ['{socket_connection}',dataString,'planner']+option)
			if result!='OK':
				print "connection problem, cannot update_cloud_info to",host[0]


		general.runDaemonCommand("service mkapi start",conn,s,True)		#can be true in log system
		
		#fix queue
		cursor.execute("SELECT `taskID`, `processID` FROM `tasks` WHERE `status`=1")
		tmpData=cursor.fetchall()
		for element in tmpData:
			queue.propagateError(element[0])

		#next is check and repair host and guests
		ha.recover()
		
		cursor.execute("UPDATE `cloud_variables` SET `value`='0' WHERE `key`='global_lock'")	#unlock global
		db.close()
		
		#tell queue to do next work
		connection.socketCall("127.0.0.1",setting.WORKER_PORT,'start_work',['{socket_connection}'])

		return

		
def start_slave_global_controller(argv):
	'''
	should be call at 127.0.0.1 (because dhcp is down now)
	command from monitoring service tell that current global controller was downed
	you are the next global controller of this cloud
	'''
	global conn
	global s
	conn = argv[0][0]
	s	 = argv[0][1]
	
	global closeSocketEvent
	closeSocketEvent=argv[0][2]
	aThread=Repair()
	aThread.start()

	return 'OK'
