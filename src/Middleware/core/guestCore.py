import setting
from util import connection,cacheFile,network,general
from util import shortcut
from dhcp import dhcpController
from planning import planTool

import MySQLdb
import json
import os
import random

"""
error = just return a string
success = shortcut.storeFinishMessage("my message") and return "OK"

"""

def guest_create(taskID,detail):
	#get parameter
	guestName=detail['guestName']
	templateID=detail['templateID']
	memory=detail['memory']
	vCPU=detail['vCPU']
	key=detail.keys()
	
	if 'inbound' in key:
		inbound=detail['inbound']
	else:
		inbound=None

	if 'outbound' in key:
		outbound=detail['outbound']
	else:
		outbound=None

	#start the work
	if not general.isGoodName(guestName):
		return 'Name '+guestName+' cannot be a guestName, please choose the new one.'

	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	#find template
	cursor.execute("SELECT `templateID`, `fileName`,`size`,`minimumMemory`,`maximumMemory` FROM `templates` WHERE `activity`=0 AND `templateID`=%s"%(str(templateID)))
	targetTemplate = cursor.fetchone()
	if targetTemplate==None:
		return 'Invalid templateID or template is busy'
	
	if int(memory)<int(targetTemplate[3]) or int(memory)>int(targetTemplate[4]):
		return 'Invalid momory size'
	
	imageSize=int(targetTemplate[2])	#unit is byte
	#find storageHolder
	cursor.execute("SELECT `hostID`, `IPAddress` FROM `hosts` WHERE `isStorageHolder`=1")
	storageHolder=cursor.fetchone()
	
	#check storage
	storageInfo=connection.socketCall('localhost',setting.MONITOR_PORT,'get_current_storage_info', [str(storageHolder[1])])
	if json.loads(storageInfo)==[]:
		return "Data is not ready, please try again later."
	freeSpace=int(json.loads(storageInfo)[0]['storage_info']['free'])	#unit is Kbyte
	if imageSize>freeSpace*1024:
		return "Do not have enough space for cloning this image"
	
	#random mac address until not exist in hosts and guests
	cursor.execute('''
	SELECT `MACAddress` FROM `hosts` 
	UNION 
	SELECT `MACAddress` FROM `guests`''')
	usedMAC=cursor.fetchall()
	while True:
		newMAC=network.randomMAC()
		if (newMAC,) in usedMAC:
			continue
		else:
			break

	#find rest ip from {guest_ip_pool}-{guests}
	cursor.execute('''
	SELECT `guest_ip_pool`.`IPAddress` FROM 
		`guest_ip_pool` LEFT JOIN `guests` ON `guest_ip_pool`.`IPAddress`=`guests`.`IPAddress`
	WHERE `guests`.`IPAddress` IS NULL
	''')
	freeIP=cursor.fetchall()
	if len(freeIP)==0:
		return "Out of IP address"
	else:
		#select the minimum from freeIP
		newIP=freeIP[0][0]
		for eachIP in freeIP:
			if network.IPAddr(eachIP[0]).getProduct()<network.IPAddr(newIP).getProduct():
				newIP=eachIP[0]

	#find image file name
	usedImageNames=os.listdir(setting.TARGET_IMAGE_PATH)
	volumeFileName=guestName+'.img'
	count=2
	while volumeFileName in usedImageNames :
		volumeFileName=guestName+'('+str(count)+').img'
		count+=1
			
	if inbound==None:
		inboundString="NULL"
	else:
		inboundString="'%s'"%(str(inbound))

	if outbound==None:
		outboundString="NULL"
	else:
		outboundString="'%s'"%(str(outbound))
	cursor.execute('''
	INSERT INTO `guests` (`guestName`, `MACAddress`, `IPAddress`, `volumeFileName`, `templateID`, `activity`,`memory`,`vCPU`,`inboundBandwidth`,`outboundBandwidth`) VALUES
	('%(guestName)s', '%(MACAddress)s', '%(IPAddress)s', '%(volumeFileName)s', '%(templateID)s', '%(activity)s', '%(memory)s', '%(vCPU)s', %(inboundBandwidth)s, %(outboundBandwidth)s);
	'''%{
	'guestName':guestName,
	'MACAddress':newMAC,
	'IPAddress':newIP,
	'volumeFileName':volumeFileName,
	'templateID':templateID,
	'activity':1,		#cloning
	'memory':memory,
	'vCPU':vCPU,
	'inboundBandwidth':inboundString,
	'outboundBandwidth':outboundString
	})
	#find the guestID of new image
	#cursor.execute('''SELECT `guestID` FROM `guests` WHERE `MACAddress`='%s';'''%(newMAC))
	#guestID=cursor.fetchone()[0]
	#I have eiser way to find ID
	guestID=cursor.lastrowid
	
	#lock new guest
	cursor.execute("INSERT IGNORE INTO `lockedGuests` (`taskID`,`guestID`) VALUES (%s,%s)"%(str(taskID),str(guestID)))

	db.close()

	result=connection.socketCall(str(storageHolder[1]),setting.LOCAL_PORT,'guest_create',[str(targetTemplate[1]),volumeFileName,str(guestID),str(taskID)])
	if result!='OK':
		#delete this guest in database
		cursor.execute("DELETE FROM `guests` WHERE `guestID`=%s"%(guestID))
		return result
	
	#set dhcp about new guest
	dhcpController.bind([(newMAC,newIP,guestName)])

	content='<guest guestID="%s" />'%(str(guestID))
	
	if not shortcut.storeFinishMessage(taskID,content):
		return "cannot storeFinishMessage"

	return "OK"

def guest_duplicate(taskID,detail):
	#get parameter
	guestName=detail['guestName']
	sourceGuestID=detail['sourceGuestID']
	
	#start the work
	if not general.isGoodName(guestName):
		return 'Name '+guestName+' cannot be a guestName, please choose the new one.'

	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	#find sourceGuestID and template data
	cursor.execute("""SELECT 
	`templates`.`size`, 
	`templates`.`minimumMemory`, 
	`templates`.`maximumMemory`,
	`guests`.`volumeFileName`, 
	`guests`.`memory`,
	`guests`.`vCPU`,
	`guests`.`inboundBandwidth`,
	`guests`.`outboundBandwidth`,
	`guests`.`status`,
	`guests`.`activity`,
	`templates`.`templateID`
	FROM `templates` INNER JOIN `guests` ON `templates`.`templateID`=`guests`.`templateID`
	WHERE `guests`.`guestID`=%s
	"""%(sourceGuestID))
	tmpData=cursor.fetchone()
	if tmpData==None:
		return 'sourceGuestID not found'
	if tmpData[8]!=0 or tmpData[9]!=0:
		return 'source guest is busy'
	
	key=detail.keys()
	
	if 'memory' in key:
		memory=detail['memory']
	else:
		memory=tmpData[4]
	
	if 'vCPU' in key:
		vCPU=detail['vCPU']
	else:
		vCPU=tmpData[5]

	if 'inbound' in key:
		inbound=detail['inbound']
	else:
		inbound=tmpData[6]

	if 'outbound' in key:
		outbound=detail['outbound']
	else:
		outbound=tmpData[7]

	imageSize=int(tmpData[0])	#unit is byte
	#find storageHolder
	cursor.execute("SELECT `hostID`, `IPAddress` FROM `hosts` WHERE `isStorageHolder`=1")
	storageHolder=cursor.fetchone()
	
	#check storage
	storageInfo=connection.socketCall('localhost',setting.MONITOR_PORT,'get_current_storage_info', [str(storageHolder[1])])
	if json.loads(storageInfo)==[]:
		return "Data is not ready, please try again later."
	freeSpace=int(json.loads(storageInfo)[0]['storage_info']['free'])	#unit is Kbyte
	if imageSize>freeSpace*1024:
		return "Do not have enough space for duplicate this image"
	
	#random mac address until not exist in hosts and guests
	cursor.execute('''
	SELECT `MACAddress` FROM `hosts` 
	UNION 
	SELECT `MACAddress` FROM `guests`''')
	usedMAC=cursor.fetchall()
	while True:
		newMAC=network.randomMAC()
		if (newMAC,) in usedMAC:
			continue
		else:
			break

	#find rest ip from {guest_ip_pool}-{guests}
	cursor.execute('''
	SELECT `guest_ip_pool`.`IPAddress` FROM 
		`guest_ip_pool` LEFT JOIN `guests` ON `guest_ip_pool`.`IPAddress`=`guests`.`IPAddress`
	WHERE `guests`.`IPAddress` IS NULL
	''')
	freeIP=cursor.fetchall()
	if len(freeIP)==0:
		return "Out of IP address"
	else:
		#select the minimum from freeIP
		newIP=freeIP[0][0]
		for eachIP in freeIP:
			if network.IPAddr(eachIP[0]).getProduct()<network.IPAddr(newIP).getProduct():
				newIP=eachIP[0]

	#find image file name
	usedImageNames=os.listdir(setting.TARGET_IMAGE_PATH)
	volumeFileName=guestName+'.img'
	count=2
	while volumeFileName in usedImageNames :
		volumeFileName=guestName+'('+str(count)+').img'
		count+=1
			
	if inbound==None or inbound=='-':
		inboundString="NULL"
	else:
		inboundString="'%s'"%(str(inbound))

	if outbound==None or outbound=='-':
		outboundString="NULL"
	else:
		outboundString="'%s'"%(str(outbound))
	cursor.execute('''
	INSERT INTO `guests` (`guestName`, `MACAddress`, `IPAddress`, `volumeFileName`, `templateID`, `activity`,`memory`,`vCPU`,`inboundBandwidth`,`outboundBandwidth`) VALUES
	('%(guestName)s', '%(MACAddress)s', '%(IPAddress)s', '%(volumeFileName)s', '%(templateID)s', '%(activity)s', '%(memory)s', '%(vCPU)s', %(inboundBandwidth)s, %(outboundBandwidth)s);
	'''%{
	'guestName':guestName,
	'MACAddress':newMAC,
	'IPAddress':newIP,
	'volumeFileName':volumeFileName,
	'templateID':tmpData[10],
	'activity':1,		#cloning
	'memory':memory,
	'vCPU':vCPU,
	'inboundBandwidth':inboundString,
	'outboundBandwidth':outboundString
	})
	#find the guestID of new image
	#cursor.execute('''SELECT `guestID` FROM `guests` WHERE `MACAddress`='%s';'''%(newMAC))
	#guestID=cursor.fetchone()[0]
	#I have eiser way to find ID
	guestID=cursor.lastrowid
	
	#lock new guest
	cursor.execute("INSERT IGNORE INTO `lockedGuests` (`taskID`,`guestID`) VALUES (%s,%s)"%(str(taskID),str(guestID)))

	#add activity duplicating
	cursor.execute("UPDATE `guests` SET `activity`=6 WHERE `guestID`=%s"%(sourceGuestID))

	result=connection.socketCall(str(storageHolder[1]),setting.LOCAL_PORT,'guest_duplicate',[str(tmpData[3]),volumeFileName,str(guestID),setting.IMAGE_PATH,str(taskID)])
	
	cursor.execute("UPDATE `guests` SET `activity`=0 WHERE `guestID`=%s"%(sourceGuestID))

	db.close()
	
	if result!='OK':
		return result
	
	#set dhcp about new guest
	dhcpController.bind([(newMAC,newIP,guestName)])

	content='<guest guestID="%s" />'%(str(guestID))
	
	if not shortcut.storeFinishMessage(taskID,content):
		return "cannot storeFinishMessage"

	return "OK"

def guest_start(taskID,detail):
	#get parameter
	guestID=detail['guestID']

	key=detail.keys()
	if 'targetHostID' in key:
		targetHostID=detail['targetHostID']
	else:
		targetHostID=None

	#start work
	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	
	#find hostIPAddress, UUID
	cursor.execute('''SELECT `hosts`.`IPAddress` , `lastUUID`
	FROM `hosts` INNER JOIN `guests` 
	ON `hosts`.`hostID`=`guests`.`lastHostID` 
	AND `guests`.`status`=1 AND `guests`.`activity`=0
	AND `guests`.`guestID`=%s;'''%(guestID))
	lastData = cursor.fetchone()

	if lastData!=None:
		hostIP=lastData[0]
		UUID = lastData[1]
		if hostIP!=None and UUID!=None:
			guestStatus=connection.socketCall(hostIP,setting.LOCAL_PORT,'guest_update_status',[UUID,str(guestID)])
			try:
				guestStatus=json.loads(guestStatus)
				if guestStatus['status']==0:
					pass
				elif guestStatus['status']==1:
					return 'This guest was already started'
				else:
					return str(guestStatus)
			except:
				return str(guestStatus)
	
	#check save status (should not start)
	cursor.execute("SELECT `status` FROM `guests` WHERE `guestID`=%s"%(guestID))
	if cursor.fetchone()[0]==2:
		return 'This guest is saved, use restore instead'

	if targetHostID==None:
		cursor.execute("SELECT `hostID`,`IPAddress` FROM `hosts` WHERE `status`=1 AND `activity`=0 AND `isHost`=1")
		candidates=cursor.fetchall()
		if len(candidates)==0:
			return 'Every host is busy!!!'
		
		tmpHostList=[]
		for element in candidates:
			tmpHostList.append(element[0])
		
		targetHostID=planTool.greedySelect(tmpHostList)
			
		for element in candidates:
			if element[0]==targetHostID:
				targetHostIP=element[1]
				break

		#lock targetHost
		cursor.execute("INSERT IGNORE INTO `lockedHosts` (`taskID`,`hostID`) VALUES (%s,%s)"%(str(taskID),str(targetHostID)))
	
	else:
		#check that targetHostID is exist and get IP
		cursor.execute("SELECT `hostID`,`IPAddress` FROM `hosts` WHERE `hostID`=%s AND `status`=1 AND `activity`=0 AND `isHost`=1"%(str(targetHostID)))
		temp=cursor.fetchone()
		if temp==None:
			return 'Host not found, or this host is busy, or this host property isHost=0'
		targetHostIP=temp[1]
	
	UUID=connection.socketCall(targetHostIP,setting.LOCAL_PORT,'guest_start',[str(guestID),str(targetHostID)]) #update data in this method
	
	if not general.isUUID(UUID):
		return UUID

	db.close()
	content="<hostID>%s</hostID>\n<UUID>%s</UUID>\n"%(str(targetHostID),UUID)

	if not shortcut.storeFinishMessage(taskID,content):
		return "cannot storeFinishMessage"

	return "OK"

def guest_suspend(taskID,detail):
	#get parameter
	guestID=detail['guestID']

	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	#find hostIPAddress, UUID
	cursor.execute('''SELECT `hosts`.`IPAddress` , `lastUUID` 
	FROM `hosts` INNER JOIN `guests` 
	ON `hosts`.`hostID`=`guests`.`lastHostID` 
	AND `guests`.`status`=1 AND `guests`.`activity`=0
	AND `guests`.`guestID`=%s;'''%(guestID))
	targetData = cursor.fetchone()
	db.close()

	if targetData==None:
		return 'Invalid guestID or cannot suspend in this status'
	
	hostIP=targetData[0]
	UUID = targetData[1]

	runningState=connection.socketCall(hostIP,setting.LOCAL_PORT,'guest_pause',[UUID])

	try:
		if not(int(runningState) in range(7)):
			return 'Something go wrong!!!'
	except:
		return str(runningState)

	content="<runningState>%s</runningState>\n"%(str(runningState))
	
	if not shortcut.storeFinishMessage(taskID,content):
		return "cannot storeFinishMessage"

	return "OK"


def guest_resume(taskID,detail):
	#get parameter
	guestID=detail['guestID']

	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	#find hostIPAddress, UUID
	cursor.execute('''SELECT `hosts`.`IPAddress` , `lastUUID` 
	FROM `hosts` INNER JOIN `guests` 
	ON `hosts`.`hostID`=`guests`.`lastHostID` 
	AND `guests`.`status`=1 AND `guests`.`activity`=0
	AND `guests`.`guestID`=%s;'''%(guestID))
	targetData = cursor.fetchone()
	db.close()

	if targetData==None:
		return 'Invalid guestID or cannot resume in this status'
	
	hostIP=targetData[0]
	UUID = targetData[1]

	runningState=connection.socketCall(hostIP,setting.LOCAL_PORT,'guest_resume',[UUID])

	try:
		if not(int(runningState) in range(7)):
			return 'Something go wrong!!!'
	except:
		return str(runningState)

	content="<runningState>%s</runningState>\n"%(str(runningState))
	
	if not shortcut.storeFinishMessage(taskID,content):
		return "cannot storeFinishMessage"

	return "OK"


def guest_save(taskID,detail):
	#get parameter
	guestID=detail['guestID']

	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	#find hostIPAddress, UUID
	cursor.execute('''SELECT `hosts`.`IPAddress` , `lastUUID`, `volumeFileName`
	FROM `hosts` INNER JOIN `guests` 
	ON `hosts`.`hostID`=`guests`.`lastHostID` 
	AND `guests`.`status`=1 AND `guests`.`activity`=0
	AND `guests`.`guestID`=%s;'''%(guestID))
	targetData = cursor.fetchone()
	db.close()

	if targetData==None:
		return 'Invalid guestID or cannot save in this status'
	
	hostIP=targetData[0]
	UUID = targetData[1]
	volumeFileName = targetData[2]

	result=connection.socketCall(hostIP,setting.LOCAL_PORT,'guest_save',[UUID,volumeFileName,str(guestID)])

	if result!='OK':
		return result
	
	content='<guest guestID="%s" />\n'%(str(guestID))

	if not shortcut.storeFinishMessage(taskID,content):
		return "cannot storeFinishMessage"

	return "OK"

def guest_restore(taskID,detail):	
	#can restore guest at other host
	#get parameter
	guestID=detail['guestID']
	
	key=detail.keys()
	if 'targetHostID' in key:
		targetHostID=detail['targetHostID']
	else:
		targetHostID=None
	
	#start work
	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()

	#find volumeFileName
	cursor.execute("SELECT `volumeFileName` FROM `guests` WHERE `status`=2 AND `activity`=0 AND `guestID`=%s;"%(guestID))
	targetData = cursor.fetchone()

	if targetData==None:
		return 'Invalid guestID or cannot restore in this status'

	volumeFileName = targetData[0]
	
	if targetHostID==None:		#randomly choose target host
		cursor.execute("SELECT `hostID`,`IPAddress` FROM `hosts` WHERE `status`=1 AND `activity`=0 AND `isHost`=1")
		allActiveHosts=cursor.fetchall()
		
		if len(allActiveHosts)==0:
			return 'Every host is busy!!!'
		
		tmpHostList=[]
		for element in allActiveHosts:
			tmpHostList.append(element[0])
		
		targetHostID=planTool.weightRandom(tmpHostList)
			
		for element in allActiveHosts:
			if element[0]==targetHostID:
				hostIP=element[1]
				break

	else:
		#check targetHostID is alive or not (from database)
		cursor.execute("SELECT `hostID`,`IPAddress` FROM `hosts` WHERE `status`=1 AND `activity`=0 AND `isHost`=1 AND `hostID`=%s"%(str(targetHostID)))
		selectedRow=cursor.fetchone()
		if selectedRow==None:
			return 'your selected host are busy or not found or isHost=0'
		else:
			hostIP=selectedRow[1]
			targetHostID=selectedRow[0]

	#lock targetHost
	cursor.execute("INSERT IGNORE INTO `lockedHosts` (`taskID`,`hostID`) VALUES (%s,%s)"%(str(taskID),str(targetHostID)))
	db.close()

	result=connection.socketCall(hostIP,setting.LOCAL_PORT,'guest_restore',[str(guestID),volumeFileName,str(targetHostID)])

	if result!='OK':
		return result
	
	content='<hostID>%s</hostID>'%(str(targetHostID))
	
	if not shortcut.storeFinishMessage(taskID,content):
		return "cannot storeFinishMessage"

	return "OK"

def guest_shutoff(taskID,detail):
	#get parameter
	guestID=detail['guestID']

	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	#find hostIPAddress, UUID
	cursor.execute('''SELECT `hosts`.`IPAddress` , `lastUUID`
	FROM `hosts` INNER JOIN `guests` 
	ON `hosts`.`hostID`=`guests`.`lastHostID` 
	AND `guests`.`status`=1 AND `guests`.`activity`=0
	AND `guests`.`guestID`=%s;'''%(guestID))
	targetData = cursor.fetchone()
	db.close()

	if targetData==None:
		return 'Invalid guestID or cannot force-off in this status'
	
	hostIP=targetData[0]
	UUID = targetData[1]

	result=connection.socketCall(hostIP,setting.LOCAL_PORT,'guest_force_off',[str(guestID),UUID])

	if result!='OK':
		return result

	content=""
	
	if not shortcut.storeFinishMessage(taskID,content):
		return "cannot storeFinishMessage"

	return "OK"

def guest_destroy(taskID,detail):
	#get parameter
	guestID=detail['guestID']

	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	
	#find status of this guest (many cases)
	cursor.execute('''SELECT `status`, `MACAddress`, `IPAddress`, `volumeFileName`, `lastHostID`, `lastUUID`
	FROM `guests` WHERE `guestID`=%s AND `activity`=0;'''%(guestID))
	guestData = cursor.fetchone()
	if guestData==None:
		return 'Invalid guestID'
	guestStatus=guestData[0]
	guestMAC=guestData[1]
	guestIP=guestData[2]
	volumeFileName=guestData[3]
	hostID=guestData[4]
	UUID=guestData[5]

	if guestStatus==0:
		#shut off status
		pass
	
	elif guestStatus==1:
		#running status
		#find hostIPAddress
		cursor.execute('''SELECT `IPAddress` FROM `hosts` WHERE `hostID`=%s;'''%(str(hostID)))
		hostData = cursor.fetchone()
	
		if hostData==None:
			return 'Cannot find target host, bug bug bug'
		
		hostIP=hostData[0]

		newGuestStatus=connection.socketCall(hostIP,setting.LOCAL_PORT,'guest_update_status',[UUID,str(guestID)])
		try:
			newGuestStatus=json.loads(newGuestStatus)
		except:
			return str(newGuestStatus)

		if newGuestStatus['status']==1:
			result=connection.socketCall(hostIP,setting.LOCAL_PORT,'guest_destroy',[UUID])

			if result!='OK':
				return result

		elif newGuestStatus['status']==0:
			pass	#do nothing like when status==0

	elif guestStatus==2:
		#saved status
		saveFileName = volumeFileName.split('.')
		saveFileName[-1]='sav'
		saveFileName = '.'.join(saveFileName)

		os.remove(setting.TARGET_IMAGE_PATH+saveFileName)
	
	unbindResult=dhcpController.unbind([(str(guestMAC),str(guestIP))])
	if unbindResult==False:
		return 'DHCP unbinding error'
	os.remove(setting.TARGET_IMAGE_PATH+volumeFileName)
	cursor.execute('''DELETE FROM `guests` WHERE `guestID`=%s'''%(guestID))
	db.close()

	content=""

	if not shortcut.storeFinishMessage(taskID,content):
		return "cannot storeFinishMessage"

	return "OK"

def guest_migrate(taskID,detail):
	#get parameter
	guestID=detail['guestID']
	targetHostID=detail['targetHostID']

	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	#find hostIPAddress, UUID
	cursor.execute('''SELECT `hosts`.`IPAddress` , `lastUUID`
	FROM `hosts` INNER JOIN `guests` 
	ON `hosts`.`hostID`=`guests`.`lastHostID` 
	AND `guests`.`status`=1 AND `guests`.`activity`=0
	AND `guests`.`guestID`=%s;'''%(guestID))
	targetData = cursor.fetchone()
	
	if targetData==None:
		return 'Invalid guestID or cannot migrate in this status'
	
	currentHostIP=targetData[0]
	currentUUID = targetData[1]
	
	#find targetHostIP *** do not push isHost to condition *** (let it be in guest migration only)
	cursor.execute('''SELECT `IPAddress` FROM `hosts` WHERE `status`=1 AND `activity`=0 AND `hostID`=%s'''%(targetHostID))
	targetData=cursor.fetchone()
	if targetData==None:
		return 'Invalid targetHostID or targetHost is not running'
	
	targetHostIP=targetData[0]

	db.close()

	result=connection.socketCall(currentHostIP,setting.LOCAL_PORT,'guest_migrate',[str(guestID),currentUUID,currentHostIP,targetHostIP,targetHostID])

	if result!='OK':
		return result
	
	content='<guest guestID="%s" />\n'%(str(guestID))

	if not shortcut.storeFinishMessage(taskID,content):
		return "cannot storeFinishMessage"

	return "OK"

def guest_scale_cpu(taskID,detail):
	#get parameter
	guestID=detail['guestID']
	vCPU=detail['vCPU']

	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	
	#update vCPU to database
	try:
		cursor.execute("UPDATE `guests` SET `vCPU`=%s WHERE `guestID`=%s"%(int(vCPU),guestID))
	except:
		db.close()
		return 'guestID not found or vCPU is invalid'

	#find hostIPAddress, UUID
	cursor.execute('''SELECT `hosts`.`IPAddress` , `lastUUID`
	FROM `hosts` INNER JOIN `guests` 
	ON `hosts`.`hostID`=`guests`.`lastHostID` 
	AND `guests`.`status`=1 AND `guests`.`activity`=0
	AND `guests`.`guestID`=%s;'''%(guestID))
	targetData = cursor.fetchone()
	db.close()

	if targetData==None:
		#this is the case when status of that host is 0(shutoff) or 2(saved)
		shortcut.storeFinishMessage(taskID,"This vCPU will not scale until you reboot your guest.")
		return 'OK'
	
	hostIP=targetData[0]
	UUID = targetData[1]

	result=connection.socketCall(hostIP,setting.LOCAL_PORT,'guest_scale_cpu',[UUID,vCPU])

	if result!='OK':
		shortcut.storeFinishMessage(taskID,"This vCPU will not scale until you reboot your guest.")
		return 'OK'		#i intend to do this (not a bug)

	content=""
	
	if not shortcut.storeFinishMessage(taskID,content):
		return "cannot storeFinishMessage"

	return "OK"

def guest_scale_memory(taskID,detail):
	#get parameter
	guestID=detail['guestID']
	memory=detail['memory']

	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	
	#update vCPU to database
	try:
		cursor.execute("UPDATE `guests` SET `memory`=%s WHERE `guestID`=%s"%(int(memory),guestID))
	except:
		db.close()
		return 'guestID not found or memory parameter is invalid'

	#find hostIPAddress, UUID
	cursor.execute('''SELECT `hosts`.`IPAddress` , `lastUUID`
	FROM `hosts` INNER JOIN `guests` 
	ON `hosts`.`hostID`=`guests`.`lastHostID` 
	AND `guests`.`status`=1 AND `guests`.`activity`=0
	AND `guests`.`guestID`=%s;'''%(guestID))
	targetData = cursor.fetchone()
	db.close()

	if targetData==None:
		#this is the case when status of that host is 0(shutoff) or 2(saved)
		shortcut.storeFinishMessage(taskID,"This vCPU will not scale until you reboot your guest.")
		return 'OK'
	
	hostIP=targetData[0]
	UUID = targetData[1]

	result=connection.socketCall(hostIP,setting.LOCAL_PORT,'guest_scale_memory',[UUID,memory])

	if result!='OK':
		shortcut.storeFinishMessage(taskID,"This memory will not scale until you reboot your guest.")
		return 'OK'		#i intend to do this (not a bug)

	content=""
	
	if not shortcut.storeFinishMessage(taskID,content):
		return "cannot storeFinishMessage"

	return "OK"
