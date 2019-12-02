import libvirt
import os
import time
import multiprocessing
import sys
import random

import setting
from util import cacheFile,network,general
from util.general import getCurrentTime

import MySQLdb

def weightRandom(hostList,weightData=None):
	'''
	this method choose a host by weight random from load data setting.WEIGHT_RANDOM_TIME seconds ago
	hostList = list of active host id (caller must filter this list before)
	'''
	if len(hostList)==0:
		return None
	
	if len(hostList)==1:
		return hostList[0]
	
	if weightData==None:
		weightData=getWeightData(hostList)

	#next is weight & random
	totalRest=0.0
	for element in weightData:
		totalRest+=element['resourceRest']

	if totalRest==0.0:	#no choice to force randomOne
		return general.randomOne(weightData)['hostID']
	
	starter=totalRest*random.random()		#[0.0, 1.0)
	
	for element in weightData:
		starter-=element['resourceRest']
		if starter<=0:
			return element['hostID']
	
def greedySelect(hostList,weightData=None):
	'''
	this method choose a host by greedy algorithm from load data setting.WEIGHT_RANDOM_TIME seconds ago
	hostList = list of active host id (caller must filter this list before)
	'''
	if len(hostList)==0:
		return None
	
	if len(hostList)==1:
		return hostList[0]
	
	if weightData==None:
		weightData=getWeightData(hostList)

	#next is weight & random
	totalRest=0.0
	for element in weightData:
		totalRest+=element['resourceRest']

	if totalRest==0.0:	#no choice to force randomOne
		return general.randomOne(weightData)['hostID']

	selectedElement=weightData[0]
	for element in weightData:
		if element['resourceRest']>selectedElement['resourceRest']:
			selectedElement=element
	return selectedElement['hostID']

def getWeightData(hostList,timeRange=None):
	'''
	if hostList==None this method will replace hostList with all active hosts (with isHost=1)
	'''

	if timeRange==None:
		timeRange=setting.WEIGHT_RANDOM_TIME

	thresholdTimestamp=getCurrentTime()-timeRange

	db = MySQLdb.connect(cacheFile.getDatabaseIP(), setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	
	if hostList==None:
		#must find all active host
		cursor.execute("SELECT `hostID` FROM `hosts` WHERE `status`=1 AND `isHost`=1")
		hostList=[]
		while True:
			tmpHostID=cursor.fetchone()
			if tmpHostID==None:
				break
			else:
				hostList.append(tmpHostID[0])
	
	hostList=list(hostList)	#this line is very important, it's deep copy

	strHostList=[]
	for tmpHostID in hostList:
		strHostList.append(str(tmpHostID))

	cursor.execute('''
		SELECT `hostID`,`timestamp`,`idleTime`,`btime` FROM `hostLoad` WHERE `hostLoadID` IN
		(	SELECT MAX(`hostLoadID`)
			FROM `hostLoad` 
			GROUP BY `hostID`
			HAVING `hostID` IN (%s))'''%(','.join(strHostList)))
	maxData=cursor.fetchall()
	
	conclude=[]
	for element in maxData:
		
		cursor.execute("SELECT `cpuCore`,`cpuSpeed` FROM `hosts` WHERE `hostID`=%s"%(element[0]))
		hostSpec=cursor.fetchone()
		
		newDict={
			'hostID':element[0],
			'maxTimestamp':element[1],
			'maxIdleTime':element[2],
			'cpuCore':hostSpec[0],
			'cpuSpeed':hostSpec[1],
		}

		cursor.execute('''
			SELECT `timestamp`,`idleTime` FROM `hostLoad` WHERE `hostLoadID` IN
			(	SELECT MIN(`hostLoadID`)
				FROM `hostLoad` 
				WHERE `timestamp`>'%s' AND `btime`='%s'
				GROUP BY `hostID`
				HAVING `hostID`='%s')'''%(thresholdTimestamp,element[3],element[0]))
		minData=cursor.fetchone()
		
		if minData==None or minData[0]>=newDict['maxTimestamp']:
			#this host is newly open (should send fake data out)
			newDict['fake']=True

			newDict['minTimestamp']=None
			newDict['minIdleTime']=None

			newDict['percentRest']=0.0
			newDict['resourceRest']=0.0
			newDict['resourceFull']=newDict['cpuSpeed']*newDict['cpuCore']
		
		else:
			#real data
			newDict['fake']=False

			newDict['minTimestamp']=minData[0]
			newDict['minIdleTime']=minData[1]
			
			newDict['percentRest']=(newDict['maxIdleTime']-newDict['minIdleTime'])*100.0/((newDict['maxTimestamp']-newDict['minTimestamp'])*newDict['cpuCore'])
			newDict['resourceRest']=newDict['percentRest']*newDict['cpuSpeed']*newDict['cpuCore']/100.0
			newDict['resourceFull']=newDict['cpuSpeed']*newDict['cpuCore']
			
		conclude.append(newDict)
		hostList.remove(newDict['hostID'])		#because this line, hostList should do deep copy
	
	#fake the rest that have not any load data
	for hostID in hostList:	#rest from remove
		cursor.execute("SELECT `cpuCore`,`cpuSpeed` FROM `hosts` WHERE `hostID`=%s"%(hostID))
		hostSpec=cursor.fetchone()
		conclude.append({
			'hostID':hostID,
			'fake':True,
			'cpuCore':hostSpec[0],
			'cpuSpeed':hostSpec[1],
			'percentRest':0.0,
			'resourceRest':0.0,
			'resourceFull':hostSpec[0]*hostSpec[1],
		})
	db.close()
	
	print "@@@@@@@@@@@"
	print conclude

	return conclude

def getGuestLoadData(timeRange=None):
	'''
	for all active guest
	'''
	if timeRange==None:
		timeRange=setting.GUEST_BALANCE_TIME
	
	timeThreshold=getCurrentTime()-timeRange
	
	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	cursor.execute("SELECT `guests`.`guestID`,`guests`.`lastHostID`,`hosts`.`cpuCore`,`hosts`.`cpuSpeed` FROM `guests` INNER JOIN `hosts` ON `guests`.`lastHostID`=`hosts`.`hostID` WHERE `guests`.`status`=1")
	guestTmpData=cursor.fetchall()
	conclude=[]
	for element in guestTmpData:
		guestDict={
			'guestID':element[0],
			'lastHostID':element[1],
			'cpuCore':element[2],
			'cpuSpeed':element[3],
		}
		cursor.execute("SELECT `timestamp`,`cpuTime` FROM `guestLoad` WHERE `timestamp`>'%s' AND `guestID`=%s"%(timeThreshold,element[0]))
		guestDict['minTimestamp']=None
		guestDict['maxTimestamp']=None
		guestDict['minCpuTime']=None
		guestDict['maxCpuTime']=None
		while True:
			tmpData=cursor.fetchone()
			if tmpData==None:
				break
			if guestDict['minTimestamp']==None or tmpData[0]<guestDict['minTimestamp']:
				guestDict['minTimestamp']=tmpData[0]
				guestDict['minCpuTime']=tmpData[1]
			if guestDict['maxTimestamp']==None or tmpData[0]>guestDict['maxTimestamp']:
				guestDict['maxTimestamp']=tmpData[0]
				guestDict['maxCpuTime']=tmpData[1]
		
		if guestDict['minTimestamp']==guestDict['maxTimestamp'] or guestDict['minCpuTime']>guestDict['maxCpuTime']:
			#this is newly open guest (have not enough data to calculate)
			#this guest will not be add in return list
			continue
		
		#calculate % and real load
		guestDict['percentLoad']=(guestDict['maxCpuTime']-guestDict['minCpuTime'])*100.0/(guestDict['cpuCore']*(guestDict['maxTimestamp']-guestDict['minTimestamp']))
		guestDict['realLoad']=guestDict['percentLoad']*guestDict['cpuSpeed']*guestDict['cpuCore']

		conclude.append(guestDict)
	db.close()
	
	print "&&&&&&&&&&&&"
	print conclude

	return conclude
