import setting

from util import connection,general,cacheFile,network
from util import shortcut
from info import dbController

from service import caService,dbService,nfsService,globalService
from scheduling import queue

import MySQLdb
import json

#############################
######## Cloud Zone #########
#############################
class Cloud(object):

	'''
	class GetLimitation():
		def index(self):
			return "OK, I got this message"
		index.exposed = True
	'''
	class GetInfo():
		def index(self):
			infoHost=cacheFile.getDatabaseIP()
			db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
			cursor = db.cursor()
			
			cursor.execute("SELECT `key`,`value` FROM `cloud_variables`")

			cloudData=cursor.fetchall()
			
			valDict={}
			for element in cloudData:
				valDict[element[0]]=element[1]

			cursor.execute("SELECT `IPAddress` FROM `guest_ip_pool`")
			poolData=cursor.fetchall()
			ipList=[]
			for element in poolData:
				ipList.append(element[0])
			
			valDict['guestIPPoolList']=','.join(ipList)

			templateString=open(setting.MAIN_PATH+'webapi/template/cloud_getInfo.xml').read()
			
			content=templateString%valDict
			
			db.close()

			return shortcut.response('success', content)

		index.exposed = True

	class GetStorageInfo():
		def index(self):
			infoHost=cacheFile.getDatabaseIP()
			db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
			cursor = db.cursor()
			
			cursor.execute('''SELECT 
			`hostID`, `IPAddress` 
			FROM `hosts` WHERE `isStorageHolder`=1''')

			hostData=cursor.fetchone()
			hostID=hostData[0]
			hostIP=hostData[1]
		
			data=connection.socketCall("localhost",setting.MONITOR_PORT,"get_current_storage_info",[hostIP])
			data=json.loads(data)
			
			if len(data)==0:
				errorMessage="Data is not ready"
				capacity=errorMessage
				free=errorMessage
				image_usage=errorMessage
				maekin_usage=errorMessage
			else:
				data=data[0]
				capacity=data['storage_info']['capacity']
				free=data['storage_info']['free']
				image_usage=data['storage_info']['image_usage']
				maekin_usage=data['storage_info']['maekin_usage']

			content='''
				<capacity>%s</capacity>
				<maekinUsage>%s</maekinUsage>
				<imageUsage>%s</imageUsage>
				<free>%s</free>
			'''%(str(capacity),str(maekin_usage),str(image_usage),str(free))
			
			db.close()

			return shortcut.response('success', content)

		index.exposed = True

	class MigrateInformationService():
		def index(self,targetHostID):
			detail={
			'command':'database_migrate',
			'targetHostID':targetHostID
			}

			taskID=queue.enqueue(detail)

			return shortcut.responseTaskID(taskID)
			
		index.exposed = True

	class MigrateCA():
		def index(self,targetHostID):
			detail={
			'command':'ca_migrate',
			'targetHostID':targetHostID
			}

			taskID=queue.enqueue(detail)

			return shortcut.responseTaskID(taskID)

		index.exposed = True
	
	class MigrateGlobalController():
		def index(self,targetHostID):
			detail={
			'command':'global_migrate',
			'targetHostID':targetHostID
			}

			taskID=queue.enqueue(detail)

			return shortcut.responseTaskID(taskID)

		index.exposed = True
	
	class MigrateNFS():
		def index(self,targetHostID):
			detail={
			'command':'nfs_migrate',
			'targetHostID':targetHostID
			}

			taskID=queue.enqueue(detail)

			return shortcut.responseTaskID(taskID)

		index.exposed = True

	class SetAutoMode():
		def index(self,mode):
			if mode not in ['0','1','2']:
				return shortcut.response('error','','mode can be 0, 1 or 2 only')
			
			infoHost=cacheFile.getDatabaseIP()
			db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
			cursor = db.cursor()
			
			cursor.execute("UPDATE `cloud_variables` SET `value`='%s' WHERE `key`='auto_mode'"%(mode))

			db.close()
			
			content=''
			return shortcut.response('success',content)
		index.exposed = True

	class SetLogMode():
		def index(self,mode):
			if mode not in ['0','1']:
				return shortcut.response('error','','mode can be 0 or 1 only')
			
			infoHost=cacheFile.getDatabaseIP()
			db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
			cursor = db.cursor()
			
			cursor.execute("UPDATE `cloud_variables` SET `value`='%s' WHERE `key`='hold_all_log'"%(mode))

			db.close()
			
			content=''
			return shortcut.response('success',content)
		index.exposed = True

	class ClearOldLog():
		def index(self):			
			infoHost=cacheFile.getDatabaseIP()
			db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
			cursor = db.cursor()
			
			cursor.execute("DELETE FROM `oldHostLoad` WHERE 1")
			cursor.execute("DELETE FROM `oldGuestLoad` WHERE 1")

			db.close()
			
			content=''
			return shortcut.response('success',content)
		index.exposed = True

	#getLimitation = GetLimitation()
	getInfo = GetInfo()
	getStorageInfo = GetStorageInfo()
	
	migrateInformationService = MigrateInformationService()
	migrateCA = MigrateCA()
	migrateGlobalController = MigrateGlobalController()

	migrateNFS = MigrateNFS()	  

	setAutoMode = SetAutoMode()
	setLogMode = SetLogMode()
	clearOldLog = ClearOldLog()