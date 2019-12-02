import setting

from util import connection,general,cacheFile,network
from util import shortcut
from info import dbController

from service import caService,dbService,nfsService,globalService

import os
import time
import MySQLdb
import json

def blank_task(taskID, detail):
	return 'OK'

def database_migrate(taskID,detail):
	#get parameter
	targetHostID=detail['targetHostID']

	#start work
	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	
	cursor.execute('''SELECT 
	`IPAddress`
	FROM `hosts` WHERE `hostID`=%s AND `status`=1'''%(str(targetHostID)))

	hostData=cursor.fetchone()
	db.close()
	
	if hostData==None:
		return 'targetHostID not found or targetHostID is turned off'
	
	targetHostIP=hostData[0]

	dbService.migrate(targetHostIP)

	return 'OK'

def ca_migrate(taskID,detail):
	#get parameter
	targetHostID=detail['targetHostID']

	#start work
	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	
	cursor.execute('''SELECT 
	`IPAddress`
	FROM `hosts` WHERE `hostID`=%s AND `status`=1'''%(str(targetHostID)))

	targetHostData=cursor.fetchone()
	db.close()
	
	if targetHostData==None:
		return 'targetHostID not found or targetHostID is turned off'

	targetHostIP=targetHostData[0]

	success=caService.migrate(targetHostIP)

	if not success:
		return 'ca migration error'

	return 'OK'

def global_migrate(taskID,detail):
	'''
	very complicated
	'''
	#get parameter
	targetHostID=detail['targetHostID']

	#start work
	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	
	cursor.execute('''SELECT 
	`IPAddress`
	FROM `hosts` WHERE `hostID`=%s AND `status`=1'''%(str(targetHostID)))

	targetHostData=cursor.fetchone()
	db.close()
	
	if targetHostData==None:
		return 'targetHostID not found or targetHostID is turned off'

	targetHostIP=targetHostData[0]
	
	#this step must do by mklocd because mkworker will be terminated during this method
	#success=globalService.migrate(targetHostIP)
	#result=connection.socketCall("localhost",setting.LOCAL_PORT,'call_globalService_migrate',['{socket_connection}',str(targetHostIP),str(taskID)]))
	success=globalService.migrate(targetHostIP)

	if not success:
		return 'global controller migration error:'
	
	#this method must block until the mkworker service on this host has stoped
	#while True:
	#	time.sleep(100)			#I will be killed at this line (the rest work will be done by call_globalService_migrate at mklocd on this host)

	return 'OK'

def nfs_migrate(taskID,detail):
	'''
	migrate nfs server
	*** this method should be fixed if you want to use ***
	*** I'm sure that now it's full of error ***
	'''
	#no need of global_lock because this method use -1 as very big lock
	#get parameter
	targetHostID=detail['targetHostID']

	#start work
	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	#cursor.execute("UPDATE `cloud_variables` SET `value`='1' WHERE `key`='global_lock'")	
	
	#check that no guest is running or having activity
	cursor.execute("SELECT `guestID` FROM `guests` WHERE `activity`<>0 OR `status`=1")
	if cursor.fetchone()!=None:
		db.close()
		return 'All guests must not be running or doing any activity'

	#check that no host have activity
	cursor.execute("SELECT `hostID` FROM `hosts` WHERE `activity`<>0")
	if cursor.fetchone()!=None:
		db.close()
		return 'All hosts must not be doing any activity' 
	
	#check that no working task in queue (except me)
	cursor.execute("SELECT `taskID` FROM `tasks` WHERE `status`=1")
	while True:
		tmp=cursor.fetchone()
		if tmp==None:
			break
		elif tmp[0]==taskID:
			continue
		else:
			db.close()
			return 'All tasks must finish before migrate nfs server'
	
	#check that targetHostID is ON
	cursor.execute("SELECT `status`, `IPAddress` FROM `hosts` WHERE `hostID`=%s"%(targetHostID))
	tmp=cursor.fetchone()
	if tmp==None:
		db.close()
		return 'target host not found'
	elif tmp[0]!=1:
		db.close()
		return 'target host is shutedoff'
	
	targetHostIP=tmp[1]

	#check ip of old nfs server
	cursor.execute("SELECT `status`, `IPAddress` FROM `hosts` WHERE `isStorageHolder`=1")
	tmp=cursor.fetchone()
	if tmp==None:
		db.close()
		return 'nfs host not found???'
	elif tmp[0]!=1:
		db.close()
		return 'nfs host is shutedoff???'
	
	nfsHostIP=tmp[1]

	#list all file to copy ( template, .img , .sav )
	filenameList=[]
	
	#template
	cursor.execute("SELECT `fileName` FROM `templates`")
	templatePathList=[]
	while True:
		tmp=cursor.fetchone()
		if tmp!=None:
			templatePathList.append(setting.TEMPLATE_PATH+tmp[0])
		else:
			break
	
	result=connection.socketCall(str(nfsHostIP),setting.LOCAL_PORT,'get_file_size',templatePathList)
	try:
		sizeList=json.loads(result)
	except:
		return result
	
	for i in range(len(templatePathList)):
		if sizeList[i]<=0:
			return "file "+templatePathList[i]+" have problem"
		filenameList.append([templatePathList[i],sizeList[i]])

	#guest image
	cursor.execute("SELECT `volumeFileName` FROM `guests`")
	while True:
		tmp=cursor.fetchone()
		if tmp!=None:
			filenameList.append([setting.IMAGE_PATH+tmp[0],os.path.getsize(setting.TARGET_IMAGE_PATH+tmp[0])])
		else:
			break
	
	#saved image
	cursor.execute("SELECT `volumeFileName` FROM `guests` WHERE `status`=2")
	while True:
		tmp=cursor.fetchone()
		if tmp!=None:
			savFilename=general.imgToSav(tmp[0])
			filenameList.append([setting.IMAGE_PATH+savFilename,os.path.getsize(setting.TARGET_IMAGE_PATH+savFilename)])
		else:
			break
	
	#check that all of the file has coppied to destination
	result=connection.socketCall(targetHostIP,setting.LOCAL_PORT,'check_nfs_migrate_destination_has_coppied',[json.dumps(filenameList)])
	
	if result!='OK':
		return result
	
	"""
	#check rest area on disk weather it's enough or not
	result=connection.socketCall(targetHostIP,setting.LOCAL_PORT,'check_nfs_migrate_destination_area',[json.dumps(filenameList)])
	
	if result!='OK':
		return result

	#copying file via nfs (when each file finish i should put result in finish message)
	result=connection.socketCall(targetHostIP,setting.LOCAL_PORT,'transfer_all_file',[json.dumps(filenameList),str(taskID)])
	if result!='OK':
		return result
	"""

	#setup config for new nfs host
	cursor.execute("SELECT `IPAddress` FROM `hosts`")
	hostIPList=[]
	while True:
		tmp=cursor.fetchone()
		if tmp!=None:
			hostIPList.append(tmp[0])
		else:
			break

	result=connection.socketCall(targetHostIP, setting.LOCAL_PORT, 'you_are_nfs_server',[json.dumps(hostIPList),"{socket_connection}"])
	if result!='OK':
		return result
	
	#close old nfs server
	result=connection.socketCall(nfsHostIP, setting.LOCAL_PORT, 'stop_nfs_server')
	if result!='OK':
		return result

	#update storageHolder in database
	cursor.execute("UPDATE `hosts` SET `isStorageHolder`=0")
	cursor.execute("UPDATE `hosts` SET `isStorageHolder`=1 WHERE `hostID`=%s"%(targetHostID))
	
	#umount and mount on every hosts (via update cloud info)
	cursor.execute("SELECT `IPAddress` FROM `hosts` WHERE `status`=1")
	activeHostIP=[]
	while True:
		tmp=cursor.fetchone()
		if tmp!=None:
			activeHostIP.append(tmp[0])
		else:
			break
	
	for hostIP in activeHostIP:
		result=connection.socketCall(hostIP, setting.LOCAL_PORT, 'update_cloud_info', ['{socket_connection}',{},'nfs'])
		if result!='OK':
			return result
	
	#unlock global lock
	#cursor.execute("UPDATE `cloud_variables` SET `value`='0' WHERE `key`='global_lock'")

	db.close()

	return "OK"
