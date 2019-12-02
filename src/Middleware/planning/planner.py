import libvirt
import os
import time
import multiprocessing
import sys
from xml.dom import minidom
import MySQLdb
import json
import traceback

import setting
from util import cacheFile,network
from util.general import getCurrentTime
from scheduling import queue

#planner shouldn't be restart after global controller move
#it can refresh data itself if any service move
#but it must be stop when this host was remove from cloud ***
def runCollector():
	jiffyPerSec=float(os.sysconf(os.sysconf_names['SC_CLK_TCK']))
	cpu_count=int(multiprocessing.cpu_count())
	
	myMAC=network.getMyMACAddr()
	myIP=network.getMyIPAddr()
	while myIP==None:
		time.sleep(1.5)
		myIP=network.getMyIPAddr()
		

	i_am_global_controller=False	#it will be changed during working
	hostID=None #will be know while working
	isHost=None #will be know while working

	timeCounter=-5	#start at 1 so everything will start slowly
	while True:
		
		#new system no need to check ip all the time
		#if timeCounter%setting.IP_CHECKING_PERIOD == 0:
		#	myIP=network.getMyIPAddr()
		#	if myIP==None:
		#		myIP=network.renewIPAddr(allowStatic=True)
			
		if timeCounter%setting.PLANNER_COLLECTING_PERIOD == 0:
			#get host data
			timestamp=getCurrentTime()	
			f=open('/proc/stat','r')
			while True:
				data=f.readline().split(' ')
				if data[0]=='cpu':
					if '' in data:
						data.remove('')
					idleTime=float(data[4])/jiffyPerSec
				elif data[0]=='btime':
					btime=int(data[1])
					break
			f.close()

			#get guest data (like mmond)
			guestError=False
			try:
				conn = libvirt.open(None)
				if conn==None:
					print "cannot connect to hypervisor"
					guestError=True

				else:
					domains = conn.listDomainsID()
					guestData=[]
					for id in domains:
						dom=conn.lookupByID(id)
						
						guestData.append({
						'UUID':dom.UUIDString().replace('-',''),
						'timestamp':getCurrentTime(),
						'cpuTime':float(dom.info()[4])/float(1000000000),
						})

			except:
				print "have error while getting guest load information"
				guestError=True

			try:
				db = MySQLdb.connect(cacheFile.getDatabaseIP(), setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
				cursor = db.cursor()
				if hostID==None:
					cursor.execute("SELECT `hostID`,`isHost` FROM `hosts` WHERE `MACAddress`='%s'"%(myMAC))
					hostID,isHost=cursor.fetchone()
				
				#put host data in database
				cursor.execute("INSERT INTO `hostLoad` (`hostID`,`timestamp`,`idleTime`,`btime`) VALUES ('%s','%s','%s','%s')"%(str(hostID),str(timestamp),str(idleTime),str(btime)))
				
				#put guest data in database
				haveActiveGuest=False
				if guestError==False:
					for element in guestData:
						cursor.execute("SELECT `guestID` FROM `guests` WHERE `lastUUID`='%s'"%(element['UUID']))
						result=cursor.fetchone()
						if result==None:
							continue
						else:
							guestID=result[0]
							cursor.execute("INSERT INTO `guestLoad` (`guestID`,`timestamp`,`cpuTime`) VALUES ('%s','%s','%s')"%(str(guestID),str(element['timestamp']),str(element['cpuTime'])))
							haveActiveGuest=True
				
				if haveActiveGuest and isHost==0:
					#should evacuate
					allowEvacuate=True
					cursor.execute("SELECT `detail` FROM `tasks` WHERE `opcode`=2005 AND `status`<>2")
					tmpDetail=cursor.fetchone()
					while tmpDetail!=None:
						detailDict=json.loads(tmpDetail[0])
						if str(detailDict['hostID'])==str(hostID):
							allowEvacuate=False
							break
						else:
							tmpDetail=cursor.fetchone()
					
					if allowEvacuate:
						taskID=queue.enqueue({
							'command':'host_evacuate_mission',	
							'hostID':hostID
						})
						if taskID==None:
							print "enqueue host_evacuate_mission error"
				
				db.close()
				
			except:
				print "error: timeCounter=",timeCounter
				traceback.print_exc()
		
		if timeCounter%setting.LOG_CLEANING_PERIOD==0 and i_am_global_controller:
			#delete log in database that older than setting.LOG_CLEANING_PERIOD
			thresholdTime=getCurrentTime()-float(setting.LOG_CLEANING_PERIOD)
			try:
				db = MySQLdb.connect(cacheFile.getDatabaseIP(), setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
				cursor = db.cursor()
				#check permission of moving old log to another table
				cursor.execute("SELECT `value` FROM `cloud_variables` WHERE `key`='hold_all_log'")
				if cursor.fetchone()[0]=='0':
					#just delete it
					cursor.execute("DELETE FROM `hostLoad` WHERE `timestamp`<'%s'"%(str(thresholdTime)))
					cursor.execute("DELETE FROM `guestLoad` WHERE `timestamp`<'%s'"%(str(thresholdTime)))

				else:
					#must move log to another 2 tables before delete
					cursor.execute("SELECT `hostLoadID`,`hostID`,`timestamp`,`idleTime`,`btime` FROM `hostLoad` WHERE `timestamp`<'%s'"%(str(thresholdTime)))
					maxID=0
					tmpData=cursor.fetchall()
					valueList=[]
					for row in tmpData:
						valueList.append("('%s','%s','%s','%s','%s')"%row)
						if row[0]>maxID:
							maxID=row[0]
					
					if len(valueList)>0:
						cursor.execute("INSERT INTO `oldHostLoad` (`hostLoadID`,`hostID`,`timestamp`,`idleTime`,`btime`) VALUES %s"%(','.join(valueList)))
						cursor.execute("DELETE FROM `hostLoad` WHERE `hostLoadID`<=%s"%(maxID))
					###############
					cursor.execute("SELECT `guestLoadID`,`guestID`,`timestamp`,`cpuTime` FROM `guestLoad` WHERE `timestamp`<'%s'"%(str(thresholdTime)))
					maxID=0
					tmpData=cursor.fetchall()
					valueList=[]
					for row in tmpData:
						valueList.append("('%s','%s','%s','%s')"%row)
						if row[0]>maxID:
							maxID=row[0]
					
					if len(valueList)>0:
						cursor.execute("INSERT INTO `oldGuestLoad` (`guestLoadID`,`guestID`,`timestamp`,`cpuTime`) VALUES %s"%(','.join(valueList)))
						cursor.execute("DELETE FROM `guestLoad` WHERE `guestLoadID`<=%s"%(maxID))

				db.close()
			except:
				print "error: timeCounter=",timeCounter
				traceback.print_exc()
		
		if timeCounter%setting.PLANNER_ACTION_PERIOD in [setting.PLANNER_ACTION_PERIOD/2 , 0]:
			#update i_am_global_controller
			i_am_global_controller=(str(myIP)==cacheFile.getGlobalControllerIP())

		if timeCounter%setting.PLANNER_ACTION_PERIOD == setting.PLANNER_ACTION_PERIOD/2 and i_am_global_controller:
			#guest action here
			#1.check auto_mode in database (can do in mode 1 and 2)
			#2.check that old mission was end
			#3.put guest balance mission in queue
			canDo=False
			try:
				db = MySQLdb.connect(cacheFile.getDatabaseIP(), setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
				cursor = db.cursor()
				cursor.execute("SELECT `value` FROM `cloud_variables` WHERE `key`='auto_mode'")
				currentMode=cursor.fetchone()[0]
				
				if currentMode in ['1','2']:
					#check old mission
					cursor.execute("SELECT `taskID` FROM `tasks` WHERE `opcode`='4001' AND (`status`=0 OR `status`=1)")
					if cursor.fetchone()==None:
						canDo=True
				db.close()	
				
			except:
				print "error: timeCounter=",timeCounter
				traceback.print_exc()
			
			if canDo:
				taskID=queue.enqueue({
					'command':'guest_balance_mission',				
				})
				if taskID==None:
					print "enqueue error"

		if timeCounter%setting.PLANNER_ACTION_PERIOD == 0 and i_am_global_controller:
			#host action here
			#1.check auto_mode in database (can do in mode 2 only)
			#2.check that old mission was end
			#3.put host balance mission in queue
			canDo=False
			try:
				db = MySQLdb.connect(cacheFile.getDatabaseIP(), setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
				cursor = db.cursor()
				cursor.execute("SELECT `value` FROM `cloud_variables` WHERE `key`='auto_mode'")
				currentMode=cursor.fetchone()[0]
				
				if currentMode=='2':
					#check old mission
					cursor.execute("SELECT `taskID` FROM `tasks` WHERE `opcode`='4002' AND (`status`=0 OR `status`=1)")
					if cursor.fetchone()==None:
						canDo=True
				db.close()	
				
			except:
				print "error: timeCounter=",timeCounter
				traceback.print_exc()
			
			if canDo:
				taskID=queue.enqueue({
					'command':'host_balance_mission',				
				})
				if taskID==None:
					print "enqueue error"

		#print "\033[A\r"+"end:",timeCounter
		#print "end:",timeCounter
		timeCounter+=1
		time.sleep(1)
