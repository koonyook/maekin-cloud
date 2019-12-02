'''
method name must match to the real command
'''
import sys
import time
import types
from xml.dom import minidom
import re
import inspect
import threading

import setting
from util import network
from shellUtil import getMyFunctionName,requestTo,requestAndWait,getTable
from shellUtil import PressKeyThread,MonitorPanel
from util.xmlUtil import getValue
import converter


def help(argv,param):
	'''List all the command that you can use.\nhelp [command]\tShow description of specific command;
	'''
	commandDict=param[3]
	commandList=commandDict.keys()
	
	if argv==[]:
		commandList.sort()
		for commandName in commandList:
			shortHelp=commandDict[commandName].__doc__.split(';')[0]
			print commandName+"\t"+shortHelp
	else:
		if argv[0] not in commandList:
			print "Command %s not found"%(argv[0])
		else:
			print commandDict[argv[0]].__doc__

	
def where(argv,param):
	'''Tell IP address and port of connected api;
	'''
	print param[0]+":"+str(setting.API_PORT)

def setautomode(argv,param):
	'''Set level of cloud automation;
	Usage:
		setautomode MODE
	MODE:
		0 = Full Manual
		1 = Auto Guest Migration
		2 = Auto Guest and Host Controll
	'''
	if len(argv)!=1:
		print param[3][getMyFunctionName()].__doc__
		return
	
	if argv[0] in ['0','1','2']:
		result=requestTo(param[0],param[1],'/cloud/setAutoMode?mode=%s'%(argv[0]))
		if result==None:
			print 'set mode error'
			return
		
		dom = minidom.parseString(result)
		if getValue(dom,'response','type')=='success':
			print 'set mode success'
		else:
			print 'set mode error:',getValue(dom,'message')
		
		return

	else:
		print param[3][getMyFunctionName()].__doc__
		return

def setlog(argv,param):
	'''Set level of host and guest load logging;
	Usage:
		setlog MODE
	MODE:
		0 = Normal usage (default)
		1 = For testing and debugging only
	'''
	if len(argv)!=1:
		print param[3][getMyFunctionName()].__doc__
		return
	
	if argv[0] in ['0','1']:
		result=requestTo(param[0],param[1],'/cloud/setLogMode?mode=%s'%(argv[0]))
		if result==None:
			print 'set mode error'
			return
		
		dom = minidom.parseString(result)
		if getValue(dom,'response','type')=='success':
			print 'set mode success'
		else:
			print 'set mode error:',getValue(dom,'message')
		
		return

	else:
		print param[3][getMyFunctionName()].__doc__
		return

def clearoldlog(argv,param):
	'''clear host and guest load logging;
	Usage:
		clearoldlog
	'''
	result=requestTo(param[0],param[1],'/cloud/clearOldLog')
	if result==None:
		print 'clear log error'
		return
	
	dom = minidom.parseString(result)
	if getValue(dom,'response','type')=='success':
		print 'clear log success'
	else:
		print 'clear log error:',getValue(dom,'message')
	
	return

def changecloud(argv,param):
	'''Change connection to the new place;
	Usage:
		changecloud IPADDRESS[:PORT]
	this command use default port when it was ignored
	'''
	if len(argv)!=1:
		print param[3][getMyFunctionName()].__doc__
		return
	
	targetData=argv[0].split(':')
	if len(targetData)==1:
		#only get ip
		ip=targetData[0]
		port=setting.API_PORT
	elif len(targetData)==2:
		ip,port=targetData
	else:
		print param[3][getMyFunctionName()].__doc__
		return
	
	token=requestTo(ip,port,'/connect/getToken')
	if token==None:
		print "Connect to %s:%s error"%(str(ip),str(port))
		return
	
	print "Connect to %s:%s success"%(str(ip),str(port))
	return {
	'newIP':ip,
	'newPort':port,
	'newToken':token
	}

def cloudinfo(argv,param):
	'''Get cloud information include storage space information;
	'''
	result=[('key','value')]
	generalInfo=requestTo(param[0],param[1],'/cloud/getInfo')
	dom = minidom.parseString(generalInfo)
	result+=[('UUID',getValue(dom,'UUID')) ]
	result+=[('name',getValue(dom,'name')) ]
	result+=[('network ID',getValue(dom,'network','id')) ]
	result+=[('netmask',getValue(dom,'network','mask')) ]
	result+=[('default route',getValue(dom,'network','defaultRoute')) ]
	key='dns'
	if getValue(dom,'dns') not in [None,'']:
		for element in getValue(dom,'dns').split(','):
			result+=[(key,element)]
			key=''
	else:
		result+=[(key,'None')]
		key=''

	simpleIPList=network.getIPPoolStringList(getValue(dom,'guest').split(','))
	key='guest IP Pool'
	for element in simpleIPList:
		result+=[(key,element) ]
		key=''
	
	result+=[('auto mode',converter.autoMode[getValue(dom,'autoMode')]) ]

	storageInfo=requestTo(param[0],param[1],'/cloud/getStorageInfo')
	dom = minidom.parseString(storageInfo)
	capacity=getValue(dom,'capacity')
	free=getValue(dom,'free')
	percent= (float(capacity)-float(free))*100.0/float(capacity)
	result+=[('storage usage','%s/%s (%.2f%%)'%(int(capacity)-int(free),capacity,percent))]
	
	hostInfo=requestTo(param[0],param[1],'/host/getInfo')
	dom = minidom.parseString(hostInfo)
	hostList=dom.getElementsByTagName('host')
	activeCount=0
	for element in hostList:
		if getValue(element,'status')=='1':
			activeCount+=1
	result+=[('active Host','%d/%d'%(activeCount,len(hostList)))]

	guestInfo=requestTo(param[0],param[1],'/guest/getState')
	dom = minidom.parseString(guestInfo)
	guestList=dom.getElementsByTagName('guest')
	activeCount=0
	for element in guestList:
		if getValue(element,'status')=='1':
			activeCount+=1
	result+=[('active Guest','%d/%d'%(activeCount,len(guestList)))]
	
	print getTable(result)

def hostlist(argv,param):
	'''List ID, name and status of all host;
	Usage:
		hostlist [OPTIONS]
	Options:
		-a for activity
		-i for IP address
		-s for service that host provide	
	'''
	optionList=tuple()
	for option in argv:
		if option=='-a':
			optionList+=('activity',)
		elif option=='-i':
			optionList+=('IP',)
		elif option=='-s':
			optionList+=('service',)
		else:
			print param[3][getMyFunctionName()].__doc__
			return

	hostInfo=requestTo(param[0],param[1],'/host/getInfo')
	dom = minidom.parseString(hostInfo)
	hostList=dom.getElementsByTagName('host')
	
	if len(hostList)==0:
		print "Error, host not found"
		return

	result=[('ID','host name','status')+optionList]
	
	for element in hostList:
		currentTuple=(
			getValue(element,'host','hostID'),
			getValue(element,'host','hostName'),
			converter.hostStatus[getValue(element,'status')],
		)
		if '-a' in argv:
			currentTuple+=(converter.hostActivity[getValue(element,'activity')],)
		if '-i' in argv:
			currentTuple+=(getValue(element,'IP'),)
		
		if '-s' in argv:
			#get list of string that make many line
			allFunction=[]
			
			if getValue(element,'isGlobalController')!='0':
				allFunction.append(converter.hostFunction[getValue(element,'isGlobalController')]+' Global Controller')
			if getValue(element,'isInformationServer')!='0':
				allFunction.append(converter.hostFunction[getValue(element,'isInformationServer')]+' Information Server')
			if getValue(element,'isNFSServer')!='0':
				allFunction.append(converter.hostFunction[getValue(element,'isNFSServer')]+' NFS Server')
			if getValue(element,'isCA')!='0':
				allFunction.append(converter.hostFunction[getValue(element,'isCA')]+' CA')

			if allFunction==[]:
				allFunction.append('None')
					
			currentTuple+=(allFunction[0],)
			result.append(currentTuple)
			
			if len(allFunction)>1:	#must add next line
				allFunction.remove(allFunction[0])
				for eachFunction in allFunction:
					result.append(('',)*(len(result[0])-1) + (eachFunction,))
				
		else:
			result.append(currentTuple)
		
	print getTable(result)

def hostadd(argv,param):
	'''Add new host to current cloud;
	Usage:
		hostadd HOSTNAME MACADDRESS IPADDRESS 
	'''
	if len(argv)==3:
		try:
			hostName=argv[0]
			macAddress=str(network.MACAddr(argv[1]))
			ipAddress=str(network.IPAddr(argv[2]))
		except:
			print "invalid MAC address or IP address"
			return
	else:
		print param[3][getMyFunctionName()].__doc__
		return
	
	finishInfo=requestAndWait(param[0],param[1],'/host/add?hostName=%s&MACAddress=%s&IPAddress=%s'%(hostName,macAddress,ipAddress))
	dom = minidom.parseString(finishInfo)
	hostID=getValue(dom,'host','hostID')
	if hostID==None:
		print 'Adding error:',getValue(dom,'finishMessage')
	else:
		print "Finish, hostID="+hostID

def hostremove(argv,param):
	'''Remove a specific host from this cloud system;
	Usage
		hostremove HOST_ID
	'''
	if len(argv)==1:
		try:
			hostID=int(argv[0])
		except:
			print "hostID must be integer"
			return
	else:
		print param[3][getMyFunctionName()].__doc__
		return
	
	finishInfo=requestAndWait(param[0],param[1],'/host/remove?hostID=%s'%(str(hostID)))
	
	if isinstance(finishInfo, (dict,)):
		return finishInfo
	
	dom = minidom.parseString(finishInfo)
	result=getValue(dom,'finishStatus')
	if result=='1':
		pass
	else:
		print 'Error:',getValue(dom,'finishMessage')

def hoststandby(argv,param):
	'''Standby a specific host;
	Usage
		hoststandby HOST_ID
	'''
	mode='standby'
	if len(argv)==1:
		try:
			hostID=int(argv[0])
		except:
			print "hostID must be integer"
			return
	else:
		print param[3][getMyFunctionName()].__doc__
		return
	
	finishInfo=requestAndWait(param[0],param[1],'/host/close?hostID=%s&mode=%s'%(str(hostID),mode))
	
	if isinstance(finishInfo, (dict,)):
		return finishInfo
	
	dom = minidom.parseString(finishInfo)
	result=getValue(dom,'finishStatus')
	if result=='1':
		pass
	else:
		print 'Error:',getValue(dom,'finishMessage')

def hosthibernate(argv,param):
	'''Hibernate a specific host;
	Usage
		hosthibernate HOST_ID
	'''
	mode='hibernate'
	if len(argv)==1:
		try:
			hostID=int(argv[0])
		except:
			print "hostID must be integer"
			return
	else:
		print param[3][getMyFunctionName()].__doc__
		return
	
	finishInfo=requestAndWait(param[0],param[1],'/host/close?hostID=%s&mode=%s'%(str(hostID),mode))
	dom = minidom.parseString(finishInfo)
	
	if isinstance(finishInfo, (dict,)):
		return finishInfo
	
	result=getValue(dom,'finishStatus')
	if result=='1':
		pass
	else:
		print 'Error:',getValue(dom,'finishMessage')

def hostshutdown(argv,param):
	'''Shutdown a specific host;
	Usage
		hostshutdown HOST_ID
	'''
	mode='shutdown'
	if len(argv)==1:
		try:
			hostID=int(argv[0])
		except:
			print "hostID must be integer"
			return
	else:
		print param[3][getMyFunctionName()].__doc__
		return
	
	finishInfo=requestAndWait(param[0],param[1],'/host/close?hostID=%s&mode=%s'%(str(hostID),mode))
	dom = minidom.parseString(finishInfo)
	
	if isinstance(finishInfo, (dict,)):
		return finishInfo
	
	result=getValue(dom,'finishStatus')
	if result=='1':
		pass
	else:
		print 'Error:',getValue(dom,'finishMessage')

def hostwakeup(argv,param):
	'''Turn on or wake up a specific host;
	Usage
		hostwakeup HOST_ID
	'''
	if len(argv)==1:
		try:
			hostID=int(argv[0])
		except:
			print "hostID must be integer"
			return
	else:
		print param[3][getMyFunctionName()].__doc__
		return
	
	finishInfo=requestAndWait(param[0],param[1],'/host/wakeup?hostID=%s'%(str(hostID)))
	dom = minidom.parseString(finishInfo)
	result=getValue(dom,'finishStatus')
	if result=='1':
		pass
	else:
		print 'Error:',getValue(dom,'finishMessage')

def hostinfo(argv,param):
	'''Show information of a specific host;
	Usage
		hostinfo HOST_ID
	'''
	if len(argv)==1:
		try:
			hostID=int(argv[0])
		except:
			print "hostID must be integer."
			return
	else:
		print param[3][getMyFunctionName()].__doc__
		return
	
	hostInfo=requestTo(param[0],param[1],'/host/getInfo?hostID=%s'%(str(hostID)))
	dom = minidom.parseString(hostInfo)
	
	if getValue(dom,'host','hostID')==None:
		print "Host not found."
		return

	result=[('key','value')]
	result+=[
		('host ID',getValue(dom,'host','hostID')),
		('host name',getValue(dom,'host','hostName')),
		('status',converter.hostStatus[getValue(dom,'status')]),
		('activity',converter.hostActivity[getValue(dom,'activity')]),
		('MAC Address',getValue(dom,'MAC')),
		('IP Address',getValue(dom,'IP')),
		('Memory size',getValue(dom,'size')),
		('CPU model',getValue(dom,'model')),
		('CPU core',getValue(dom,'number')),
		('CPU speed(MHz)',getValue(dom,'frequency')),
		('Guest Holder',converter.hostIsHost[getValue(dom,'isHost')]),
		('Global Controller',converter.hostFunction[getValue(dom,'isGlobalController')]),
		('Information Server',converter.hostFunction[getValue(dom,'isInformationServer')]),
		('NFS Server',converter.hostFunction[getValue(dom,'isNFSServer')]),
		('CA Server',converter.hostFunction[getValue(dom,'isCA')])
	]
	print getTable(result)



def hostmonitor(argv,param):
	'''Show current status of a specific host;
	Usage
		hostmonitor HOST_ID
	'''
	if len(argv)==1:
		try:
			hostID=int(argv[0])
		except:
			print "hostID must be integer"
			return
	else:
		print param[3][getMyFunctionName()].__doc__
		return
	
	panel=MonitorPanel()

	firstRound=True
	while True:
		hostInfo=requestTo(param[0],param[1],'/host/getAllCurrentInfo?hostID=%s'%(str(hostID)))
		dom = minidom.parseString(hostInfo)
		if firstRound:
			if getValue(dom,'host','hostID')==None:
				print "Host not found."
				return
			if getValue(dom,'host','polling')=='error':
				print "Host is not running."
				return
			PressKeyThread().start()
			firstRound=False

		result=[('host ID: '+getValue(dom,'host','hostID'),' '*30)]
		result+=[('CPU Usage',str(getValue(dom,'average'))+'%')]
		
		try:
			memTotal=int(getValue(dom,'memTotal'))
			memFree=int(getValue(dom,'memFree'))
			result+=[('free memory space','%d/%d %.2f%%'%(memFree,memTotal,memFree*100.0/memTotal))]
		except:
			result+=[('free memory space','None')]
		
		result+=[('network transmit rate',str(getValue(dom,'tx'))+' Kbps')]
		result+=[('network recieve rate',str(getValue(dom,'rx'))+' Kbps')]

		try:
			storageFree=int(getValue(dom,'free'))
			storageCapacity=int(getValue(dom,'capacity'))
			result+=[('free storage space','%d/%d %.2f%%'%(storageFree,storageCapacity,storageFree*100.0/storageCapacity))]
		except:
			result+=[('free storage space','None')]

		panel.update(getTable(result))

		if len(threading.enumerate())==1:
			break
		
		time.sleep(1)
	
	print ''
		
def guestlist(argv,param):
	'''List ID, name and status of all guest;
	'''
	guestInfo=requestTo(param[0],param[1],'/guest/getState')
	dom = minidom.parseString(guestInfo)
	guestList=dom.getElementsByTagName('guest')
	
	if len(guestList)==0:
		print "No guest found."
		return

	result=[('ID','guest name','status','activity')]
	
	for element in guestList:
		
		result.append((
			getValue(element,'guest','guestID'),
			getValue(element,'guest','guestName'),
			converter.getSimpleGuestStatus(getValue(element,'status'),getValue(element,'runningState')),
			converter.guestActivity[getValue(element,'activity')]
		))
		
	print getTable(result)

def guestcreate(argv,param):
	'''Create new guest;
	Usage:
		guestcreate TEMPLATE_ID GUEST_NAME MEMORY_SIZE(MB) CPU 
	'''
	if len(argv)==4:
		try:
			templateID=int(argv[0])
			guestName=argv[1]
			memSize=int(argv[2])
			CPU=int(argv[3])
		except:
			print "invalid data"
			return
	else:
		print param[3][getMyFunctionName()].__doc__
		return
	
	finishInfo=requestAndWait(param[0],param[1],'/guest/create?guestName=%s&templateID=%s&memory=%s&vCPU=%s'%(guestName,str(templateID),str(memSize),str(CPU)))
	dom = minidom.parseString(finishInfo)
	guestID=getValue(dom,'guest','guestID')
	if guestID==None:
		print 'Creating error:',getValue(dom,'finishMessage')
	else:
		print "Finish, guestID="+guestID

def guestduplicate(argv,param):
	'''Create new guest by cloning from created guest(source guest must be shutoff);
	Usage:
		guestduplicate SOURCE_GUEST_ID GUEST_NAME
	'''
	if len(argv)==2:
		try:
			sourceGuestID=int(argv[0])
			guestName=argv[1]
		except:
			print "invalid data"
			return
	else:
		print param[3][getMyFunctionName()].__doc__
		return
	
	finishInfo=requestAndWait(param[0],param[1],'/guest/duplicate?guestName=%s&sourceGuestID=%s'%(guestName,str(sourceGuestID)))
	dom = minidom.parseString(finishInfo)
	guestID=getValue(dom,'guest','guestID')
	if guestID==None:
		print 'Creating error:',getValue(dom,'finishMessage')
	else:
		print "Finish, guestID="+guestID

def guestdestroy(argv,param):
	'''Destroy guest;
	Usage:
		guestdestroy GUEST_ID 
	'''
	if len(argv)==1:
		try:
			guestID=int(argv[0])
		except:
			print "invalid data"
			return
	else:
		print param[3][getMyFunctionName()].__doc__
		return
	
	finishInfo=requestAndWait(param[0],param[1],'/guest/destroy?guestID=%s'%(str(guestID)))
	dom = minidom.parseString(finishInfo)
	result=getValue(dom,'finishStatus')
	if result=='1':
		print 'Success.'
	else:
		print 'Error:',getValue(dom,'finishMessage')

def gueststart(argv,param):
	'''Boot up guest;
	Usage:
		gueststart GUEST_ID [TARGET_HOST_ID]
	'''
	if len(argv) in [1,2]:
		try:
			guestID=int(argv[0])
			if len(argv)==2:
				targetHostID=int(argv[1])
				optional="&targetHostID=%s"%(str(targetHostID))
			else:
				targetHostID=None
				optional=''
		except:
			print "invalid data"
			return
	else:
		print param[3][getMyFunctionName()].__doc__
		return
	
	finishInfo=requestAndWait(param[0],param[1],('/guest/start?guestID=%s'%(str(guestID)))+optional)
	dom = minidom.parseString(finishInfo)
	result=getValue(dom,'finishStatus')
	if result=='1':
		print 'Success, target host ID='+getValue(dom,'hostID')
	else:
		print 'Error:',getValue(dom,'finishMessage')

def guestforceoff(argv,param):
	'''Force shuting off a guest;
	Usage:
		guestforceoff GUEST_ID 
	'''
	if len(argv)==1:
		try:
			guestID=int(argv[0])
		except:
			print "invalid data"
			return
	else:
		print param[3][getMyFunctionName()].__doc__
		return
	
	finishInfo=requestAndWait(param[0],param[1],'/guest/forceOff?guestID=%s'%(str(guestID)))
	dom = minidom.parseString(finishInfo)
	result=getValue(dom,'finishStatus')
	if result=='1':
		print 'Success.'
	else:
		print 'Error:',getValue(dom,'finishMessage')

def guestpause(argv,param):
	'''Pause guest;
	Usage:
		guestpause GUEST_ID 
	'''
	if len(argv)==1:
		try:
			guestID=int(argv[0])
		except:
			print "invalid data"
			return
	else:
		print param[3][getMyFunctionName()].__doc__
		return
	
	finishInfo=requestAndWait(param[0],param[1],'/guest/suspend?guestID=%s'%(str(guestID)))
	dom = minidom.parseString(finishInfo)
	result=getValue(dom,'finishStatus')
	if result=='1':
		print 'Success.'
	else:
		print 'Error:',getValue(dom,'finishMessage')

def guestresume(argv,param):
	'''Resume guest from paused state;
	Usage:
		guestresume GUEST_ID 
	'''
	if len(argv)==1:
		try:
			guestID=int(argv[0])
		except:
			print "invalid data"
			return
	else:
		print param[3][getMyFunctionName()].__doc__
		return
	
	finishInfo=requestAndWait(param[0],param[1],'/guest/resume?guestID=%s'%(str(guestID)))
	dom = minidom.parseString(finishInfo)
	result=getValue(dom,'finishStatus')
	if result=='1':
		print 'Success.'
	else:
		print 'Error:',getValue(dom,'finishMessage')

def guestsave(argv,param):
	'''Save guest to disk(like hibernate);
	Usage:
		guestsave GUEST_ID 
	'''
	if len(argv)==1:
		try:
			guestID=int(argv[0])
		except:
			print "invalid data"
			return
	else:
		print param[3][getMyFunctionName()].__doc__
		return
	
	finishInfo=requestAndWait(param[0],param[1],'/guest/save?guestID=%s'%(str(guestID)))
	dom = minidom.parseString(finishInfo)
	result=getValue(dom,'finishStatus')
	if result=='1':
		print 'Success.'
	else:
		print 'Error:',getValue(dom,'finishMessage')

def guestrestore(argv,param):
	'''Restore guest from saved state;
	Usage:
		guestrestore GUEST_ID [TARGET_HOST_ID]
	'''
	if len(argv) in [1,2]:
		try:
			guestID=int(argv[0])
			if len(argv)==2:
				targetHostID=int(argv[1])
				optional="&targetHostID=%s"%(str(targetHostID))
			else:
				targetHostID=None
				optional=''
		except:
			print "invalid data"
			return
	else:
		print param[3][getMyFunctionName()].__doc__
		return
	
	finishInfo=requestAndWait(param[0],param[1],('/guest/restore?guestID=%s'%(str(guestID)))+optional)
	dom = minidom.parseString(finishInfo)
	result=getValue(dom,'finishStatus')
	if result=='1':
		print 'Success, target host ID='+getValue(dom,'hostID')
	else:
		print 'Error:',getValue(dom,'finishMessage')

def guestmigrate(argv,param):
	'''Migrate a guest to target host;
	Usage:
		guestmigrate GUEST_ID TARGET_HOST_ID
	'''
	if len(argv)==2:
		try:
			guestID=int(argv[0])
			targetHostID=int(argv[1])
		except:
			print "invalid data"
			return
	else:
		print param[3][getMyFunctionName()].__doc__
		return
	
	finishInfo=requestAndWait(param[0],param[1],'/guest/migrate?guestID=%s&targetHostID=%s'%(str(guestID),str(targetHostID)))
	dom = minidom.parseString(finishInfo)
	result=getValue(dom,'finishStatus')
	if result=='1':
		print 'Success.'
	else:
		print 'Error:',getValue(dom,'finishMessage')

def guestinfo(argv,param):
	'''Show information of a specific guest;
	Usage
		guestinfo GUEST_ID
	'''
	if len(argv)==1:
		try:
			guestID=int(argv[0])
		except:
			print "guestID must be integer."
			return
	else:
		print param[3][getMyFunctionName()].__doc__
		return
	
	guestInfo=requestTo(param[0],param[1],'/guest/getInfo?guestID=%s'%(str(guestID)))
	guestState=requestTo(param[0],param[1],'/guest/getState?guestID=%s'%(str(guestID)))
	dom = minidom.parseString(guestInfo)

	if getValue(dom,'guest','guestID')==None:
		print 'Guest not found.'
		return

	result=[('key','value')]
	result+=[
		('guest ID',getValue(dom,'guest','guestID')),
		('lastest host ID',getValue(dom,'lastHostID')),
		('guest name',getValue(dom,'guest','guestName')),
		('MAC Address',getValue(dom,'MAC')),
		('IP Address',getValue(dom,'IP')),
		('template ID',getValue(dom,'templateID')),
		('memory size',getValue(dom,'memory')),
		('virtual CPU core',getValue(dom,'vCPU')),
		('inboundBandwidth',getValue(dom,'inbound')),
		('outboundBandwidth',getValue(dom,'outbound'))
	]
	dom = minidom.parseString(guestState)
	result+=[
		('status',converter.getSimpleGuestStatus(getValue(dom,'status'),getValue(dom,'runningState'))),
		('activity',converter.guestActivity[getValue(dom,'activity')])
	]
	print getTable(result)

def guestmonitor(argv,param):
	'''Show current status of a specific guest;
	Usage
		guestmonitor GUEST_ID
	'''
	if len(argv)==1:
		try:
			guestID=int(argv[0])
		except:
			print "guestID must be integer"
			return
	else:
		print param[3][getMyFunctionName()].__doc__
		return
	
	panel=MonitorPanel()
	
	firstRound=True
	while True:
		guestInfo=requestTo(param[0],param[1],'/guest/getCustomizedInfo?guestIDs=%s&cpu=1&memory=1&network=1&io=1'%(str(guestID)))
		dom = minidom.parseString(guestInfo)
		if firstRound:
			if getValue(dom,'guest','guestID')==None:
				print "Guest not found"
				return
			elif getValue(dom,'guest','polling')=='error':
				print "Guest is not running"
				return
			PressKeyThread().start()
			firstRound=False

		result=[('guest ID: '+getValue(dom,'guest','guestID'),' '*30)]
		result+=[('CPU Usage',getValue(dom,'average')+'%')]
		result+=[('CPU Time',getValue(dom,'cpuTime')+'ns')]

		memTotal=int(getValue(dom,'memTotal'))
		memUse=int(getValue(dom,'memUse'))
		result+=[('used memory space','%d/%d %.2f%%'%(memUse,memTotal,memUse*100.0/memTotal))]
		
		networkDom=dom.getElementsByTagName('networkInfo')[0]
		result+=[('network transmit rate',getValue(networkDom,'tx')+' bps')]
		result+=[('network recieve rate',getValue(networkDom,'rx')+' bps')]
		
		ioDom=dom.getElementsByTagName('ioInfo')[0]
		result+=[('io read rate',getValue(ioDom,'rx')+' bps')]
		result+=[('io write rate',getValue(ioDom,'wx')+' bps')]	
		
		panel.update(getTable(result))

		if len(threading.enumerate())==1:
			break
		
		time.sleep(1)
	
	print ''

def templatelist(argv,param):
	'''List ID, OS and size of all template;
	'''
	templateInfo=requestTo(param[0],param[1],'/template/getInfo')
	dom = minidom.parseString(templateInfo)
	templateList=dom.getElementsByTagName('template')
	
	if len(templateList)==0:
		print "Error, template not found"
		return

	result=[('ID','OS','size')]
	
	for element in templateList:
		result.append((
			getValue(element,'template','templateID'),
			getValue(element,'OS'),
			getValue(element,'size')
		))
		
	print getTable(result)

def templateinfo(argv,param):
	'''Show information of specific template;
	Usage
		templateinfo TEMPLATE_ID
	'''
	if len(argv)==1:
		try:
			templateID=int(argv[0])
		except:
			print "templateID must be integer"
			return
	else:
		print param[3][getMyFunctionName()].__doc__
		return

	templateInfo=requestTo(param[0],param[1],'/template/getInfo?templateID=%s'%(str(templateID)))
	dom = minidom.parseString(templateInfo)
	
	if getValue(dom,'template','templateID')==None:
		print 'Template not found.'
		return

	result=[('key','value')]
	result+=[
	('template ID',getValue(dom,'template','templateID')),
	('OS',getValue(dom,'OS')),
	('minimum memory',getValue(dom,'minimumMemory')),
	('maximum memory',getValue(dom,'maximumMemory')),
	('activity',converter.templateActivity[getValue(dom,'activity')])
	]
	key='description'
	desc=getValue(dom,'description').replace('\n',' ')
	desc_width=50
	i=0
	while i<len(desc):
		result+=[(key,desc[i:i+desc_width])]
		key=''
		i+=desc_width

	print getTable(result)

def templatecreatefromguest(argv,param):
	'''Create new template by cloning from created guest(source guest must be shutoff);
	Usage:
		templatecreatefromguest SOURCE_GUEST_ID DESCRIPTION
	'''
	if len(argv)>1:
		try:
			sourceGuestID=int(argv[0])
			description=' '.join(argv[1:])
		except:
			print "invalid data"
			return
	else:
		print param[3][getMyFunctionName()].__doc__
		return
	
	finishInfo=requestAndWait(param[0],param[1],'/template/createFromGuest?sourceGuestID=%s&description=%s'%(str(sourceGuestID),description))
	dom = minidom.parseString(finishInfo)
	templateID=getValue(dom,'template','templateID')
	if templateID==None:
		print 'Creating error:',getValue(dom,'finishMessage')
	else:
		print "Finish, templateID="+templateID

def templateadd(argv,param):
	'''Add new template that already have image file in storage path of NFS server;
	Usage:
		templateadd FILE_NAME MINIMUM_MEMORY MAXIMUM_MEMORY
	'''
	if len(argv)==3:
		try:
			fileName=argv[0]
			minimumMemory=int(argv[1])
			maximumMemory=int(argv[2])
			#get more data
			OS=raw_input("OS:")
			description=raw_input("description:")
		except:
			print "invalid data"
			return
	else:
		print param[3][getMyFunctionName()].__doc__
		return
	
	finishInfo=requestTo(param[0],param[1],'/template/add?fileName=%s&OS=%s&description=%s&minimumMemory=%s&maximumMemory=%s'%(fileName,OS,description,minimumMemory,maximumMemory))

	dom = minidom.parseString(finishInfo)
	templateID=getValue(dom,'template','templateID')
	if templateID==None:
		print 'Creating error:',getValue(dom,'message')
	else:
		print "Finish, templateID="+templateID

def templateremove(argv,param):
	'''Remove a template permanently;
	Usage:
		templateremove TEMPLATE_ID
	'''
	if len(argv)==1:
		try:
			templateID=int(argv[0])
		except:
			print "invalid data"
			return
	else:
		print param[3][getMyFunctionName()].__doc__
		return
	
	finishInfo=requestAndWait(param[0],param[1],'/template/remove?templateID=%s'%(str(templateID)))
	dom = minidom.parseString(finishInfo)
	result=getValue(dom,'finishStatus')
	if result=='1':
		print 'Success.'
	else:
		print 'Error:',getValue(dom,'finishMessage')

def servicemigrate(argv,param):
	'''Migrate global controller service(webapi,dhcp server) to target host;
	Usage:
		servicemigrate SERVICE_NAME TARGET_HOST_ID
		SERVICE_NAME=global		is migration of webapi,dhcp server
		SERVICE_NAME=database	is migration of database
		SERVICE_NAME=ca			is migration of certificate authority
		SERVICE_NAME=nfs		is migration of nfs server
	'''

	if len(argv)==2:
		try:
			targetService=argv[0]
			if targetService not in ['global','database','ca','nfs']:
				print "invalid SERVICE_NAME"
				return
			targetHostID=int(argv[1])
		except:
			print "invalid data."
			return
	else:
		print param[3][getMyFunctionName()].__doc__
		return
	
	if targetService=='global':
		commandString='migrateGlobalController'
		
		#must get ip address of targetHostID from /host/getInfo
		hostInfo=requestTo(param[0],param[1],'/host/getInfo?hostID=%s'%(str(targetHostID)))
		dom = minidom.parseString(hostInfo)
		backupIP=getValue(dom,'IP')

	elif targetService=='database':
		commandString='migrateInformationService'
	elif targetService=='ca':
		commandString='migrateCA'
	elif targetService=='nfs':
		commandString='migrateNFS'

	if commandString!='migrateGlobalController':
		finishInfo=requestAndWait(param[0],param[1],'/cloud/%s?targetHostID=%s'%(commandString,str(targetHostID)))
		dom = minidom.parseString(finishInfo)
		result=getValue(dom,'finishStatus')
		if result=='1':
			print 'Success.'
		else:
			print 'Error:',getValue(dom,'finishMessage')
	
	else:
		finishInfo=requestAndWait(param[0],param[1],'/cloud/%s?targetHostID=%s'%(commandString,str(targetHostID)),backupIP=backupIP)
		dom = minidom.parseString(finishInfo)
		result=getValue(dom,'finishStatus')
		if result=='1':
			print 'Success.'
			return {
				'newIP':backupIP,
				#'newPort':port,
				}
		else:
			print 'Error:',getValue(dom,'finishMessage')

def setishost(argv,param):
	'''Set policy of host usage about guest hosting;
	Usage
		setishost HOST_ID VALUE
		VALUE
			0 : avoid this host from guest hosting
			1 : allow this host to host guests
	'''
	if len(argv)==2:
		try:
			hostID=int(argv[0])
		except:
			print "hostID must be integer"
			return
		
		if argv[1] in ['0','1']:
			val=argv[1]
			
			result=requestTo(param[0],param[1],'/host/setIsHost?hostID=%s&isHost=%s'%(hostID,val))
			if result==None:
				print 'setishost error'
				return
			
			dom = minidom.parseString(result)
			if getValue(dom,'response','type')=='success':
				print 'setishost success'
			else:
				print 'setishost error:',getValue(dom,'message')
			
			return

		else:
			print "invalid value"
			return
	else:
		print param[3][getMyFunctionName()].__doc__
		return
	
	