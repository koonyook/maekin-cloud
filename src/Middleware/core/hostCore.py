import setting

from util import connection,general,cacheFile,network
from util import ping
from util import shortcut
from info import dbController
from planning import planTool

from scheduling import mission

from service import caService,dbService,nfsService,globalService

import time
import subprocess,shlex
import MySQLdb
import json
from datetime import datetime

def createHostClearingDetailList(hostID,taskID,migrateService=True):
	'''
	add locking more host at the end
	'''
	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	
	cursor.execute('''
	SELECT `isHost`,`isGlobalController`,`isInformationServer`,`isStorageHolder`,`isCA`,`status`,`activity`,`IPAddress`,`MACAddress`
	FROM `hosts` WHERE `hostID`=%s'''%(str(hostID)))
	
	hostData=cursor.fetchone()
	if hostData==None:
		return 'createHostClearingDetailList error, host not found'
	
	isHost,isGlobalController,isInformationServer,isStorageHolder,isCA,status,activity,IPAddress,MACAddress=hostData

	if status!=1:
		return 'this host is already turned off'

	if isStorageHolder==1 and migrateService==True:
		return 'this host is nfs server (cannot be clear)'
	
	if activity!=0:
		return 'this host is busy (try again later)'
	
	cursor.execute("SELECT `guestID` FROM `guests` WHERE `status`=1 AND `lastHostID`=%s"%(str(hostID)))
	victimGuestList=cursor.fetchall()
	victimGuestNumber=len(victimGuestList)

	#we need at lease 1 free active host to be a destination of guests and services
	cursor.execute("SELECT `hostID` FROM `hosts` WHERE `status`=1 AND `activity`=0 AND `isHost`=1 AND `hostID`<>%s"%(str(hostID)))
	destHostList=cursor.fetchall()

	if migrateService==True:
		if len(destHostList)==0 and (isGlobalController==1 or isInformationServer==1 or isCA==1 or victimGuestNumber>0):
			return 'no free active host to be destination of guests and services'
	else:
		if len(destHostList)==0 and victimGuestNumber>0:
			return 'no free active host to be destination of guests'

	tmpList=[]
	for element in destHostList:
		tmpList.append(element[0])
	destHostList=tmpList
	
	#ready to do
	cursor.execute("UPDATE `hosts` SET `activity`=1 WHERE `hostID`=%s"%(str(hostID)))

	detailList=[]
	moreLockedHost=[]
	
	if (migrateService==True and (isGlobalController==1 or isInformationServer==1 or isCA==1)) or len(victimGuestList)>0:
		weightData=planTool.getWeightData(destHostList)
	else:
		weightData=None
	
	#migrate services on this hosts
	if migrateService==True:
		if isGlobalController==1:
			targetHostID=planTool.weightRandom(destHostList,weightData)
			detailList.append({
				'command':'global_migrate',
				'targetHostID':targetHostID
			})
			if targetHostID not in moreLockedHost:
				moreLockedHost.append(targetHostID)

		if isInformationServer==1:
			targetHostID=planTool.weightRandom(destHostList,weightData)
			detailList.append({
				'command':'database_migrate',
				'targetHostID':targetHostID
			})
			if targetHostID not in moreLockedHost:
				moreLockedHost.append(targetHostID)
		
		if isCA==1:
			targetHostID=planTool.weightRandom(destHostList,weightData)
			detailList.append({
				'command':'ca_migrate',
				'targetHostID':targetHostID
			})
			if targetHostID not in moreLockedHost:
				moreLockedHost.append(targetHostID)

	#migrate active guests on this hosts 
	for element in victimGuestList:
		guestID=element[0]
		targetHostID=planTool.weightRandom(destHostList,weightData)
		detailList.append({
			'command':'guest_migrate',
			'guestID':guestID,
			'targetHostID':targetHostID
		})
		if targetHostID not in moreLockedHost:
			moreLockedHost.append(targetHostID)
	
	#and lock destination (insert if not exists)
	if len(moreLockedHost)>0:
		lockValueList=[]
		for lockedHostID in moreLockedHost:
			lockValueList.append("(%s,%s)"%(str(taskID),str(lockedHostID)))

		cursor.execute("INSERT IGNORE INTO `lockedHosts` (`taskID`,`hostID`) VALUES %s"%(','.join(lockValueList)))

	db.close()

	return detailList

def host_close(taskID,detail):
	#get parameter
	hostID=detail['hostID']
	mode = detail['mode']
	
	#check that active isHost is left in cloud (except me)
	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	cursor.execute("SELECT `hostID` FROM `hosts` WHERE `status`=1 AND `isHost`=1 AND `hostID`<>%s"%(str(hostID)))
	tmp=cursor.fetchone()
	db.close()
	if tmp==None:
		return "this host is the last active host that have isHost=1, cannot close"

	#start work
	detailList=createHostClearingDetailList(hostID,taskID)
	
	if type(detailList)!=type([]):
		return str(detailList)

	success=mission.addSubTasks(taskID,detailList)
	if success:
		return 'OK'
	else:
		return "addSubtasks fail"

def host_close_ending(taskID):

	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	#get ip of target host
	cursor.execute("SELECT `detail` FROM `tasks` WHERE `taskID`=%s"%(str(taskID)))
	detail=cursor.fetchone()[0]
	detail=json.loads(detail)

	hostID=detail['hostID']
	mode=detail['mode']

	cursor.execute("SELECT `IPAddress` FROM `hosts` WHERE `hostID`=%s"%(str(hostID)))
	targetHostIP=cursor.fetchone()[0]
	
	#check that target is slave db or not and destroy it
	cursor.execute("SELECT `IPAddress` FROM `hosts` WHERE `hostID`=%s AND `isInformationServer`=2"%(str(hostID)))
	if cursor.fetchone()!=None:
		result=connection.socketCall(targetHostIP,setting.LOCAL_PORT,'destroy_slave_host_info')
	
	#and destroy CA via database
	cursor.execute("UPDATE `hosts` SET `isCA`=0 WHERE `hostID`=%s"%(str(hostID)))

	result=connection.socketCall(targetHostIP,setting.LOCAL_PORT,'close_your_host',['{socket_connection}',mode])
	
	#update host activity and status
	if mode=='standby':
		newStatus=2
	elif mode=='hibernate':
		newStatus=3
	elif mode=='shutdown':
		newStatus=0
	else:
		print "this line cannot happen, mode=",mode
		newStatus=-1

	cursor.execute("UPDATE `hosts` SET `activity`=0, `status`=%s WHERE `hostID`=%s"%(str(newStatus),str(hostID)))

	db.close()
	print "finish closing"
	return "OK"

def host_close_error(taskID):

	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	#get ID of target host
	cursor.execute("SELECT `detail` FROM `tasks` WHERE `taskID`=%s"%(str(taskID)))
	detail=cursor.fetchone()[0]
	detail=json.loads(detail)

	hostID=detail['hostID']

	cursor.execute("UPDATE `hosts` SET `activity`=0 WHERE `hostID`=%s"%(str(hostID)))

	db.close()
	print "finish cleaning host activity after error. hostID=",hostID
	return "OK"

def host_evacuate_mission(taskID,detail):
	#get parameter
	hostID=detail['hostID']

	#start work
	detailList=createHostClearingDetailList(hostID,taskID,migrateService=False)
	
	if type(detailList)!=type([]):
		return str(detailList)

	success=mission.addSubTasks(taskID,detailList)
	if success:
		return 'OK'
	else:
		return "addSubtasks fail"

def host_evacuate_mission_ending(taskID):

	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	
	cursor.execute("SELECT `detail` FROM `tasks` WHERE `taskID`=%s"%(str(taskID)))
	detail=cursor.fetchone()[0]
	detail=json.loads(detail)

	hostID=detail['hostID']

	cursor.execute("UPDATE `hosts` SET `activity`=0 WHERE `hostID`=%s"%(str(hostID)))

	db.close()
	print "finish evacuating"
	return "OK"

def host_evacuate_mission_error(taskID):

	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	
	cursor.execute("SELECT `detail` FROM `tasks` WHERE `taskID`=%s"%(str(taskID)))
	detail=cursor.fetchone()[0]
	detail=json.loads(detail)

	hostID=detail['hostID']

	cursor.execute("UPDATE `hosts` SET `activity`=0 WHERE `hostID`=%s"%(str(hostID)))

	db.close()
	print "finish cleaning host activity after error. hostID=",hostID
	return "OK"

def host_wakeup(taskID,detail):
	'''
	this is primary work
	bring it back in every situation and wait until i can say hello to mklocd of that host
	'''
	#get parameter
	hostID=detail['hostID']

	#find mac address and send magic packet
	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()

	cursor.execute("SELECT `MACAddress`,`IPAddress`,`status` FROM `hosts` WHERE `hostID`=%s"%(str(hostID)))
	hostData=cursor.fetchone()

	if hostData==None:
		return 'host not found'
	
	targetHostMAC,targetHostIP,status=hostData
	
	#update activity
	cursor.execute("UPDATE `hosts` SET `activity`=2 WHERE `hostID`=%s"%(str(hostID)))

	result = subprocess.Popen(shlex.split("ether-wake -i br0 %s"%(targetHostMAC)),stdout=subprocess.PIPE)
	result.wait()

	#check with ping until it get ip
	start_ping_time=datetime.now()
	while ping.check(targetHostIP,2)==False:
		pingtime=(datetime.now()-start_ping_time).seconds
		if pingtime>setting.MAXIMUM_BOOT_TIME:
			cursor.execute("UPDATE `hosts` SET `activity`=0 WHERE `hostID`=%s"%(str(hostID)))
			db.close()
			return 'boot time exceed'
		result = subprocess.Popen(shlex.split("ether-wake -i br0 %s"%(targetHostMAC)),stdout=subprocess.PIPE)
		result.wait()
		pass
	
	#check with socketCall until mklocd is up
	while True:
		result=connection.socketCall(targetHostIP,setting.LOCAL_PORT,'hello')
		if result=='OK':
			break
		else:
			pingtime=(datetime.now()-start_ping_time).seconds
			if pingtime>setting.MAXIMUM_BOOT_TIME:
				cursor.execute("UPDATE `hosts` SET `activity`=0 WHERE `hostID`=%s"%(str(hostID)))
				db.close()
				return 'boot time exceed'
			time.sleep(2)
	
	#update data and mount folder at targetHost
	currentDict=cacheFile.getCurrentDict()
	currentDict['myLastIP']=str(targetHostIP)
	
	if status==0:	#case of boot host from shutoff state
		moreOption=['planner']	#must start mkplanner
	else:
		moreOption=[]
	connection.socketCall(targetHostIP,setting.LOCAL_PORT,'update_cloud_info',['{socket_connection}',json.dumps(currentDict),'nfs']+moreOption)

	#update to database
	cursor.execute("UPDATE `hosts` SET `activity`=0, `status`=1 WHERE `hostID`=%s"%(str(hostID)))

	db.close()
	print "finish wake up"
	return "OK"

def host_remove(taskID,detail):
	#get parameter
	hostID=detail['hostID']

	#check that active isHost is left in cloud (except me)
	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	cursor.execute("SELECT `hostID` FROM `hosts` WHERE `status`=1 AND `isHost`=1 AND `hostID`<>%s"%(str(hostID)))
	tmp=cursor.fetchone()
	db.close()
	if tmp==None:
		return "this host is the last active host that have isHost=1, cannot remove"


	#start work
	detailList=createHostClearingDetailList(hostID,taskID)
	
	if type(detailList)!=type([]):
		return str(detailList)

	success=mission.addSubTasks(taskID,detailList)
	if success:
		return 'OK'
	else:
		return "addSubtasks fail"

	
def host_remove_ending(taskID):

	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	#get ip of target host
	cursor.execute("SELECT `detail` FROM `tasks` WHERE `taskID`=%s"%(str(taskID)))
	detail=cursor.fetchone()[0]
	detail=json.loads(detail)

	hostID=detail['hostID']

	cursor.execute("SELECT `IPAddress`,`MACAddress` FROM `hosts` WHERE `hostID`=%s"%(str(hostID)))
	targetHostIP,targetHostMAC=cursor.fetchone()
	
	#unmount at that host
	result=connection.socketCall(targetHostIP,setting.LOCAL_PORT,'nfs_umount')
	if result!='OK':
		return result
	
	#stop mkplanner at that host
	result=connection.socketCall(targetHostIP,setting.LOCAL_PORT,'stop_mkplanner')
	if result!='OK':
		return result
		
	#check that target is slave db or not and destroy it
	cursor.execute("SELECT `hostID` FROM `hosts` WHERE `IPAddress`='%s' AND `isInformationServer`=2"%(str(targetHostIP)))
	if cursor.fetchone()!=None:
		result=connection.socketCall(targetHostIP,setting.LOCAL_PORT,'destroy_slave_host_info')
		if result!='OK':
			return result
	
	#remove at nfs export file
	cursor.execute("SELECT `IPAddress` FROM `hosts` WHERE `isStorageHolder`=1")
	nfsHostIP=cursor.fetchone()[0]
	result=connection.socketCall(nfsHostIP,setting.LOCAL_PORT,'nfs_refresh_export',[targetHostIP])
	if result!='OK':
		return result
	
	#unbind at dhcp config file
	cursor.execute("SELECT `IPAddress` FROM `hosts` WHERE `isGlobalController`=1")
	dhcpHostIP=cursor.fetchone()[0]
	result=connection.socketCall(dhcpHostIP,setting.LOCAL_PORT,'dhcp_unbind_host',[targetHostMAC,targetHostIP,'{socket_connection}'])
	if result!='OK':
		return result
	
	# ** remove cacheFile and restart mklocd for wait new ip **
	result=connection.socketCall(targetHostIP,setting.LOCAL_PORT,'remove_cache_and_restart_mklocd',['{socket_connection}'])
	if result!='OK':
		return result
	
	#delete this host from database
	cursor.execute("DELETE FROM `hosts` WHERE `hostID`=%s"%(str(hostID)))

	db.close()
	print "finish removing"
	return "OK"

def host_remove_error(taskID):

	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	
	cursor.execute("SELECT `detail` FROM `tasks` WHERE `taskID`=%s"%(str(taskID)))
	detail=cursor.fetchone()[0]
	detail=json.loads(detail)

	hostID=detail['hostID']

	cursor.execute("UPDATE `hosts` SET `activity`=0 WHERE `hostID`=%s"%(str(hostID)))

	db.close()
	print "finish cleaning host activity after error. hostID=",hostID
	return "OK"


def host_add(taskID, detail):
	'''
	this is primary work
	bring it back in every situation and wait until i can say hello to mklocd of that host
	'''
	#get parameter
	hostName=detail['hostName']
	targetHostMAC=str(detail['MACAddress'])
	targetHostIP=detail['IPAddress']
	
	if not general.isGoodName(hostName,allowDot=True):
		return 'Name '+hostName+' cannot be a guestName, please choose the new one.'
	
	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()

	#check if exist
	cursor.execute("SELECT `IPAddress` FROM `guest_ip_pool` WHERE `IPAddress`='%s'"%(str(targetHostIP)))
	if cursor.fetchone()!=None:
		return "this IP Address is already used"

	cursor.execute("SELECT `IPAddress` FROM `hosts` WHERE `IPAddress`='%s' OR `MACAddress`='%s' OR `hostName`='%s'"%(str(targetHostIP),str(targetHostMAC),hostName))
	if cursor.fetchone()!=None:
		return "this IP Address or MAC Address or hostName is already used"

	
	#bind at dhcpServer
	cursor.execute("SELECT `IPAddress` FROM `hosts` WHERE `isGlobalController`=1")
	dhcpHostIP=cursor.fetchone()[0]
	result=connection.socketCall(dhcpHostIP,setting.LOCAL_PORT,'dhcp_bind_host',[targetHostMAC,targetHostIP,hostName,'{socket_connection}'])
	if result!='OK':
		return result

	#send magic packet
	result = subprocess.Popen(shlex.split("ether-wake -i br0 %s"%(targetHostMAC)),stdout=subprocess.PIPE)
	result.wait()
	
	#check with ping until it get ip
	start_ping_time=datetime.now()
	while ping.check(targetHostIP,2)==False:
		pingtime=(datetime.now()-start_ping_time).seconds
		if pingtime>setting.MAXIMUM_BOOT_TIME:
			return 'add_host time exceed'
		result = subprocess.Popen(shlex.split("ether-wake -i br0 %s"%(targetHostMAC)),stdout=subprocess.PIPE)
		result.wait()
		pass
	
	#check with socketCall until mklocd is up
	while True:
		result=connection.socketCall(targetHostIP,setting.LOCAL_PORT,'hello')
		if result=='OK':
			break
		else:
			pingtime=(datetime.now()-start_ping_time).seconds
			if pingtime>setting.MAXIMUM_BOOT_TIME:
				return 'add_host time exceed'
			time.sleep(2)

	#assign hostname to new host
	result=connection.socketCall(targetHostIP, setting.LOCAL_PORT, 'assign_hostname',[hostName])
	if result!='OK':
		return result

	#create pki of new host
	cursor.execute("SELECT `IPAddress` FROM `hosts` WHERE `isCA`=1")
	CAHostIP=cursor.fetchone()[0]
	result=connection.socketCall(targetHostIP, setting.LOCAL_PORT, 'update_pki', ['{socket_connection}',CAHostIP])	#save load of database
	if result!='OK':
		return result

	#update data and mount folder at targetHost
	currentDict=cacheFile.getCurrentDict()
	currentDict['myLastIP']=str(targetHostIP)
	connection.socketCall(targetHostIP,setting.LOCAL_PORT,'update_cloud_info',['{socket_connection}',json.dumps(currentDict),'nfs','planner'])

	hostSpec=connection.socketCall(targetHostIP, setting.LOCAL_PORT, 'ask_your_spec')
	hostSpec=json.loads(hostSpec)
	cpuCore=hostSpec['cpu']['number']
	cpuSpeed=hostSpec['cpu']['speed']

	#insert to database 
	cursor.execute('''
	INSERT INTO `hosts` (`hostName`, `MACAddress`, `IPAddress`, `isHost`, `isGlobalController`, `isInformationServer`, `isStorageHolder`,`isCA`, `status`, `activity`,`cpuCore`,`cpuSpeed`) VALUES ('%s','%s','%s',1,0,0,0,0,0,2,'%s','%s');
'''%(hostName,targetHostMAC,targetHostIP,cpuCore,cpuSpeed))
	
	hostID=cursor.lastrowid
	
	#lock this host
	cursor.execute("INSERT IGNORE INTO `lockedHosts` (`taskID`,`hostID`) VALUES (%s,%s)"%(str(taskID),str(hostID)))

	#update to database
	cursor.execute("UPDATE `hosts` SET `activity`=0, `status`=1 WHERE `hostID`=%s"%(str(hostID)))

	db.close()
	
	content='<host hostID="%s" />'%(str(hostID))
	
	if not shortcut.storeFinishMessage(taskID,content):
		return "cannot storeFinishMessage"

	print "finish adding host"
	return "OK"
