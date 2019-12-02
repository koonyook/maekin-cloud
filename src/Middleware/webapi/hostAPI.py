import setting

import MySQLdb
import json
from util import connection,cacheFile,network,general
from util import shortcut
from scheduling import queue

class Host(object):

	class GetInfo():
		def index(self,hostID=None):
			#get data from database
			infoHost=cacheFile.getDatabaseIP()
			db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
			cursor = db.cursor()
			
			if hostID==None:
				conditionString="";
			else:
				conditionString="WHERE `hostID`=%s"%(str(hostID))
			
			cursor.execute('''SELECT 
			`hostID`, `hostName`,`status`,`activity`,`MACAddress`,`IPAddress`,`isHost`,`isGlobalController`,`isInformationServer`,`isStorageHolder`,`isCA`
			FROM `hosts`'''+conditionString+";")
			
			table=cursor.fetchall()
			
			if len(table)==0:
				return shortcut.response('error','','hostID not found')

			if hostID==None:
				argv=[]
			else:
				argv=[str(table[0][5])]	#IPAddr
			
			specData=connection.socketCall("localhost",setting.MONITOR_PORT,"get_host_spec",argv)
			#print "#############specData##############"
			#print specData
			specData=json.loads(specData)
			
			templateString=open(setting.MAIN_PATH+'webapi/template/host_getInfo.xml').read()
			result=''
			for row in table:
				hostDict={
				'hostID':str(row[0]),
				'hostName':str(row[1]),
				'status':str(row[2]),
				'activity':str(row[3]),
				'MAC':str(row[4]),
				'IP':str(row[5]),
				'isHost':str(row[6]),
				'isGlobalController':str(row[7]),
				'isInformationServer':str(row[8]),
				'isNFSServer':str(row[9]),
				'isCA':str(row[10])
				}
				specFound=False
				for element in specData:
					if element['IP']==hostDict['IP']:
						hostDict['mem_size']=element['spec']['memory']['size']
						hostDict['mem_type']=element['spec']['memory']['type']
						hostDict['mem_speed']=element['spec']['memory']['speed']
						hostDict['cpu_number']=element['spec']['cpu']['number']
						hostDict['cpu_model']=element['spec']['cpu']['model']
						hostDict['cpu_cache']=element['spec']['cpu']['cache']
						hostDict['cpu_speed']=element['spec']['cpu']['speed']
						specFound=True
						break
				
				if not specFound:
					errorMessage="Data is not ready"
					hostDict['mem_size']=errorMessage
					hostDict['mem_type']=errorMessage
					hostDict['mem_speed']=errorMessage
					hostDict['cpu_number']=errorMessage
					hostDict['cpu_model']=errorMessage
					hostDict['cpu_cache']=errorMessage
					hostDict['cpu_speed']=errorMessage

				result+=templateString%hostDict
			
			db.close()

			return shortcut.response('success', result)

		index.exposed = True

	class GetCurrentCPUInfo():
		def index(self,hostID=None):
			infoHost=cacheFile.getDatabaseIP()
			db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
			cursor = db.cursor()
			
			if hostID==None:
				conditionString="";
			else:
				conditionString="WHERE `hostID`=%s"%(str(hostID))
			
			cursor.execute('''SELECT 
			`hostID`, `IPAddress` 
			FROM `hosts`'''+conditionString+";")

			table=cursor.fetchall()
				
			if len(table)==0:
				return shortcut.response('error','','hostID not found')

			if hostID==None:
				argv=[]
			else:
				argv=[str(table[0][1])]	#IPAddr
			
			data=connection.socketCall("localhost",setting.MONITOR_PORT,"get_current_cpu_info",argv)
			data=json.loads(data)

			templateString=open(setting.MAIN_PATH+'webapi/template/host_getCurrentCPUInfo.xml').read()
			result=''
			for row in table:
				hostDict={
				'hostID':str(row[0]),
				'IP':str(row[1])
				}
				#set default value in case of no data
				hostDict['average']="-"

				for element in data:
					if element['IP']==hostDict['IP']:
						percent_list=element['cpu_info']
						total=0.0
						for p in percent_list:
							total+=float(p)
						hostDict['average']=str(total/float(len(percent_list)))
						break

				result+=templateString%hostDict
			
			db.close()

			return shortcut.response('success', result)

		index.exposed = True
	
	class GetCurrentMemoryInfo():
		def index(self,hostID=None):
			infoHost=cacheFile.getDatabaseIP()
			db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
			cursor = db.cursor()
			
			if hostID==None:
				conditionString="";
			else:
				conditionString="WHERE `hostID`=%s"%(str(hostID))
			
			cursor.execute('''SELECT 
			`hostID`, `IPAddress` 
			FROM `hosts`'''+conditionString+";")

			table=cursor.fetchall()
			
			if len(table)==0:
				return shortcut.response('error','','hostID not found')

			if hostID==None:
				argv=[]
			else:
				argv=[str(table[0][1])]	#IPAddr
			
			data=connection.socketCall("localhost",setting.MONITOR_PORT,"get_current_memory_info",argv)
			data=json.loads(data)
			
			templateString=open(setting.MAIN_PATH+'webapi/template/host_getCurrentMemoryInfo.xml').read()
			result=''
			for row in table:
				hostDict={
				'hostID':str(row[0]),
				'IP':str(row[1])
				}
				#set default value in case of no data
				hostDict['memTotal']="-"
				hostDict['memTotalUnit']="-"
				hostDict['memFree']="-"
				hostDict['memFreeUnit']="-"

				for element in data:
					if element['IP']==hostDict['IP']:
						hostDict['memTotal']=element['memory_info']['MemTotal'][0]
						hostDict['memTotalUnit']=element['memory_info']['MemTotal'][1]
						hostDict['memFree']=element['memory_info']['MemFree'][0]
						hostDict['memFreeUnit']=element['memory_info']['MemFree'][1]
						break

				result+=templateString%hostDict
			
			db.close()

			return shortcut.response('success', result)

		index.exposed = True

	class GetCurrentNetworkInfo():
		def index(self,hostID=None):
			infoHost=cacheFile.getDatabaseIP()
			db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
			cursor = db.cursor()
			
			if hostID==None:
				conditionString="";
			else:
				conditionString="WHERE `hostID`=%s"%(str(hostID))
			
			cursor.execute('''SELECT 
			`hostID`, `IPAddress` 
			FROM `hosts`'''+conditionString+";")

			table=cursor.fetchall()
			
			if len(table)==0:
				return shortcut.response('error','','hostID not found')

			if hostID==None:
				argv=[]
			else:
				argv=[str(table[0][1])]	#IPAddr
			
			data=connection.socketCall("localhost",setting.MONITOR_PORT,"get_current_network_info",argv)
			data=json.loads(data)
			
			templateString=open(setting.MAIN_PATH+'webapi/template/host_getCurrentNetworkInfo.xml').read()
			result=''
			for row in table:
				hostDict={
				'hostID':str(row[0]),
				'IP':str(row[1])
				}
				#set default value in case of no data
				hostDict['transmit_rate']="-"
				hostDict['recieve_rate']="-"

				for element in data:
					if element['IP']==hostDict['IP']:
						#find eth0 and get data
						for	interface in element['network_info']:			
							if interface['interface']=='eth0':
								hostDict['transmit_rate']=interface['tx']
								hostDict['recieve_rate']=interface['rx']
								break

						break

				result+=templateString%hostDict
			
			db.close()

			return shortcut.response('success', result)

		index.exposed = True

	class GetCurrentStorageInfo():
		def index(self,hostID=None):
			infoHost=cacheFile.getDatabaseIP()
			db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
			cursor = db.cursor()
			
			if hostID==None:
				conditionString="";
			else:
				conditionString="WHERE `hostID`=%s"%(str(hostID))
			
			cursor.execute('''SELECT 
			`hostID`, `IPAddress` 
			FROM `hosts`'''+conditionString+";")

			table=cursor.fetchall()
			
			if len(table)==0:
				return shortcut.response('error','','hostID not found')

			if hostID==None:
				argv=[]
			else:
				argv=[str(table[0][1])]	#IPAddr
			
			data=connection.socketCall("localhost",setting.MONITOR_PORT,"get_current_storage_info",argv)
			data=json.loads(data)
			
			templateString=open(setting.MAIN_PATH+'webapi/template/host_getCurrentStorageInfo.xml').read()
			result=''
			for row in table:
				hostDict={
				'hostID':str(row[0]),
				'IP':str(row[1])
				}
				#set default value in case of no data
				hostDict['capacity']="-"
				hostDict['free']="-"
				hostDict['maekin_usage']="-"
				hostDict['image_usage']="-"

				for element in data:
					if element['IP']==hostDict['IP']:
						hostDict['capacity']=element['storage_info']['capacity']
						hostDict['free']=element['storage_info']['free']
						hostDict['maekin_usage']=element['storage_info']['maekin_usage']
						hostDict['image_usage']=element['storage_info']['image_usage']
						break

				result+=templateString%hostDict
			
			db.close()

			return shortcut.response('success', result)

		index.exposed = True

	class GetAllCurrentInfo():
		def index(self,hostID=None):
			infoHost=cacheFile.getDatabaseIP()
			db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
			cursor = db.cursor()
			
			if hostID==None:
				conditionString="";
			else:
				conditionString="WHERE `hostID`=%s"%(str(hostID))
			
			cursor.execute('''SELECT 
			`hostID`, `IPAddress` 
			FROM `hosts`'''+conditionString)

			table=cursor.fetchall()
				
			if len(table)==0:
				return shortcut.response('error','','hostID not found')

			if hostID==None:
				argv=[]
			else:
				argv=[str(table[0][1])]	#IPAddr
			
			data=connection.socketCall("localhost",setting.MONITOR_PORT,"get_current_info",argv)
			data=json.loads(data)

			cpuTemplateString=open(setting.MAIN_PATH+'webapi/template/host_getCurrentCPUInfo.xml').read()
			memoryTemplateString=open(setting.MAIN_PATH+'webapi/template/host_getCurrentMemoryInfo.xml').read()
			networkTemplateString=open(setting.MAIN_PATH+'webapi/template/host_getCurrentNetworkInfo.xml').read()
			storageTemplateString=open(setting.MAIN_PATH+'webapi/template/host_getCurrentStorageInfo.xml').read()

			result=''
			for row in table:
				inHost=''
				hostDict={
				'hostID':str(row[0]),
				'IP':str(row[1])
				}
				#search for current element in data
				currentData=None
				for element in data:
					if element['IP']==hostDict['IP']:
						currentData=element
				
				if currentData==None:
					result+='<host hostID="%s" polling="error">Info not found</host>'%(str(row[0]))
					continue
				
				#cpuInfo
				percent_list=currentData['cpu_info']
				total=0.0
				for p in percent_list:
					total+=float(p)
				hostDict['average']=str(total/float(len(percent_list)))
			
				inHost+=cpuTemplateString%hostDict
				
				#memoryInfo
				hostDict['memTotal']=currentData['memory_info']['MemTotal'][0]
				hostDict['memTotalUnit']=currentData['memory_info']['MemTotal'][1]
				hostDict['memFree']=currentData['memory_info']['MemFree'][0]
				hostDict['memFreeUnit']=currentData['memory_info']['MemFree'][1]

				inHost+=memoryTemplateString%hostDict

				#networkInfo
				for	interface in currentData['network_info']:			
					if interface['interface']=='eth0':
						hostDict['transmit_rate']=interface['tx']
						hostDict['recieve_rate']=interface['rx']
						break
				
				inHost+=networkTemplateString%hostDict

				#storageInfo
				hostDict['capacity']=currentData['storage_info']['capacity']
				hostDict['free']=currentData['storage_info']['free']
				hostDict['maekin_usage']=currentData['storage_info']['maekin_usage']
				hostDict['image_usage']=currentData['storage_info']['image_usage']
				
				inHost+=storageTemplateString%hostDict

				result+='<host hostID="%s" polling="success">%s</host>'%(str(row[0]),inHost)
			
			db.close()

			return shortcut.response('success', result)

		index.exposed = True
	
	class Close():
		def index(self,hostID,mode):
			if mode not in ['standby','hibernate','shutdown']:
				return shortcut.response('error','','invalid mode')
			
			detail={
			'command':'host_close',
			'hostID':hostID,
			'mode':mode					#{'standby','hibernate','shutdown'}
			}

			taskID=queue.enqueue(detail)

			return shortcut.responseTaskID(taskID)

		index.exposed = True
	
	class Wakeup():
		def index(self,hostID):
			detail={
			'command':'host_wakeup',
			'hostID':hostID
			}

			taskID=queue.enqueue(detail)

			return shortcut.responseTaskID(taskID)

		index.exposed = True
	
	class Remove():
		def index(self,hostID):
			detail={
			'command':'host_remove',
			'hostID':hostID
			}

			taskID=queue.enqueue(detail)

			return shortcut.responseTaskID(taskID)

		index.exposed = True
	
	class Add():					
		def index(self,hostName,MACAddress,IPAddress):
			detail={
			'command':'host_add',
			'hostName':hostName,
			'MACAddress':MACAddress,
			'IPAddress':IPAddress
			}

			taskID=queue.enqueue(detail)

			return shortcut.responseTaskID(taskID)

		index.exposed = True
	
	class SetIsHost():
		def index(self,hostID,isHost):
			
			if isHost!='0' and isHost!='1':
				return shortcut.response('error','','invalid syntax')
			
			infoHost=cacheFile.getDatabaseIP()
			db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
			cursor = db.cursor()
			
			cursor.execute("SELECT `isHost` FROM `hosts` WHERE `hostID`=%s"%(hostID))
			tmp=cursor.fetchone()
			if tmp==None:
				return shortcut.response('error', '', 'hostID not found')
			
			if isHost==str(tmp[0]):
				return shortcut.response('success', '', 'you did not change anything')

			if isHost=='0':	#check many things in this case
				cursor.execute("SELECT `hostID` FROM `hosts` WHERE `hostID`<>%s AND `isHost`=1 AND `status`=1 AND `activity`=0"%(hostID))
				if cursor.fetchone()==None:
					return shortcut.response('error', '', 'you need at least one active host that have isHost=1 and activity=0')
				
				detail={
					'command':'host_evacuate_mission',
					'hostID':hostID
				}

				taskID=queue.enqueue(detail)
			
			cursor.execute("UPDATE `hosts` SET `isHost`=%s WHERE `hostID`=%s"%(isHost,hostID))
			db.close()
			
			result=''
			return shortcut.response('success',result)

		index.exposed = True


	getInfo = GetInfo()
	getCurrentCPUInfo = GetCurrentCPUInfo()
	getCurrentMemoryInfo = GetCurrentMemoryInfo()
	getCurrentNetworkInfo = GetCurrentNetworkInfo()
	getCurrentStorageInfo = GetCurrentStorageInfo()

	getAllCurrentInfo = GetAllCurrentInfo()

	close = Close()
	wakeup = Wakeup()

	remove = Remove()
	add = Add()		
	
	setIsHost = SetIsHost()	
