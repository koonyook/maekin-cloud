import setting

from util import network,cacheFile,ping,general
from util import shortcut
from info import dbController
from storage import nfsController

import os
import shutil
import time
import threading
import subprocess,shlex
import libvirt
import MySQLdb
import json
import traceback
from datetime import datetime
################################################
### this zone is called by global controller ###
################################################

def guest_update_status(argv):
	'''
	check current status of this guest and update in database
	'''
	UUID=argv[0]
	guestID=argv[1]

	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	
	cursor = db.cursor()
	cursor.execute('''SELECT 
	`status`, `activity`
	FROM `guests`
	WHERE `guestID`=%s;'''%(guestID))
	guestData=cursor.fetchone()
	if guestData==None:
		return 'Invalid guestID'

	lastStatus=guestData[0]
	lastActivity=guestData[1]
	
	if lastActivity!=0 :
		return json.dumps({'status':lastStatus,'runningState':0})
	if lastStatus==2 or lastStatus==0:
		return json.dumps({'status':lastStatus,'runningState':0})

	conn = libvirt.open(None)
	if conn == None:
		return 'Failed to open connection to the hypervisor'

	try:
		dom = conn.lookupByUUID(general.transformUUID(UUID))
	
		result= {'status':1,'runningState':dom.info()[0]}
	except:
		cursor.execute('''UPDATE `guests` SET `status`=0 WHERE `guestID`=%s'''%(guestID))
		result= {'status':0,'runningState':0}

	db.close()
	return json.dumps(result)

class LongCloning(threading.Thread):

	def setArguments(self,argv):
		self.sourceFileName = argv[0]
		self.targetFileName = argv[1]
		self.guestID        = argv[2]
		self.sourcePath		= argv[3]	# may be setting.TEMPLATE_PATH or setting.IMAGE_PATH

	def run(self):
		'''
		conn = libvirt.open(None)
		if conn == None:
			print 'Failed to open connection to the hypervisor'

		pool = conn.storagePoolLookupByName('default')
		volumeTemplateString = open(setting.MAIN_PATH+'libvirtTemplate/volume.xml','r').read()
		vol=pool.createXMLFrom(volumeTemplateString%{
			'IMAGE_FILE_NAME':self.targetFileName,
			'IMAGE_DIRECTORY_PATH':setting.TARGET_IMAGE_PATH
			},pool.storageVolLookupByName(self.sourceFileName),0)
		
		if vol==None:
			activity=-1
			print "Clone volume error"
		else:
			activity=0
			print "Clone volume success"
		'''
		global threadResult
		try:
			shutil.copy2(self.sourcePath+self.sourceFileName,setting.IMAGE_PATH+self.targetFileName)
			result = subprocess.Popen(shlex.split("chmod 777 %s"%(setting.IMAGE_PATH+self.targetFileName))) 
			result.wait()
			activity=0
			print "Clone volume success"
			
			threadResult="OK"

		except:
			threadResult=MySQLdb.escape_string(traceback.format_exc())
			activity=-1
			print "Clone volume error"

		#finish and tell database that you finish
		infoHost=cacheFile.getDatabaseIP()
		db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
		cursor = db.cursor()
		cursor.execute('''UPDATE `guests` SET `activity`=%s WHERE `guestID`=%s'''%(str(activity),self.guestID))
		db.close()
		

def guest_duplicate(argv):
	'''
	should be called at storageHolder only
	argv[0]=sourceFileName
	argv[1]=targetFileName
	argv[2]=guestID
	argv[3]=sourcePath

	argv[4]=taskID
	'''
	guestID=argv[2]
	taskID=argv[4]

	aThread=LongCloning()
	aThread.setArguments(argv)
	aThread.start()
	

	#main thread will see the size of new file and store progress in <finishMessage>
	currentFileSize=0
	targetFileSize=os.path.getsize(argv[3]+argv[0])
	while aThread.isAlive():
		try:
			currentFileSize=os.path.getsize(setting.IMAGE_PATH+argv[1])
		except os.error:
			currentFileSize=0
		
		message='<progress>%s</progress>\n<guest guestID="%s" />'%(str(currentFileSize*100.0/targetFileSize)+'%',str(guestID))
		shortcut.storeFinishMessage(taskID,message)
		print message
		aThread.join(5)		#update progress every five seconds
	
	return threadResult

def guest_create(argv):
	'''
	should be called at storageHolder only
	argv[0]=sourceFileName
	argv[1]=targetFileName
	argv[2]=guestID

	argv[3]=taskID
	'''
	sourceFileName=argv[0]
	targetFileName=argv[1]
	guestID=argv[2]
	taskID=argv[3]

	result = subprocess.Popen(shlex.split("qemu-img create -b %s -f qcow2 %s"%(setting.TARGET_TEMPLATE_PATH+sourceFileName,setting.IMAGE_PATH+targetFileName))) 
	result.wait()
	
	try:
		os.path.getsize(setting.IMAGE_PATH+targetFileName)
		result = subprocess.Popen(shlex.split("chmod 777 %s"%(setting.IMAGE_PATH+targetFileName))) 
		result.wait()
		activity=0
		print "Create new image success"	
	except:
		activity=-1
		print "Create new image error"

	#finish and tell database that you finish
	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	cursor.execute('''UPDATE `guests` SET `activity`=%s WHERE `guestID`=%s'''%(str(activity),guestID))
	db.close()
	
	if activity==0:
		return "OK"
	else:
		return "Create new image error"

'''
class Pinger(threading.Thread):
	def setArguments(self,guestID,guestIP):
		self.guestID=guestID
		self.guestIP=guestIP

	def run(self):
		
		result=False
		while result==False:
			time.sleep(2)
			result=ping.check(self.guestIP,2)

		#response in database (change status and activity)
		infoHost=cacheFile.getDatabaseIP()
		db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
		cursor = db.cursor()
		cursor.execute("UPDATE `guests` SET `status`=1, `activity`=0 WHERE `guestID`=%s"%(self.guestID))
		db.close()
'''		

def guest_start(argv):
	'''
	start guest and create a thread for ping this guest until success and tell in database
	'''
	guestID=argv[0]
	hostID=argv[1]
	
	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	cursor.execute('''SELECT 
	`guestID`, `guestName`, `MACAddress`, `volumeFileName`, `memory`, `vCPU`, `status`, `activity`, `IPAddress`, `inboundBandwidth`, `outboundBandwidth`
	FROM `guests`
	WHERE `guestID`=%s;'''%(guestID))
	guestData=cursor.fetchone()
	if guestData==None:
		return "Invalid guestID"
	
	bandwidthString=''
	if guestData[9]!=None:
		bandwidthString+="<inbound average='%s' peak='%s'/> "%(guestData[9]/2,guestData[9])
	if guestData[10]!=None:
		bandwidthString+="<outbound average='%s' peak='%s'/> "%(guestData[10]/2,guestData[10])
	
	
	cpuTuneString=''
	cpuSetString=''
	"""
	if guestData[5]==2 and guestData[1].startswith('a') and len(guestData[1])==3:
		cpuSetString='cpuset="0,1"'
		cpuTuneString='''
		<cputune>
			<vcpupin vcpu="0" cpuset="0"/>
			<vcpupin vcpu="1" cpuset="1"/>
			<quota>-1</quota>
		</cputune>
		'''
	"""

	try:
		conn = libvirt.open(None)
		if conn == None:
			return 'Failed to open connection to the hypervisor'

		domainTemplateString = open(setting.MAIN_PATH+'libvirtTemplate/domain.xml','r').read()
		guestDomain = conn.createXML(domainTemplateString%{
			'DOMAIN_NAME':guestData[1],
			'MEMORY':str(int(guestData[4])*1024),	#convert from MB to KB
			'VCPU':str(guestData[5]),
			'CPUSET':cpuSetString,
			'CPUTUNE':cpuTuneString,
			'IMAGE_PATH':setting.TARGET_IMAGE_PATH,
			'IMAGE_FILENAME':guestData[3],
			'MAC_ADDRESS':guestData[2],
			'BANDWIDTH':bandwidthString,
			},0)
		
		UUID=guestDomain.UUIDString().replace('-','')

		cursor.execute("UPDATE `guests` SET `activity`=2, `lastUUID`='%s', `lastHostID`=%s WHERE `guestID`=%s"%(UUID,hostID,guestData[0])) #I'm booting

	except:
		cursor.execute("UPDATE `guests` SET `activity`=0 WHERE `guestID`=%s"%(guestData[0]))
		db.close()
		return MySQLdb.escape_string(traceback.format_exc())

	'''
	aThread=Pinger()
	aThread.setArguments(guestData[0],guestData[8])
	aThread.start()

	#new version (blocked method)
	if argv[-1]=='{block}':
		aThread.join()
	'''
	start_ping_time=datetime.now()
	result=False
	while result==False:
		time.sleep(2)
		result=ping.check(guestData[8],2)
		pingtime=(datetime.now()-start_ping_time).seconds
		if pingtime>setting.MAXIMUM_BOOT_TIME:
			#shutoff current guest and update database
			try:
				guestDomain.destroy()
			except:
				pass
			cursor.execute("UPDATE `guests` SET `status`=0, `activity`=0 WHERE `guestID`=%s"%(guestData[0]))
			return "Boot time exceed"			

	#response in database (change status and activity)
	cursor.execute("UPDATE `guests` SET `status`=1, `activity`=0 WHERE `guestID`=%s"%(guestData[0]))
	db.close()

	return UUID

def guest_pause(argv):
	'''
	pause guest only
	'''
	UUID=argv[0]

	conn = libvirt.open(None)
	if conn == None:
		return 'Failed to open connection to the hypervisor'

	try:
		dom = conn.lookupByUUID(general.transformUUID(UUID))
	except:
		return 'Failed to find your domain'

	if dom.info()[0]==1 :
		try:
			dom.suspend()
		except:
			return 'Failed to suspend your domain'
		
		#nothing to do with database
		return str(3)	#return runningState    #dom.info()[0] should be 3

	else:
		return 'Cannot suspend this domain in this status(%d)'%(dom.info()[0])

def guest_resume(argv):
	'''
	resume guest only
	'''
	UUID=argv[0]

	conn = libvirt.open(None)
	if conn == None:
		return 'Failed to open connection to the hypervisor'

	try:
		dom = conn.lookupByUUID(general.transformUUID(UUID))
	except:
		return 'Failed to find your domain'

	if dom.info()[0]==3 :
		try:
			dom.resume()
		except:
			return 'Failed to resume your domain'
		
		#nothing to do with database
		return str(1)	#return runningState    #dom.info()[0] should be 1

	else:
		return 'Cannot suspend this domain in this status(%d)'%(dom.info()[0])

def guest_send_shutdown_signal(argv):
	'''
	only send shutdown signal to the guest
	'''
	UUID=argv[0]

	conn = libvirt.open(None)
	if conn == None:
		return 'Failed to open connection to the hypervisor'

	try:
		dom = conn.lookupByUUID(general.transformUUID(UUID))
	except:
		return 'Failed to find your domain'


	try:
		dom.shutdown()
	except:
		return 'Failed to send shutdown signal'
	
	return "OK"

def guest_send_reboot_signal(argv):
	'''
	only send reboot signal to the guest
	'''
	UUID=argv[0]

	conn = libvirt.open(None)
	if conn == None:
		return 'Failed to open connection to the hypervisor'

	try:
		dom = conn.lookupByUUID(general.transformUUID(UUID))
	except:
		return 'Failed to find your domain'


	try:
		dom.reboot()
	except:
		return 'Failed to send reboot signal'
	
	return "OK"
"""
class LongSaving(threading.Thread):

	def setArguments(self,dom,guestID,saveFileName):
		self.dom		  = dom
		self.guestID      = guestID
		self.saveFileName = saveFileName
		
	def run(self):
		result=self.dom.save(setting.TARGET_IMAGE_PATH+self.saveFileName)
		
		if result==-1:
			print "saving fail"
			return result

		#finish and tell database that you finish
		infoHost=cacheFile.getDatabaseIP()
		db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
		cursor = db.cursor()
		cursor.execute('''UPDATE `guests` SET `activity`=0, `status`=2 WHERE `guestID`=%s'''%(self.guestID))
		db.close()
"""
def guest_save(argv):
	'''
	save guest and update database
	'''
	UUID=argv[0]
	volumeFileName=argv[1]
	guestID=argv[2]

	saveFileName = volumeFileName.split('.')
	saveFileName[-1]='sav'
	saveFileName = '.'.join(saveFileName)

	conn = libvirt.open(None)
	if conn == None:
		return 'Failed to open connection to the hypervisor'

	try:
		dom = conn.lookupByUUID(general.transformUUID(UUID))
	except:
		return 'Failed to find your domain'

	runningState=dom.info()[0]
	if runningState==1 or runningState==3 :
		
		infoHost=cacheFile.getDatabaseIP()
		db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
		cursor = db.cursor()
		#I'm saving
		cursor.execute("UPDATE `guests` SET `activity`=3 WHERE `guestID`=%s"%(guestID))
		
		
		"""
		aThread=LongSaving()
		aThread.setArguments(dom,str(guestID),saveFileName)
		aThread.start()
		
		#new version (blocked method)
		if argv[-1]=='{block}':
			aThread.join()

		"""
		result=dom.save(setting.TARGET_IMAGE_PATH+saveFileName)
		
		if result==-1:
			print "saving fail"
			cursor.execute("UPDATE `guests` SET `activity`=-1 WHERE `guestID`=%s"%(str(guestID)))
			db.close()
			return result

		#finish and tell database that you finish
		cursor.execute("UPDATE `guests` SET `activity`=0, `status`=2 WHERE `guestID`=%s"%(str(guestID)))
		db.close()
		
		return "OK"

	else:
		return 'Cannot save your domain in this status(%d)'%(dom.info()[0])
"""
class LongRestoring(threading.Thread):

	def setArguments(self,conn,guestID,saveFileName,myHostID):
		self.conn		  = conn
		self.guestID      = guestID
		self.saveFileName = saveFileName
		self.myHostID	  =	myHostID
		
	def run(self):
		result = self.conn.restore(setting.TARGET_IMAGE_PATH+self.saveFileName)
		print 'restore result:',result
		if result==-1:
			print "restoring fail"
			return result

		#finish and tell database that you finish
		infoHost=cacheFile.getDatabaseIP()
		db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
		cursor = db.cursor()
		cursor.execute('''UPDATE `guests` SET `activity`=0, `status`=1, `lastHostID`=%s WHERE `guestID`=%s'''%(self.myHostID,self.guestID))
		db.close()

		try:
			os.remove(setting.TARGET_IMAGE_PATH+self.saveFileName)
		except:
			print "cannot remove .sav file completely"
"""
def guest_restore(argv):
	'''
	restore guest and update database
	'''
	guestID=argv[0]
	volumeFileName=argv[1]
	myHostID=argv[2]

	saveFileName = volumeFileName.split('.')
	saveFileName[-1]='sav'
	saveFileName = '.'.join(saveFileName)

	conn = libvirt.open(None)
	if conn == None:
		return 'Failed to open connection to the hypervisor'
	
	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	#I'm restoring
	cursor.execute("UPDATE `guests` SET `activity`=4 WHERE `guestID`=%s"%(guestID))
	
	"""
	aThread=LongRestoring()
	aThread.setArguments(conn,str(guestID),saveFileName,myHostID)
	aThread.start()
		
	#new version (blocked method)
	if argv[-1]=='{block}':
		aThread.join()
	"""
	result = conn.restore(setting.TARGET_IMAGE_PATH+saveFileName)
	if result==-1:
		print "restoring fail"
		cursor.execute("UPDATE `guests` SET `activity`=-1 WHERE `guestID`=%s"%(str(guestID)))
		db.close()
		return result

	#finish and tell database that you finish
	cursor.execute("UPDATE `guests` SET `activity`=0, `status`=1, `lastHostID`=%s WHERE `guestID`=%s"%(str(myHostID),str(guestID)))
	db.close()

	try:
		os.remove(setting.TARGET_IMAGE_PATH+saveFileName)
	except:
		print "cannot remove .sav file completely"

	return "OK"
	

def guest_force_off(argv):
	'''
	force clost a guest
	'''
	if 'macMode' in argv:
		guestMAC=argv[0]
	else:
		guestID=argv[0]
	
	UUID=argv[1]
	
	conn = libvirt.open(None)
	if conn == None:
		return 'Failed to open connection to the hypervisor'

	try:
		dom = conn.lookupByUUID(general.transformUUID(UUID))
	except:
		return 'Failed to find your domain'

#runningState=dom.info()[0]
#if runningState==1 or runningState==3 :
	try:
		dom.destroy()
	except:
		return "destroy error"

	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	if 'macMode' in argv:
		condition=" WHERE `MACAddress`='%s'"%(guestMAC)
	else:
		condition=" WHERE `guestID`=%s"%(guestID)
	
	cursor.execute("UPDATE `guests` SET `status`=0, `activity`=0, `lastUUID`=NULL, `lastHostID`=NULL"+condition)
	db.close()

	return "OK"	

#else:
#	return 'Cannot forced-off your domain in this runningState(%d)'%(dom.info()[0])

def guest_destroy(argv):
	'''
	destroy only
	'''
	UUID=argv[0]
	
	conn = libvirt.open(None)
	if conn == None:
		return 'Failed to open connection to the hypervisor'

	try:
		dom = conn.lookupByUUID(general.transformUUID(UUID))
	except:
		return 'Failed to find your domain'

	runningState=dom.info()[0]
	if runningState==1 or runningState==3 :
		try:
			dom.destroy()
		except:
			return "destroy error"

		return "OK"	

	else:
		return 'Cannot forced-off your domain in this runningState(%d)'%(dom.info()[0])

def guest_get_current_info(argv):
	'''
	all-in-one function
	'''
	UUID=argv[0]

	conn = libvirt.open(None)
	if conn == None:
		return 'Failed to open connection to the hypervisor'

	try:
		dom = conn.lookupByUUID(general.transformUUID(UUID))
	except:
		return 'Failed to find your domain'

	try:
		currentInfoString=open(setting.CURRENT_INFO_PATH+UUID+'.info','r').read()
	except:
		if ('cpu' in argv) or ('network' in argv) or ('io' in argv):
			return 'Current info of this domain is not ready now please try again in '+str(setting.GUEST_MONITOR_PERIOD)+' seconds.'
	
	currentInfo={}
	for element in currentInfoString.split('\n'):
		if element=='':
			continue
		temp=element.split(':')
		currentInfo[temp[0]]=temp[1]
	
	resultData={}
	if 'cpu' in argv:
		cpuInfo={
			'usage'		:currentInfo['CPU_USAGE'],
			'cpuTime'	:currentInfo['CPU_TIME']
		}
		resultData['cpuInfo']=cpuInfo
	
	if 'network' in argv:
		networkInfo={
			'rxRate'	:currentInfo['INTERFACE_RX_RATE'],
			'txRate'	:currentInfo['INTERFACE_TX_RATE'],
			'rxUsed'	:currentInfo['INTERFACE_RX_USED'],
			'txUsed'	:currentInfo['INTERFACE_TX_USED']
		}
		resultData['networkInfo']=networkInfo
	
	if 'io' in argv:
		ioInfo={
			'rxRate'	:currentInfo['DISK_READ_RATE'],
			'wxRate'	:currentInfo['DISK_WRITE_RATE'],
			'rxUsed'	:currentInfo['DISK_READ_USED'],
			'wxUsed'	:currentInfo['DISK_WRITE_USED']
		}
		resultData['ioInfo']=ioInfo

	if ('cpu' in argv) or ('network' in argv) or ('io' in argv):
		resultData['lastUpdate']=currentInfo['UPDATE']
	
	if 'memory' in argv:
		info=dom.info()

		memoryInfo={
			'usage'		:str(dom.info()[2]*1024),
			'total'		:str(dom.info()[1]*1024)
		}
		resultData['memoryInfo']=memoryInfo

	return json.dumps(resultData)

"""
class LongMigration(threading.Thread):

	def setArguments(self,guestID,dom,connDest,targetHostID):
		self.guestID      = guestID
		self.dom		  = dom
		self.connDest	= connDest
		self.targetHostID = targetHostID
		
	def run(self):
		global threadResult
		try:
			newDom=self.dom.migrate(self.connDest,libvirt.VIR_MIGRATE_LIVE,None,None,0)
			newUUID=newDom.UUIDString().replace('-','')
		
			#finish and tell database that you finish
			infoHost=cacheFile.getDatabaseIP()
			db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
			cursor = db.cursor()
			cursor.execute('''UPDATE `guests` SET `activity`=0, `status`=1, `lastUUID`='%s', `lastHostID`=%s WHERE `guestID`=%s'''%(newUUID,self.targetHostID,self.guestID))
			db.close()
			threadResult="OK"

		except:
			print "migration error"
			threadResult=MySQLdb.escape_string(traceback.format_exc())
			#fix activity back to None
			infoHost=cacheFile.getDatabaseIP()
			db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
			cursor = db.cursor()
			cursor.execute('''UPDATE `guests` SET `activity`=0, `status`=1 WHERE `guestID`=%s'''%(self.guestID))
			db.close()
"""

def guest_migrate(argv):
	
	guestID=argv[0]
	currentUUID=argv[1]
	currentHostIP=argv[2]
	targetHostIP=argv[3]
	targetHostID=argv[4]

	connSource = libvirt.open(None)
	if connSource == None:
		return 'Failed to open connection to the hypervisor'

	try:
		dom = connSource.lookupByUUID(general.transformUUID(currentUUID))
	except:
		return 'Failed to find your domain'

	try:
		destURI="qemu+tls://%s/system"%(targetHostIP)
		connDest = libvirt.open(destURI)
		if connDest==None:
			return 'Failed to find targetHost'
	except:
		return 'Failed to find targetHost'

	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	#I'm migrating
	cursor.execute("UPDATE `guests` SET `activity`=5 WHERE `guestID`=%s"%(guestID))
	
	"""
	aThread=LongMigration()
	aThread.setArguments(str(guestID),dom,connDest,targetHostID)
	aThread.start()
	
	if argv[-1]=='{block}':
		aThread.join()
		return threadResult	#value sent from thread
	"""
	try:
		#newDom=dom.migrate(connDest,libvirt.VIR_MIGRATE_LIVE,None,None,0)		#can use at magi, error at steam
		#newDom=dom.migrate(connDest,libvirt.VIR_MIGRATE_LIVE+libvirt.VIR_MIGRATE_PEER2PEER,None,destURI,0)		#error at steam, unknown at magi
		migrateURI="tcp:"+str(targetHostIP)
		newDom=dom.migrate(connDest,libvirt.VIR_MIGRATE_LIVE,None,migrateURI,0)

		newUUID=newDom.UUIDString().replace('-','')
	
		#finish and tell database that you finish
		cursor.execute('''UPDATE `guests` SET `activity`=0, `status`=1, `lastUUID`='%s', `lastHostID`=%s WHERE `guestID`=%s'''%(newUUID,targetHostID,str(guestID)))
		db.close()

	except:
		print "migration error"
		#fix activity back to None
		cursor.execute("UPDATE `guests` SET `activity`=0, `status`=1 WHERE `guestID`=%s"%(str(guestID)))
		db.close()

		return MySQLdb.escape_string(traceback.format_exc())

	return 'OK'  

def guest_scale_cpu(argv):
	'''
	scale cpu while it's running
	'''
	UUID=argv[0]
	vCPU=int(argv[1])

	conn = libvirt.open(None)
	if conn == None:
		return 'Failed to open connection to the hypervisor'

	try:
		dom = conn.lookupByUUID(general.transformUUID(UUID))
	except:
		return 'Failed to find your domain'

	if dom.info()[0]==1 :
		try:
			result=dom.setVcpus(vCPU)
			if result==0:	
				return "OK"
			elif result==-1:
				return 'Failed to scale cpu immediately'
			else:
				return 'this line should not be done'

		except:
			return 'Failed to scale cpu immediately'

	else:
		return 'Cannot scale cpu in this status(%d)'%(dom.info()[0])


def guest_scale_memory(argv):
	'''
	scale memory while it's running
	'''
	UUID=argv[0]
	memory=int(argv[1])

	conn = libvirt.open(None)
	if conn == None:
		return 'Failed to open connection to the hypervisor'

	try:
		dom = conn.lookupByUUID(general.transformUUID(UUID))
	except:
		return 'Failed to find your domain'

	if dom.info()[0]==1 :
		try:
			result=dom.setMaxMemory(memory*1024)
			result+=dom.setMemory(memory*1024)
			if result==0:	
				return "OK"
			elif result<0:
				return 'Failed to scale memory immediately'
			else:
				return 'this line should not be done'

		except:
			return 'Failed to scale memory immediately'

	else:
		return 'Cannot scale memory in this status(%d)'%(dom.info()[0])
