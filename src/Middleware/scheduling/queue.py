from core import guestCore,hostCore,cloudCore,balanceCore,templateCore,testCore
from util import connection,cacheFile,network,general
import setting
import static

import MySQLdb
import json
import os
import traceback

def enqueue(detail):
	'''
	add new task to queue
	detail = a dictionary of {'command', 'each parameter'}
	return taskID if success
	return None if error
	'''
	try:
		form = static.commandToDetail[detail['command']]
	except:
		print 'Error: no command found'
		return None
	
	opcode = form['opcode']

	for parameter in form['param']:
		if parameter not in detail.keys():
			print 'Error: parameter not found -> '+parameter
			return None
	
	if form['isMission']:
		isMission = 1
	else:
		isMission = 0
	
	try:
		infoHost=cacheFile.getDatabaseIP()
		db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
		cursor = db.cursor()

		cursor.execute('''
			INSERT INTO `tasks` (`opcode`, `isMission`, `detail`, `createTimestamp`) VALUES
			( %(opcode)s, %(isMission)s, '%(detail)s', NOW());
			'''%{
			'opcode':str(opcode),
			'isMission':str(isMission),
			'detail':json.dumps(detail)
			})
		
		taskID=cursor.lastrowid
		db.close()
		
		connection.socketCall('localhost',setting.WORKER_PORT,'start_work',['{socket_connection}'])

		return taskID

	except:
		print 'have someting wrong with database'
		return None

def doNextWork(locker):
	'''
	***only worker can call this function directly***
	***if you isn't worker call this function via 
		connection.socketCall('localhost',setting.WORKER_PORT,'start_work',['{socket_connection}'])
	return True if it can do
	return False if it cannot
	'''
	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	
	#choose 
	
	cursor.execute('''
		SELECT `taskID`,`opcode`,`isMission`,`detail`,`parentTaskID` FROM `tasks` WHERE `status`=0 AND COALESCE(`parentTaskID`,0)=
			(SELECT MAX(`parentTaskID`) FROM
				(SELECT COALESCE(`parentTaskID`,0) as `parentTaskID` FROM `tasks` WHERE `status`=0 AND `createTimestamp`=
					(SELECT MIN(`createTimestamp`) FROM
						(SELECT `createTimestamp` FROM `tasks` WHERE `status`=0) inQueue
					) 
				) minCreateTimestamp
			)
			AND `createTimestamp`=
				(SELECT MIN(`createTimestamp`) FROM
					(SELECT `createTimestamp` FROM `tasks` WHERE `status`=0) inQueue
				)
	''')
	
	candidate=cursor.fetchall()
	if len(candidate)==0:
		#cursor.execute("UPDATE `cloud_variables` SET `value`='0' WHERE `key`='dequeuing'")
		locker.unlock()
		db.close()
		print "Task not found"
		return True
	else:
		if candidate[0][4]==None:
			nextTaskData=candidate[0]
			for element in candidate:
				if element[0]<nextTaskData[0]:
					nextTaskData=element
		else:
			nextTaskData=candidate[0]
			for element in candidate:
				if element[0]>nextTaskData[0]:
					nextTaskData=element		

	taskID,opcode,isMission,detail,parentTaskID=nextTaskData
	detail=json.loads(detail)

	if parentTaskID!=None:
		ancester=[str(parentTaskID)]
		currentTaskID=parentTaskID
		while True:
			cursor.execute("SELECT `parentTaskID` FROM `tasks` WHERE `taskID`=%s"%(currentTaskID))
			result=cursor.fetchone()
			if result==None:
				break
			if result[0]==None:
				break
			ancester.append(str(result[0]))
			currentTaskID=result[0]		
	else:
		ancester=[]
		
	ancesterCondition=""	
	if len(ancester)>0:
		ancesterCondition+="WHERE `taskID` NOT IN (%s)"%(','.join(ancester))

	lockData = analyseLockData(detail)
	#compare with database (locked table)
	conflict=False
	cursor.execute("SELECT `hostID` FROM `lockedHosts` "+ancesterCondition)
	while True:
		element = cursor.fetchone()
		if element==None:
			break
		if element[0] in lockData['hostID']:
			conflict=True
			break
		if element[0]==-1 and len(lockData['hostID'])>0:
			conflict=True
			break
		if -1 in lockData['hostID']:
			conflict=True
			break

	if not conflict:
		cursor.execute("SELECT `guestID` FROM `lockedGuests` "+ancesterCondition)
		while True:
			element = cursor.fetchone()
			if element==None:
				break
			if element[0] in lockData['guestID']:
				conflict=True
				break
			if element[0]==-1 and len(lockData['guestID'])>0:
				conflict=True
				break
			if -1 in lockData['guestID']:
				conflict=True
				break
	
	if conflict:
		#cursor.execute("UPDATE `cloud_variables` SET `value`='0' WHERE `key`='dequeuing'")
		locker.unlock()
		db.close()
		return False
	
	#this point can put this task in the working pool [1.lock 2.put in]
	
	insertLockHeader="INSERT INTO `lockedHosts` (`taskID`, `hostID`) VALUES "
	insertList=[]
	for hostID in lockData['hostID']:
		insertList.append("(%s, %s)"%(str(taskID),hostID))
	if len(lockData['hostID'])>0:
		cursor.execute(insertLockHeader+str(','.join(insertList)))

	insertLockHeader="INSERT INTO `lockedGuests` (`taskID`, `guestID`) VALUES "
	insertList=[]
	for guestID in lockData['guestID']:
		insertList.append("(%s, %s)"%(str(taskID),guestID))
	if len(lockData['guestID'])>0:
		cursor.execute(insertLockHeader+str(','.join(insertList)))

	#shift from inQueue to working	
	cursor.execute("UPDATE `tasks` SET `status`=1, `processID`=%s  WHERE `taskID`=%s"%(str(os.getpid()),str(taskID)))
	
	######################
	## do the real work ##
	######################
	operationError=False
	coreCommandDict=general.getCommandDict(guestCore,hostCore,cloudCore,balanceCore,templateCore,testCore)
	
	print "do task :",taskID,detail
	if isMission==0:
		#cursor.execute("UPDATE `cloud_variables` SET `value`='0' WHERE `key`='dequeuing'")
		locker.unlock()
		try:
			result=coreCommandDict[detail['command']](taskID,detail)	#this should be blocked method (some method lock more, every method fill finishMessage if success)
			# must check cacheFile again (database_migrate can change it)
			newInfoHost=cacheFile.getDatabaseIP()
			if newInfoHost!=infoHost:
				infoHost=newInfoHost
				db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
				cursor = db.cursor()
			
			if result=='OK':
				#update db to tell that your task has finish
				cursor.execute("UPDATE `tasks` SET `status`=2, `finishStatus`=1, `finishTimestamp`=NOW() WHERE `taskID`=%s"%(str(taskID)))
			else:
				#in case of error
				operationError=True
				cursor.execute("UPDATE `tasks` SET `status`=2, `finishStatus`=2, `finishMessage`='%s', `finishTimestamp`=NOW() WHERE `taskID`=%s"
					%(MySQLdb.escape_string(str(result)),str(taskID)))
				
		except:
			#update db to tell that your task has error
			operationError=True
			print "%sThis is handled error, already be logged in database.%s"%(static.RED_COLOR,static.END_COLOR)
			traceback.print_exc()
			print "%s----------------------%s"%(static.RED_COLOR,static.END_COLOR)
			cursor.execute("UPDATE `tasks` SET `status`=2, `finishStatus`=2, `finishMessage`=%s, `finishTimestamp`=NOW() WHERE `taskID`=%s",
				[MySQLdb.escape_string(traceback.format_exc()),str(taskID)])
		cursor.execute("DELETE FROM `lockedHosts` WHERE `taskID`=%s"%(str(taskID)))
		cursor.execute("DELETE FROM `lockedGuests` WHERE `taskID`=%s"%(str(taskID)))

	elif isMission==1:
		interceptQueueError=False
		try:
			result=coreCommandDict[detail['command']](taskID,detail)	#this should be blocked method (some method lock more, every method fill finishMessage if success)
			if result!='OK':
				#in case of error
				interceptQueueError=True
				cursor.execute("UPDATE `tasks` SET `status`=2, `finishStatus`=2, `finishMessage`='%s', `finishTimestamp`=NOW() WHERE `taskID`=%s"
					%(MySQLdb.escape_string(str(result)),str(taskID)))	
		except:
			interceptQueueError=True
			#update db to tell that your task has error
			print "%sThis is handled error, already be logged in database.%s"%(static.RED_COLOR,static.END_COLOR)
			traceback.print_exc()
			print "%s----------------------%s"%(static.RED_COLOR,static.END_COLOR)
			cursor.execute("UPDATE `tasks` SET `status`=2, `finishStatus`=2, `finishMessage`=%s, `finishTimestamp`=NOW() WHERE `taskID`=%s",
				[MySQLdb.escape_string(traceback.format_exc()),str(taskID)])
				
		if interceptQueueError:
			operationError=True
			cursor.execute("DELETE FROM `tasks` WHERE `parentTaskID`=%s"%(str(taskID)))
			cursor.execute("DELETE FROM `lockedHosts` WHERE `taskID`=%s"%(str(taskID)))
			cursor.execute("DELETE FROM `lockedGuests` WHERE `taskID`=%s"%(str(taskID)))
		
		#cursor.execute("UPDATE `cloud_variables` SET `value`='0' WHERE `key`='dequeuing'")
		locker.unlock()
	
	if operationError:
		propagateError(taskID)

	#check parent
	currentParentTaskID=parentTaskID
	while currentParentTaskID!=None and operationError==False:
		cursor.execute("SELECT `taskID` FROM `tasks` WHERE `finishStatus`<>1 AND `parentTaskID`=%s"%(str(currentParentTaskID)))
		if cursor.fetchone()==None:								#all of childTask finish and do not have error child
			#do something and update finishMessage before finish
			
			#acquire command name of currentParentTaskID
			cursor.execute("SELECT `detail` FROM `tasks` WHERE `taskID`=%s"%(str(currentParentTaskID)))
			currentParentTaskDetail=json.loads(cursor.fetchone()[0])
			currentParentTaskCommand=currentParentTaskDetail['command']
			if str(currentParentTaskCommand+'_ending') in coreCommandDict.keys():
				try:
					coreCommandDict[currentParentTaskCommand+'_ending'](currentParentTaskID)
				except:
					operationError=True
					print "%sThis is handled error, already be logged in database.%s"%(static.RED_COLOR,static.END_COLOR)
					traceback.print_exc()
					print "%s----------------------%s"%(static.RED_COLOR,static.END_COLOR)
					cursor.execute("UPDATE `tasks` SET `status`=2, `finishStatus`=2, `finishMessage`=%s, `finishTimestamp`=NOW() WHERE `taskID`=%s",
						[MySQLdb.escape_string(traceback.format_exc()),str(currentParentTaskID)])
			#do like finishing of primary work
			if operationError==False:
				cursor.execute("UPDATE `tasks` SET `status`=2, `finishStatus`=1, `finishTimestamp`=NOW() WHERE `taskID`=%s"%(str(currentParentTaskID)))
			
			cursor.execute("DELETE FROM `lockedHosts` WHERE `taskID`=%s"%(str(currentParentTaskID)))
			cursor.execute("DELETE FROM `lockedGuests` WHERE `taskID`=%s"%(str(currentParentTaskID)))
			
			if operationError:
				propagateError(currentParentTaskID)

			cursor.execute("SELECT `parentTaskID` FROM `tasks` WHERE `taskID`=%s"%(str(currentParentTaskID)))
			data=cursor.fetchone()
			if data[0]==None:
				break
			else:
				currentParentTaskID=data[0]
		else:
			break
	
	#get new ip address of global controller (maybe change during working)
	cursor.execute("SELECT `IPAddress` FROM `hosts` WHERE `isGlobalController`=1")
	newGlobalControllerIP=cursor.fetchone()[0]

	db.close()

	#socketCall to worker(now is mklocd) that something in queue has changed
	#print "I will sakid"
	connection.socketCall(newGlobalControllerIP,setting.WORKER_PORT,'start_work',['{socket_connection}'])
	#print "I will return"
	return True

def propagateError(taskID):
	'''
	propagate error from one task to every relative task (inqueue task & working mission)
	'''
	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	
	#start at top mission and go down to every child task
	currentTaskID=taskID
	while True:
		cursor.execute("SELECT `parentTaskID` FROM `tasks` WHERE `taskID`=%s"%(str(currentTaskID)))
		parentTaskID=cursor.fetchone()[0]
		if parentTaskID==None:
			break
		else:
			currentTaskID=parentTaskID
	
	#currentTaskID is the top task
	#print "TOP TASK", currentTaskID

	#collect all (already include currentTaskID) 
	taskList=getAllDescendantTasks(currentTaskID,cursor)
	
	#print "Descendant",taskList

	if len(taskList)>0:
		#choose inqueue task & working mission
		updateCondition=" WHERE (`status`=0 OR (`status`=1 AND `isMission`=1)) AND (`taskID` IN (%s))"%(','.join(taskList))
	
		cursor.execute("SELECT `taskID`, `isMission` FROM `tasks` %s"%updateCondition)
		selectedTask=cursor.fetchall()
		delList=[]
		coreCommandDict=general.getCommandDict(guestCore,hostCore,cloudCore,balanceCore,templateCore,testCore)
		for element in selectedTask:
			delList.append(str(element[0]))

			#clean database after error
			if element[1]==1:	#this element is working mission
				cursor.execute("SELECT `detail` FROM `tasks` WHERE `taskID`=%s"%(str(element[0])))
				currentTaskDetail=json.loads(cursor.fetchone()[0])
				currentTaskCommand=currentTaskDetail['command']
				if str(currentTaskCommand+'_error') in coreCommandDict.keys():
					try:
						coreCommandDict[currentTaskCommand+'_error'](currentTaskID)
					except:
						operationError=True
						print "%sThis is handled error, didn't be logged in database.%s"%(static.RED_COLOR,static.END_COLOR)
						traceback.print_exc()
						print "%s----------------------%s"%(static.RED_COLOR,static.END_COLOR)
		
		#get finish message of error cause
		cursor.execute("SELECT `finishMessage` FROM `tasks` WHERE `taskID`=%s"%(str(taskID)))
		errorMessage=cursor.fetchone()[0]
		cursor.execute("UPDATE `tasks` SET `status`=2, `finishStatus`=3, `finishMessage`='%s', `finishTimestamp`=NOW() %s"%("Cause of error is taskID="+str(taskID)+"\n"+errorMessage, updateCondition))
		
		if len(delList)>0:
			deleteCondition="WHERE `taskID` IN (%s)"%(','.join(delList))
			cursor.execute("DELETE FROM `lockedHosts` %s"%(deleteCondition))
			cursor.execute("DELETE FROM `lockedGuests` %s"%(deleteCondition))

	db.close()

def getAllDescendantTasks(taskID,cursor):
	'''
	return list of string of taskID (*** include taskID too ***)
	'''
	taskList=[]
	cursor.execute("SELECT `taskID` FROM `tasks` WHERE `parentTaskID`=%s"%(str(taskID)))
	tasks=cursor.fetchall()
	for element in tasks:
		taskList+=getAllDescendantTasks(element[0],cursor)
		#taskList.append(str(element[0])) #do not use +=
	taskList.append(str(taskID))

	return taskList

"""
def finishSpecialTask(taskID):
	'''
	must finish by mklocd (when migrate mkworker)
	'''
	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()

	#update db to tell that your task has finish
	cursor.execute("UPDATE `tasks` SET `status`=2, `finishStatus`=1, `finishTimestamp`=NOW() WHERE `taskID`=%s"%(str(taskID)))
				
	cursor.execute("DELETE FROM `lockedHosts` WHERE `taskID`=%s"%(str(taskID)))
	cursor.execute("DELETE FROM `lockedGuests` WHERE `taskID`=%s"%(str(taskID)))

	cursor.execute("SELECT `parentTaskID` FROM `tasks` WHERE `taskID`=%s"%(str(taskID)))
	parentTaskID=cursor.fetchone()[0]

	#check parent
	currentParentTaskID=parentTaskID
	while currentParentTaskID!=None:
		cursor.execute("SELECT `taskID` FROM `tasks` WHERE `status`=0 AND `parentTaskID`=%s"%(str(currentParentTaskID)))
		if cursor.fetchone()==None:								#all of childTask finish
			#do something and update finishMessage before finish
			if (detail['command']+'_ending') in coreCommandDict.keys():
				coreCommandDict[detail['command']+'_ending'](currentParentTaskID)
			#do like finishing of primary work
			cursor.execute("UPDATE `tasks` SET `status`=2, `finishStatus`=1, `finishTimestamp`=NOW() WHERE `taskID`=%s"%(str(currentParentTaskID)))
			cursor.execute("DELETE FROM `lockedHosts` WHERE `taskID`=%s"%(str(currentParentTaskID)))
			cursor.execute("DELETE FROM `lockedGuests` WHERE `taskID`=%s"%(str(currentParentTaskID)))
			
			cursor.execute("SELECT `parentTaskID` FROM `tasks` WHERE `taskID`=%s"%(str(currentParentTaskID)))
			data=cursor.fetchone()
			if data[0]==None:
				break
			else:
				currentParentTaskID=data[0]
		else:
			break

	#socketCall to worker that something in queue has changed
	print "I will sakid"
	cursor.execute("SELECT `IPAddress` FROM `host` WHERE `isGlobalController`=1")
	newGlobalControllerIP=cursor.fetchone()[0]
	db.close()
	connection.socketCall(newGlobalControllerIP,setting.WORKER_PORT,'start_work',['{socket_connection}'])
	print "I will return"
	return True
"""

def getNFSHostID():
	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	
	cursor.execute("SELECT `hostID` FROM `hosts` WHERE `isStorageHolder`=1")
	hostID=cursor.fetchone()[0]

	db.close()
	return hostID

def getGlobalControllerHostID():
	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	
	cursor.execute("SELECT `hostID` FROM `hosts` WHERE `isGlobalController`=1")
	hostID=cursor.fetchone()[0]

	db.close()
	return hostID

def analyseLockData(detail):
	'''
	think about which hosts or guests should be locked during working
	detail = {'command', parameters }
	return {'guestID':[1,2,3],'hostID':[1,4]}
	'''
	guestList=[]
	hostList=[]
		
	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	
	if detail['command']=='guest_create':	
		hostList.append(getNFSHostID())
		#/and new guestID will be locked when it have been created (during working)
	
	elif detail['command']=='guest_duplicate':	
		hostList.append(getNFSHostID())
		guestList.append(detail['sourceGuestID'])
		#/and new guestID will be locked when it have been created (during working)
	
	elif detail['command']=='template_create_from_guest':
		hostList.append(getNFSHostID())
		guestList.append(detail['sourceGuestID'])
	
	elif detail['command']=='template_remove':
		hostList.append(getNFSHostID())	 #to ensure that no clonning happen during remove template
		#cursor.execute("SELECT `guestID` FROM `guests` WHERE `templateID`=%s"%(str(detail['templateID'])))
		#guests=cursor.fetchall()
		#for element in guests:
		#	guestList.append(element[0])

	elif detail['command']=='guest_destroy':
		guestList.append(detail['guestID'])
		hostList.append(getNFSHostID())
		cursor.execute("SELECT `status`,`lastHostID` FROM `guests` WHERE `guestID`=%s"%(str(detail['guestID'])))
		tmp=cursor.fetchone()
		if tmp!=None:
			status,lastHostID=tmp
			if status==1:		#in case that guest is running(or pausing) on that host
				hostList.append(lastHostID)

	elif detail['command']=='guest_start':
		guestList.append(detail['guestID'])
		if 'targetHostID' in detail.keys():
			hostList.append(detail['targetHostID'])
		else:	#in case of randomly choosen targetHostID
			pass	#/this lock will be added when it start working  ***********************

	elif detail['command']=='guest_shutoff':
		guestList.append(detail['guestID'])
		cursor.execute("SELECT `lastHostID` FROM `guests` WHERE `guestID`=%s"%(str(detail['guestID'])))
		lastHostID=cursor.fetchone()
		if lastHostID!=None:
			hostList.append(lastHostID[0])
	
	elif detail['command']=='guest_save':
		guestList.append(detail['guestID'])
		hostList.append(getNFSHostID())
		cursor.execute("SELECT `lastHostID` FROM `guests` WHERE `guestID`=%s"%(str(detail['guestID'])))
		lastHostID=cursor.fetchone()
		if lastHostID!=None:
			hostList.append(lastHostID[0])

	elif detail['command']=='guest_restore':
		guestList.append(detail['guestID'])
		hostList.append(getNFSHostID())
		#target host should be added during working (you can restore guest at any host)

	elif detail['command']=='guest_suspend':
		guestList.append(detail['guestID'])
		cursor.execute("SELECT `lastHostID` FROM `guests` WHERE `guestID`=%s"%(str(detail['guestID'])))
		lastHostID=cursor.fetchone()
		if lastHostID!=None:
			hostList.append(lastHostID[0])
		
	elif detail['command']=='guest_resume':
		guestList.append(detail['guestID'])
		cursor.execute("SELECT `lastHostID` FROM `guests` WHERE `guestID`=%s"%(str(detail['guestID'])))
		lastHostID=cursor.fetchone()
		if lastHostID!=None:
			hostList.append(lastHostID[0])

	elif detail['command']=='guest_migrate':
		guestList.append(detail['guestID'])
		hostList.append(detail['targetHostID'])
		cursor.execute("SELECT `lastHostID` FROM `guests` WHERE `guestID`=%s"%(str(detail['guestID'])))
		lastHostID=cursor.fetchone()
		if lastHostID!=None:
			hostList.append(lastHostID[0])
		
	elif detail['command']=='guest_clone_as_template':		#skip
		guestList.append(detail['guestID'])
		hostList.append(getNFSHostID())

	elif detail['command']=='guest_scale_cpu':
		guestList.append(detail['guestID'])
		cursor.execute("SELECT `lastHostID` FROM `guests` WHERE `guestID`=%s"%(str(detail['guestID'])))
		lastHostID=cursor.fetchone()
		if lastHostID!=None:
			hostList.append(lastHostID[0])
	
	elif detail['command']=='guest_scale_memory':
		guestList.append(detail['guestID'])
		cursor.execute("SELECT `lastHostID` FROM `guests` WHERE `guestID`=%s"%(str(detail['guestID'])))
		lastHostID=cursor.fetchone()
		if lastHostID!=None:
			hostList.append(lastHostID[0])

	elif detail['command']=='host_add':		
		hostList.append(getNFSHostID())
		hostList.append(getGlobalControllerHostID())
		#the new hostID will be added too when it have been created (during working)

	elif detail['command']=='host_remove':	#mission
		hostList.append(getNFSHostID())
		hostList.append(getGlobalControllerHostID())
		hostList.append(detail['hostID'])
		#and all of active guest on this host
		cursor.execute("SELECT `guestID` FROM `guests` WHERE `status`=1 AND `lastHostID`=%s"%(str(detail['hostID'])))
		guests=cursor.fetchall()
		for element in guests:
			guestList.append(element[0])
		#targetHosts for guests and services migrating will be lock during the working phase (while adding subtask)
	
	elif detail['command']=='host_open':
		hostList.append(detail['hostID'])
		#and all of active guest on this host
		cursor.execute("SELECT `guestID` FROM `guests` WHERE `status`=1 AND `lastHostID`=%s"%(str(detail['hostID'])))
		guests=cursor.fetchall()
		for element in guests:
			guestList.append(element[0])
		#targetHosts for guests and services migrating will be lock during the working phase (while adding subtask)

	elif detail['command']=='host_close':
		hostList.append(detail['hostID'])
	
	elif detail['command']=='host_evacuate_mission':
		hostList.append(detail['hostID'])

	elif detail['command']=='global_migrate':
		hostList.append(detail['targetHostID'])
		cursor.execute("SELECT `hostID` FROM `hosts` WHERE `isGlobalController`=1")
		sourceHostID=cursor.fetchone()[0]
		hostList.append(sourceHostID)

	elif detail['command']=='global_promote':		#skip (used by ha only)
		pass

	elif detail['command']=='database_migrate':
		#lock all of the host
		cursor.execute("SELECT `hostID` FROM `hosts`")
		hosts=cursor.fetchall()
		for element in hosts:
			hostList.append(element[0])

	elif detail['command']=='database_make_slave':
		#lock all of the host
		cursor.execute("SELECT `hostID` FROM `hosts`")
		hosts=cursor.fetchall()
		for element in hosts:
			hostList.append(element[0])

	elif detail['command']=='database_promote':		#skip (used by ha only)
		pass 

	elif detail['command']=='ca_migrate':
		hostList.append(detail['targetHostID'])
		cursor.execute("SELECT `hostID` FROM `hosts` WHERE `isCA`=1")
		sourceHostID=cursor.fetchone()[0]
		hostList.append(sourceHostID)

	elif detail['command']=='ca_make_slave':
		hostList.append(detail['targetHostID'])
		cursor.execute("SELECT `hostID` FROM `hosts` WHERE `isCA`=1")
		sourceHostID=cursor.fetchone()[0]
		hostList.append(sourceHostID)

	elif detail['command']=='ca_promote':		#skip (used by ha only)
		pass
	
	elif detail['command']=='nfs_migrate':
		hostList.append(-1)			#all of host
		guestList.append(-1)		#all of guest

	else:
		pass #for general method that do not lock anything
		#print "Error, command not found:
		#return None
	
	####################
	### testing zone ###
	####################
	if detail['command']=='task_a':
		pass
		#hostList.append(1)
	elif detail['command']=='task_b':
		pass
		#hostList.append(1)
	
	#cut duplicate and filter out None value
	cleanGuestList=[]
	for aGuest in guestList:
		try:
			cleanGuestList.append(int(aGuest))
		except:
			continue
		
	cleanGuestList=list(set(cleanGuestList))

	cleanHostList=[]
	for aHost in hostList:
		try:
			cleanHostList.append(int(aHost))
		except:
			continue

	cleanHostList=list(set(cleanHostList))

	return {'guestID':cleanGuestList,'hostID':cleanHostList}
