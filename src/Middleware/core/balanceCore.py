import setting

from util import connection,general,cacheFile,network
from util import shortcut
from scheduling import mission
from planning import planTool

import time
import MySQLdb
import json

def guest_balance_mission(taskID,detail):
	'''
	calculate and push guest migrations as subtasks
	'''
	detailList=[]

	#find blank active host to be volunteer
	usageData=planTool.getWeightData(None,setting.GUEST_BALANCE_TIME)

	volunteers=[]
	needHelps=[]
	for element in usageData:
		if element['percentRest']>setting.VOLUNTEER_THRESHOLD and element['fake']==False:
			#this host is volunteer
			element['canGive']=element['percentRest']-setting.NEED_HELP_THRESHOLD
			volunteers.append(element)
		elif element['percentRest']<setting.NEED_HELP_THRESHOLD and element['fake']==False:
			#this host need help
			element['need']=setting.NEED_HELP_THRESHOLD-element['percentRest']
			needHelps.append(element)
	
	if len(volunteers)==0 or len(needHelps)==0:
		#no need to do in this mission
		shortcut.storeFinishMessage(taskID,"no volunteer or no need of help")
	else:
		#calculate all active guest % usage
		guestData=planTool.getGuestLoadData()
		
		for host in needHelps:
			host['guestList']=[]
			for guest in guestData:
				if host['hostID']==guest['lastHostID']:
					host['guestList'].append(guest)
			
			host['guestList'].sort(key= lambda x: x['percentLoad'],reverse=True)

		#sort volunteers from max help to min help
		volunteers.sort(key=lambda x: x['percentRest'],reverse=True)

		for volunteer in volunteers:
			needHelps.sort(key=lambda x: x['need'],reverse=True)
			for needHelp in needHelps:
				while needHelp['need']>=0:
					selectedGuest=None
					for guest in needHelp['guestList']:
						if guest['percentLoad']<=volunteer['canGive']:
							selectedGuest=guest
							break
					if selectedGuest==None:
						break
					detailList.append({'command':'guest_migrate','guestID':str(selectedGuest['guestID']),'targetHostID':str(volunteer['hostID'])})
					volunteer['canGive']-=selectedGuest['percentLoad']
					needHelp['need']-=selectedGuest['percentLoad']
					needHelp['guestList'].remove(selectedGuest)

	success=mission.addSubTasks(taskID,detailList)
	if success:
		return 'OK'
	else:
		return "addSubtasks fail"
"""
def guest_balance_mission_ending(taskID):
	finishMessage="guest_balance_mission success"
	print shortcut.storeFinishMessage(taskID,finishMessage)
	print "guest_balance_mission success"

	return "OK"
"""
def host_balance_mission(taskID,detail):
	'''
	calculate and decide what host should be open or close
	'''
	detailList=[]

	usageData=planTool.getWeightData(None,setting.HOST_BALANCE_TIME)
	totalResource=0.0
	restResource=0.0
	
	needVolume=0.0
	giveVolume=0.0

	for element in usageData:	#every host must provide real data (no fake)
		
		if element['fake']:
			success=mission.addSubTasks(taskID,[])
			if success:
				return 'OK'
			else:
				return 'add sub task fail'

		totalResource+=element['resourceFull']
		restResource+=element['resourceRest']

		if element['percentRest']<setting.NEED_HELP_THRESHOLD:
			needVolume+=setting.NEED_HELP_THRESHOLD-element['percentRest']
		elif element['percentRest']>setting.VOLUNTEER_THRESHOLD:
			giveVolume+=element['percentRest']-setting.VOLUNTEER_THRESHOLD
	
	concludeUsage=1.0-(restResource/totalResource)
	shortcut.storeFinishMessage(taskID,"concludeUsage:"+str(concludeUsage))

	if concludeUsage>setting.OPEN_HOST_THRESHOLD or needVolume>giveVolume:
		#select a host to open
		infoHost=cacheFile.getDatabaseIP()
		db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
		cursor = db.cursor()
		cursor.execute("SELECT `hostID` FROM `hosts` WHERE `status`=0 OR `status`=2")
		selectedHost=cursor.fetchone()
		
		if selectedHost!=None:
			selectedHostID=selectedHost[0]
			detailList.append({'command':'host_wakeup', 'hostID':str(selectedHostID)})
			cursor.execute("INSERT IGNORE INTO `lockedHosts` (`taskID`,`hostID`) VALUES (%s,%s)"%(taskID,selectedHostID))
		
		db.close()

	elif concludeUsage<setting.CLOSE_HOST_THRESHOLD:
		#select an active host to close
		infoHost=cacheFile.getDatabaseIP()
		db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
		cursor = db.cursor()
		cursor.execute("SELECT `hostID` FROM `hosts` WHERE `isStorageHolder`=1")
		nfsHostID=cursor.fetchone()[0]
		
		targetHost=None
		for element in usageData:
			if element['hostID']==nfsHostID:
				continue
			if targetHost==None:
				targetHost=element
			elif element['resourceRest']>targetHost['resourceRest']:
				targetHost=element
		
		if targetHost!=None:
			targetHostID=targetHost['hostID']
			detailList.append({'command':'host_close', 'hostID':str(targetHostID), 'mode':'shutdown'})
			cursor.execute("INSERT IGNORE INTO `lockedHosts` (`taskID`,`hostID`) VALUES (%s,%s)"%(taskID,targetHostID))
		
		db.close()
	

	success=mission.addSubTasks(taskID,detailList)
	if success:
		return 'OK'
	else:
		return "addSubtasks fail"
"""
def host_balance_mission_ending(taskID):
	finishMessage="host_balance_mission success"
	print shortcut.storeFinishMessage(taskID,finishMessage)
	print "host_balance_mission success"

	return "OK"
"""