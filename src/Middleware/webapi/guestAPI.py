import setting
from util import connection,cacheFile,network,general
from util import shortcut
from dhcp import dhcpController
from scheduling import queue

import MySQLdb
import json
import os
import random
import traceback

class Guest(object):

	class Create():
		def index(self,guestName,templateID,memory,vCPU,inbound=None,outbound=None):
			detail={
			'command':'guest_create',
			'guestName':guestName,
			'templateID':templateID,
			'memory':memory,
			'vCPU':vCPU
			}

			if inbound!=None:
				detail['inbound']=inbound
			if outbound!=None:
				detail['outbound']=outbound

			taskID=queue.enqueue(detail)

			return shortcut.responseTaskID(taskID)
		
		index.exposed = True

	class Duplicate():
		def index(self,guestName,sourceGuestID,memory=None,vCPU=None,inbound=None,outbound=None):
			detail={
			'command':'guest_duplicate',
			'guestName':guestName,
			'sourceGuestID':sourceGuestID,
			}

			if memory!=None:
				detail['memory']=memory
			if vCPU!=None:
				detail['vCPU']=vCPU
			if inbound!=None:
				detail['inbound']=inbound
			if outbound!=None:
				detail['outbound']=outbound

			taskID=queue.enqueue(detail)

			return shortcut.responseTaskID(taskID)
		
		index.exposed = True

	class Start():
		def index(self,guestID,targetHostID=None):
			detail={
			'command':'guest_start',
			'guestID':guestID
			}

			if targetHostID!=None:
				detail['targetHostID']=targetHostID

			taskID=queue.enqueue(detail)

			return shortcut.responseTaskID(taskID)
		index.exposed = True

	class StartWithIP():
		def index(self,guestIP,targetHostID=None):
			#resolve for guestID
			infoHost=cacheFile.getDatabaseIP()
			db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
			cursor = db.cursor()
			cursor.execute("SELECT `guestID` FROM `guests` WHERE `IPAddress`='%s' "%(guestIP))
			guestID = cursor.fetchone()
			db.close()
			
			if guestID!=None:
				guestID=guestID[0]
			else:
				return shortcut.response('error', '', 'guestIP not found')
			
			detail={
			'command':'guest_start',
			'guestID':guestID
			}

			if targetHostID!=None:
				detail['targetHostID']=targetHostID

			taskID=queue.enqueue(detail)

			return shortcut.responseTaskID(taskID)
		index.exposed = True

	class Suspend():
		def index(self,guestID):
			detail={
			'command':'guest_suspend',
			'guestID':guestID
			}

			taskID=queue.enqueue(detail)

			return shortcut.responseTaskID(taskID)

		index.exposed = True

	class Resume():
		def index(self,guestID):
			detail={
			'command':'guest_resume',
			'guestID':guestID
			}

			taskID=queue.enqueue(detail)

			return shortcut.responseTaskID(taskID)

		index.exposed = True

	

	class Save():
		def index(self,guestID):
			detail={
			'command':'guest_save',
			'guestID':guestID
			}

			taskID=queue.enqueue(detail)

			return shortcut.responseTaskID(taskID)

		index.exposed = True

	class Restore():
		def index(self,guestID,targetHostID=None):	#I think I can restore guest at other host (if last host is not running it cannot restore [now])
			detail={
			'command':'guest_restore',
			'guestID':guestID
			}
			if targetHostID!=None:
				detail['targetHostID']=targetHostID

			taskID=queue.enqueue(detail)

			return shortcut.responseTaskID(taskID)

		index.exposed = True

	class ForceOff():
		def index(self,guestID):
			
			detail={
			'command':'guest_shutoff',
			'guestID':guestID
			}

			taskID=queue.enqueue(detail)

			return shortcut.responseTaskID(taskID)
		index.exposed = True
	
	class ForceOffWithIP():
		def index(self,guestIP):
			
			#resolve for guestID
			infoHost=cacheFile.getDatabaseIP()
			db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
			cursor = db.cursor()
			cursor.execute("SELECT `guestID` FROM `guests` WHERE `IPAddress`='%s' "%(guestIP))
			guestID = cursor.fetchone()[0]
			db.close()
			
			if guestID!=None:
				guestID=guestID[0]
			else:
				return shortcut.response('error', '', 'guestIP not found')

			detail={
			'command':'guest_shutoff',
			'guestID':guestID
			}

			taskID=queue.enqueue(detail)

			return shortcut.responseTaskID(taskID)
		index.exposed = True

	class Destroy():
		def index(self,guestID):
			detail={
			'command':'guest_destroy',
			'guestID':guestID
			}

			taskID=queue.enqueue(detail)

			return shortcut.responseTaskID(taskID)
		index.exposed = True
	
	class Migrate():
		def index(self,guestID,targetHostID):
			detail={
			'command':'guest_migrate',
			'guestID':guestID,
			'targetHostID':targetHostID
			}

			taskID=queue.enqueue(detail)

			return shortcut.responseTaskID(taskID)

		index.exposed = True
	
	class SendShutdownSignal():
		def index(self,guestID):
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
				return shortcut.response('error', '', 'Invalid guestID or Machine was closed or doing activity')
			
			hostIP=targetData[0]
			UUID = targetData[1]

			result=connection.socketCall(hostIP,setting.LOCAL_PORT,'guest_send_shutdown_signal',[UUID])

			if result!="OK":
					return shortcut.response('error', '', result)

			#no content		
			return shortcut.response('success', '', 'Shutdown signal was sending to the guest.')

		index.exposed = True

	class SendRebootSignal():
		'''
		cannot work now (have something to study more)
		'''
		def index(self,guestID):
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
				return shortcut.response('error', '', 'Invalid guestID or Machine was closed or doing activity')
			
			hostIP=targetData[0]
			UUID = targetData[1]

			result=connection.socketCall(hostIP,setting.LOCAL_PORT,'guest_send_reboot_signal',[UUID])

			if result!="OK":
					return shortcut.response('error', '', result)

			#no content		
			return shortcut.response('success', '', 'Reboot signal was sending to the guest.')

		index.exposed = True
	

	class GetInfo():
		'''
		get guest info from database only
		'''
		def index(self,guestID=None):
			infoHost=cacheFile.getDatabaseIP()
			db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
			cursor = db.cursor()
			
			if guestID==None:
				conditionString="";
			else:
				conditionString="WHERE `guestID`=%s"%(str(guestID))
			
			cursor.execute('''SELECT 
			`guestID`, `guestName`,`MACAddress`,`IPAddress`,`templateID`,`lastHostID`,`lastUUID`,`memory`,`vCPU`,`inboundBandwidth`,`outboundBandwidth` 
			FROM `guests`'''+conditionString+";")
			
			table=cursor.fetchall()
			db.close()	
			
			templateString=open(setting.MAIN_PATH+'webapi/template/guest_getInfo.xml').read()
			result=''
			for row in table:
				guestDict={
				'guestID':str(row[0]),
				'guestName':str(row[1]),
				'MACAddress':str(row[2]),
				'IPAddress':str(row[3]),
				'templateID':str(row[4]),
				'lastHostID':str(row[5]),
				'lastUUID':str(row[6]),
				'memory':str(row[7]*1024*1024),		#MB to Byte
				'vCPU':str(row[8]),
				'inboundBandwidth':str(row[9]),
				'outboundBandwidth':str(row[10])
				}
				#print "~~~~~~~~~~~~~~~~~~~~~~~"
				#print templateString
				#print guestDict
				#print "#######################"
				result+=templateString%guestDict
			
			return shortcut.response('success', result)
			
		index.exposed = True

	class GetState():
		'''
		update guest status and get it to return
		'''
		def index(self,guestID=None):
			infoHost=cacheFile.getDatabaseIP()
			db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
			cursor = db.cursor()
			
			if guestID!=None:
				condition=" WHERE `guestID`=%s"%(str(guestID))
			else:
				condition=""

			cursor.execute("SELECT `status`, `activity`, `guestID`, `guestName` FROM `guests`"+condition)
			guestDataList=cursor.fetchall()

			content=''
			templateString=open(setting.MAIN_PATH+'webapi/template/guest_getState.xml').read()
		
			for oldData in guestDataList:
				status=oldData[0]
				activity=oldData[1]
				currentGuestID=oldData[2]
				currentGuestName=oldData[3]
				
				if status!=1:	# No need to update status
					runningState=0
				elif status==1:	# real status can be 0, must be update 
					#find hostIPAddress, UUID
					cursor.execute('''SELECT `hosts`.`IPAddress` , `lastUUID`
						FROM `hosts` INNER JOIN `guests` 
						ON `hosts`.`hostID`=`guests`.`lastHostID` 
						AND `guests`.`status`=1
						AND `guests`.`guestID`=%s;'''%(currentGuestID))
					lastData = cursor.fetchone()
			
					print lastData
					if lastData!=None:
						hostIP=lastData[0]
						UUID = lastData[1]
						if hostIP!=None and UUID!=None:
							guestStatus=connection.socketCall(hostIP,setting.LOCAL_PORT,'guest_update_status',[UUID,str(currentGuestID)])
							try:
								guestStatus=json.loads(guestStatus)
								status=guestStatus['status']
								runningState=guestStatus['runningState']
							except:
								return shortcut.response('error', '', guestStatus)			
						else:
							return shortcut.response('error', '', 'hostIP & UUID was made to be NULL before (it is bug)')
					else:
						return shortcut.response('error', '', 'Invalid guestID')
				else:
					return shortcut.response('error', '', 'Status error (bug sure)')

				stateDict={
				'guestID':currentGuestID,
				'guestName':currentGuestName,
				'status':status,
				'activity':activity,
				'runningState':runningState
				}
				content+=templateString%stateDict
			return shortcut.response('success', content)
		
		index.exposed = True

	class GetCurrentCPUInfo():
		def index(self,guestID):
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
				return shortcut.response('error', '', 'Invalid guestID or cannot suspend in this status')
			
			hostIP=targetData[0]
			UUID = targetData[1]

			result=connection.socketCall(hostIP,setting.LOCAL_PORT, 'guest_get_current_info', [UUID,'cpu'])
				
			try:
				result=json.loads(result)
			except:
				if type(result)==type('str'):
					return shortcut.response('error', '', result)
				else:
					return shortcut.response('error', '', 'May be network error')

			percent=result['cpuInfo']['usage']
			cpuTime=result['cpuInfo']['cpuTime']

			content='''
			<guest guestID="%s">
				<average>%s</average>
				<cpuTime>%s</cpuTime>
			</guest>
			'''%(str(guestID),percent,cpuTime)
			return shortcut.response('success', content)

		index.exposed = True
	
	class GetCurrentMemoryInfo():
		def index(self,guestID):
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
				return shortcut.response('error', '', 'Invalid guestID or cannot suspend in this status')
			
			hostIP=targetData[0]
			UUID = targetData[1]

			result=connection.socketCall(hostIP,setting.LOCAL_PORT, 'guest_get_current_info', [UUID,'memory'])
				
			try:
				result=json.loads(result)
			except:
				if type(result)==type('str'):
					return shortcut.response('error', '', result)
				else:
					return shortcut.response('error', '', 'May be network error')

			memTotal=result['memoryInfo']['total']
			memUsage=result['memoryInfo']['usage']

			content='''
			<guest guestID="%s">
				<memTotal>%s</memTotal>
				<memUse>%s</memUse>
			</guest>
			'''%(str(guestID),str(memTotal),str(memUsage))
			return shortcut.response('success', content)

		index.exposed = True

	class GetCurrentNetworkInfo():
		def index(self,guestID):
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
				return shortcut.response('error', '', 'Invalid guestID or cannot suspend in this status')
			
			hostIP=targetData[0]
			UUID = targetData[1]

			result=connection.socketCall(hostIP,setting.LOCAL_PORT, 'guest_get_current_info', [UUID,'network'])
				
			try:
				result=json.loads(result)
			except:
				if type(result)==type('str'):
					return shortcut.response('error', '', result)
				else:
					return shortcut.response('error', '', 'May be network error')

			rx=result['networkInfo']['rxRate']
			tx=result['networkInfo']['txRate']
			sumRx=result['networkInfo']['rxUsed']
			sumTx=result['networkInfo']['txUsed']

			content='''
			<guest guestID="%s">
				<rx>%s</rx>
				<tx>%s</tx>
				<sumRx>%s</sumRx>
				<sumTx>%s</sumTx>
			</guest>
			'''%(str(guestID),str(rx),str(tx),str(sumRx),str(sumTx))
			return shortcut.response('success', content)

		index.exposed = True

	class GetCurrentIOInfo():
		def index(self,guestID):
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
				return shortcut.response('error', '', 'Invalid guestID or cannot suspend in this status')
			
			hostIP=targetData[0]
			UUID = targetData[1]

			result=connection.socketCall(hostIP,setting.LOCAL_PORT, 'guest_get_current_info', [UUID,'io'])
				
			try:
				result=json.loads(result)
			except:
				if type(result)==type('str'):
					return shortcut.response('error', '', result)
				else:
					return shortcut.response('error', '', 'May be network error')

			rx=result['ioInfo']['rxRate']
			wx=result['ioInfo']['wxRate']
			sumRx=result['ioInfo']['rxUsed']
			sumWx=result['ioInfo']['wxUsed']

			content='''
			<guest guestID="%s">
				<rx>%s</rx>
				<wx>%s</wx>
				<sumRx>%s</sumRx>
				<sumWx>%s</sumWx>
			</guest>
			'''%(str(guestID),str(rx),str(wx),str(sumRx),str(sumWx))
			return shortcut.response('success', content)

		index.exposed = True

	class GetCustomizedInfo():
		'''
		return customized info
		cpu={0,1}
		memory={0,1}
		network={0,1}
		io={0,1}
		guestID=3,6,9,10,15
		'''
		def index(self,cpu,memory,network,io,guestIDs):
			#validate input
			enables=[cpu,memory,network,io]
			for element in enables:
				if element!='1' and element!='0':
					return shortcut.response('error', '', 'invalid parameter (enabler path)')
			
			if int(cpu)+int(memory)+int(network)+int(io)==0:
				return shortcut.response('error', '', 'invalid parameter (nothing to monitor)')
			
			guestList=[]
			if guestIDs!=None:	
				for element in guestIDs.split(','):
					try:
						guestList.append(str(int(element)))
					except:
						return shortcut.response('error', '', 'invalid parameter (guestIDs path)')
			
			if guestList==[]:
				return shortcut.response('error', '', 'invalid guestIDs')

			optionList=[]
			if cpu=='1':
				optionList.append('cpu')
			if memory=='1':
				optionList.append('memory')
			if network=='1':
				optionList.append('network')
			if io=='1':
				optionList.append('io')

			infoHost=cacheFile.getDatabaseIP()
			db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
			cursor = db.cursor()
			
			#find hostIPAddress, UUID
			cursor.execute('''SELECT  `hosts`.`IPAddress` , `lastUUID`, `guests`.`guestID`
			FROM `hosts` INNER JOIN `guests` 
			ON `hosts`.`hostID`=`guests`.`lastHostID` 
			AND `guests`.`status`=1 AND `guests`.`activity`=0
			AND `guests`.`guestID` IN (%s);'''%(','.join(guestList)))

			fetchedData=cursor.fetchall()
			content=''
			for guestID in guestList:
				inGuest=''
				#search guestID in fetchedData
				selectedData=None
				for element in fetchedData:
					if str(element[2])==str(guestID):
						selectedData=element
						break

				if selectedData==None:
					content+='<guest guestID="%s" polling="error">cannot get info from this guest. (guest not found or guest is busy)</guest>'%(str(guestID))
					continue
				
				hostIP=selectedData[0]
				UUID = selectedData[1]
				
				result=connection.socketCall(hostIP,setting.LOCAL_PORT, 'guest_get_current_info', [UUID]+optionList)
					
				try:
					result=json.loads(result)
				except:
					if type(result)==type('str'):
						content+='<guest guestID="%s" polling="error">cannot get info from this guest. (json convert state)</guest>'%(str(guestID))
						continue
					else:
						content+='<guest guestID="%s" polling="error">cannot get info from this guest. (maybe network error)</guest>'%(str(guestID))
						continue

				if cpu=='1':
					percent=result['cpuInfo']['usage']
					cpuTime=result['cpuInfo']['cpuTime']

					inGuest+='''
					<cpuInfo guestID="%s">
						<average>%s</average>
						<cpuTime>%s</cpuTime>
					</cpuInfo>
					'''%(str(guestID),percent,cpuTime)

				if memory=='1':
					memTotal=result['memoryInfo']['total']
					memUsage=result['memoryInfo']['usage']

					inGuest+='''
					<memoryInfo guestID="%s">
						<memTotal>%s</memTotal>
						<memUse>%s</memUse>
					</memoryInfo>
					'''%(str(guestID),str(memTotal),str(memUsage))

				if network=='1':
					rx=result['networkInfo']['rxRate']
					tx=result['networkInfo']['txRate']
					sumRx=result['networkInfo']['rxUsed']
					sumTx=result['networkInfo']['txUsed']

					inGuest+='''
					<networkInfo guestID="%s">
						<rx>%s</rx>
						<tx>%s</tx>
						<sumRx>%s</sumRx>
						<sumTx>%s</sumTx>
					</networkInfo>
					'''%(str(guestID),str(rx),str(tx),str(sumRx),str(sumTx))


				if io=='1':
					rx=result['ioInfo']['rxRate']
					wx=result['ioInfo']['wxRate']
					sumRx=result['ioInfo']['rxUsed']
					sumWx=result['ioInfo']['wxUsed']

					inGuest+='''
					<ioInfo guestID="%s">
						<rx>%s</rx>
						<wx>%s</wx>
						<sumRx>%s</sumRx>
						<sumWx>%s</sumWx>
					</ioInfo>
					'''%(str(guestID),str(rx),str(wx),str(sumRx),str(sumWx))

				content+='<guest guestID="%s" polling="success">%s</guest>'%(str(guestID),inGuest)

			return shortcut.response('success', content)
		
		index.exposed = True
	
	class Rename():
		'''
		change guest name (only in database)
		'''
		def index(self,guestID,guestName):
			try:
				if not general.isGoodName(guestName):
					return 'Name '+guestName+' cannot be a guestName, please choose the new one.'
				
				infoHost=cacheFile.getDatabaseIP()
				db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
				cursor = db.cursor()
				
				cursor.execute("SELECT `guestID` FROM `guests` WHERE `guestID`=%s"%(guestID))
				if cursor.fetchone()==None:
					db.close()
					return shortcut.response('error', '', 'no guest found')
				
				if guestName=='':
					db.close()
					return shortcut.response('error', '', 'invalid guest name')

				cursor.execute("UPDATE `guests` SET `guestName`='%s' WHERE `guestID`=%s"%(guestName,guestID))
				
				db.close()

			except:
				return shortcut.response('error', '', MySQLdb.escape_string(traceback.format_exc()))

			content=''
			return shortcut.response('success', content,'Your guest has been renamed')
		
		index.exposed = True
	
	class ScaleCPU():
		'''
		this can scale while guest running
		'''
		def index(self,guestID,vCPU):
			detail={
			'command':'guest_scale_cpu',
			'guestID':guestID,
			'vCPU':vCPU,
			}

			taskID=queue.enqueue(detail)

			return shortcut.responseTaskID(taskID)

		index.exposed = True
	
	class ScaleMemory():
		'''
		this can scale while guest running
		'''
		def index(self,guestID,memory):
			detail={
			'command':'guest_scale_memory',
			'guestID':guestID,
			'memory':memory,
			}

			taskID=queue.enqueue(detail)

			return shortcut.responseTaskID(taskID)

		index.exposed = True

	class ScaleBandwidth():
		'''
		change guest name (only in database)
		'''
		def index(self,guestID,inbound=None,outbound=None):
			try:
				infoHost=cacheFile.getDatabaseIP()
				db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
				cursor = db.cursor()
				
				#checking parameter
				cursor.execute("SELECT `guestID` FROM `guests` WHERE `guestID`=%s"%(guestID))
				if cursor.fetchone()==None:
					db.close()
					return shortcut.response('error', '', 'no guest found')
				
				if inbound==None and outbound==None:
					db.close()
					return shortcut.response('error', '', 'please set parameter inbound or outbound')
				
				if inbound not in [None, 'infinite']:
					try:
						tmp=int(inbound)
					except:
						db.close()
						return shortcut.response('error', '', 'invalid parameter inbound')
				
				if outbound not in [None, 'infinite']:
					try:
						tmp=int(outbound)
					except:
						db.close()
						return shortcut.response('error', '', 'invalid parameter outbound')
				
				#set value in database
				if inbound!=None:
					if inbound=='infinite':
						cursor.execute("UPDATE `guests` SET `inboundBandwidth`=NULL WHERE `guestID`=%s"%(guestID))
					else:
						cursor.execute("UPDATE `guests` SET `inboundBandwidth`=%s WHERE `guestID`=%s"%(inbound,guestID))
				
				if outbound!=None:
					if outbound=='infinite':
						cursor.execute("UPDATE `guests` SET `outboundBandwidth`=NULL WHERE `guestID`=%s"%(guestID))
					else:
						cursor.execute("UPDATE `guests` SET `outboundBandwidth`=%s WHERE `guestID`=%s"%(outbound,guestID))

				db.close()

			except:
				return shortcut.response('error', '', MySQLdb.escape_string(traceback.format_exc()))

			content=''
			return shortcut.response('success', content,"Your guest's bandwidth will be changed when you're turning it on")
		
		index.exposed = True	

	create = Create()
	duplicate = Duplicate()
	start  = Start()
	startWithIP = StartWithIP()

	suspend = Suspend()
	resume = Resume()
	
	save = Save()
	restore = Restore()
	forceOff = ForceOff()
	forceOffWithIP=ForceOffWithIP()
	destroy = Destroy()
	
	migrate = Migrate()

	sendShutdownSignal = SendShutdownSignal()
	sendRebootSignal = SendRebootSignal()

	getInfo = GetInfo()
	getState = GetState()
	getCurrentCPUInfo = GetCurrentCPUInfo()
	getCurrentMemoryInfo = GetCurrentMemoryInfo()
	getCurrentNetworkInfo = GetCurrentNetworkInfo()
	getCurrentIOInfo = GetCurrentIOInfo()
	
	getCustomizedInfo = GetCustomizedInfo()

	rename = Rename()

	scaleCPU = ScaleCPU()
	scaleMemory = ScaleMemory()
	scaleBandwidth = ScaleBandwidth()
