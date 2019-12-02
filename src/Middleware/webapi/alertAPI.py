import setting
from util import connection,general,shortcut,cacheFile,psutil
from util import ha
from scheduling import queue
from service import dbService,caService

import threading
#############################
######## Alert Zone #########
#############################
class Alert(object):

	class RepairThread(threading.Thread):

		def setArguments(self,hostIP):
			self.hostIP = hostIP

		def run(self):
			victimIP=self.hostIP

			#check database service
			currentDict=chacheFile.getCurrentDict()
			oldMasterDB=currentDict['masterDB']
			if oldMasterDB==victimIP:
				#masterDB is down
				if currentDict['slaveDB']==None:
					print "cloud is stopping service, cannot restore(no slave db)"
					return
				else:
					#must promote the slave db up
					dbService.promote()
			
			infoHost=cacheFile.getDatabaseIP()
			if infoHost==oldMasterDB:
				print 'promotion error, master database do not change'
				return
			
			db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
			cursor = db.cursor()
			
			#global_lock
			cursor.execute("UPDATE `cloud_variables` SET `value`='1' WHERE `key`='global_lock'")	#don't forget to open when finish everything

			#check CA service
			cursor.execute("SELECT `IPAddress` FROM `hosts` WHERE `isCA`=1")
			caIP=cursor.fetchone()[0]
			if caIP==victimIP:
				#CA is down
				if caService.promote()==False:
					print "cannot promote CA, ending"
					return

			#check and repair hosts and guests
			if victimIP==oldMasterDB:
				#kill all of task that alive and mark as error in database
				cursor.execute("SELECT `taskID`, `processID` FROM `tasks` WHERE `status`=1")
				tmpData=cursor.fetchall()
				for element in tmpData:
					psutil.waitProcessFinish(element[1])
					queue.propagateError(element[0])

			else:
				#victim is normal host
				#wait until all task has finished
				while True:
					cursor.execute("SELECT `taskID` FROM `tasks` WHERE `status`=1")
					if cursor.fetchone()==None:
						break
					time.sleep(2)

			ha.recover()
		
			cursor.execute("UPDATE `cloud_variables` SET `value`='0' WHERE `key`='global_lock'")	#unlock global
			db.close()
			
			#tell queue to do next work
			connection.socketCall("127.0.0.1",setting.WORKER_PORT,'start_work',['{socket_connection}'])

			return
	
	class HostDisconnected():
		def index(self,hostIP):
			#if this method not work, It should change to socketCall to localhost and do like this
			aThread=RepairThread()
			aThread.setArguments(hostIP)
			aThread.start()

			return shortcut.response('success','',"OK, I got this message")
		index.exposed = True

	class HostConnected():
		def index(self,hostIP):
			#just log to database as event

			return shortcut.response('success','',"OK, I got this message")
		index.exposed = True

	class HostOverheat():
		def index(self,hostIP):
			#just log to database as event

			return shortcut.response('success','',"OK, I got this message")
		index.exposed = True

	hostDisconnected = HostDisconnected()
	hostConnected = HostConnected()
	hostOverheat = HostOverheat()

