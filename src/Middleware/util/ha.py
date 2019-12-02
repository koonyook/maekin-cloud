'''
high availability module
'''
import MySQLdb
import json

import setting
import connection,cacheFile


def recover():
	'''
	check and repair all hosts and guests of this cloud
	
	needed environment:
		database is up
		updated cacheFile
		global_lock is locked
		no working task
	'''

	#check hosts
	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	
	cursor.execute("SELECT `hostID`, `IPAddress`, `status` FROM `hosts`")
	hostData=cursor.fetchall()
	
	hostIPtoID={}	#use at the end
	for element in hostData:
		hostIPtoID[element[1]]=element[0]

	activeHost=[]

	for element in hostData:
		result=connection.socketCall(element[1],setting.LOCAL_PORT,'hello')
		if result=='OK':
			#this is active host
			activeHost.append(activeHost)
			if element[2]!=1:
				cursor.execute("UPDATE `hosts` SET `status`=1 WHERE `hostID`=%s"%(str(element[0])))
		else:
			#inactive host
			if element[2]==1:
				cursor.execute("UPDATE `hosts` SET `status`=0 WHERE `hostID`=%s"%(str(element[0])))
	
	#change activity of all host
	cursor.execute("UPDATE `hosts` SET `activity`=0")
	
	#######################################################

	#repair guest activity (the guest with cloning activity must be destroy)
	cursor.execute("SELECT `guestID`,`MACAddress`,`IPAddress`,`volumeFileName` FROM `guests` WHERE `activity`=1")
	tmpData=cursor.fetchall()
	for element in tmpData:
		reply=connection.socketCall(element[1],setting.LOCAL_PORT,'dhcp_unbind_host',[element[1],element[2],'{socket_connection}'])
		if reply!='OK':
			print 'DHCP unbinding error, but do not care.'
		os.remove(setting.TARGET_IMAGE_PATH+element[3])
		cursor.execute("DELETE FROM `guests` WHERE `guestID`=%s"%(element[0]))
	
	cursor.execute("UPDATE `guests` SET `activity`=0")

	#######################################################
	rawGuestData=[]
	for element in activeHost:
		result=connection.socketCall(element[1],setting.LOCAL_PORT,'get_local_raw_guest_data')
		rawGuestData+=json.loads(result)
	
	#remove the outer guest (is not in this system)
	cursor.execute("SELECT `MACAddress` FROM `guests`")
	tmpData=cursor.fetchall()
	allMAC=[]
	for element in tmpData:
		allMAC.append(element[0])
	
	outerGuest=[]
	for element in rawGuestData:
		if element['MACAddress'] not in allMAC:
			outerGuest.append(element)
	
	for element in outerGuest:
		rawGuestData.remove(element)
	#######################################################
	
	#close abnormal guests
	abnormal=[]
	for element in rawGuestData:
		if (element['isActive']!=1) or (element['runningState']!=1 and element['runningState']!=3):
			abnormal.append(element)
	
	for element in abnormal:
		#update status,lastHost,lastUUID to database in this socketCall
		connection.socketCall(element['hostIP'],setting.LOCAL_PORT,'guest_force_off',[element['MACAddress'],element['UUID'],'macMode'])
		rawGuestData.remove(element)
	
	######################################################

	#close replicated guests
	realActiveGuest={}
	for element in rawGuestData:
		if element['MACAddress'] not in realActiveGuest.keys():
			realActiveGuest[element['MACAddress']]=element
		else:
			#this is replicated guest must be force off
			connection.socketCall(element['hostIP'],setting.LOCAL_PORT,'guest_force_off',[element['MACAddress'],element['UUID'],'macMode'])
	
	#update database from realActiveGuest
	for key in realActiveGuest.keys():
		cursor.execute("UPDATE `guests` SET `status`=1, `lastHostID`=%s, `lastUUID`='%s' WHERE `MACAddress`='%s'"%(str(hostIPtoID[element['hostIP']]),element['UUID'],key))
	
	return True   #finish recover
