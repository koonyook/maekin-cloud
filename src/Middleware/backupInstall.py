#this script must be run on the host that be nfs server

# python backupInstall.py <backup directory path>

import setting

import sys,os
import time
import subprocess,shlex
from xml.dom import minidom
import shutil

import MySQLdb
import json

from dhcp import dhcpController
from storage import nfsController

from util import connection,cacheFile,network,general,waker

from service import caService,dbService,nfsService,globalService
from shell.shellUtil import requestAndWait
from util.xmlUtil import getValue

if len(sys.argv)!=2:
	print "python backupInstall.py <backup_directory_path>"
	sys.exit()
else:
	backupPath=sys.argv[1]

print "Checking available resource at this cloud..."

if not backupPath.endswith('/'):
	backupPath=backupPath+'/'

#read data from backupPath
aFile=open(backupPath+setting.CLOUD_BACKUP_FILENAME,'r')
backupData=json.loads(aFile.read())
aFile.close()

myIP=network.getMyIPAddr()

dbIP=cacheFile.getDatabaseIP()
db = MySQLdb.connect(dbIP, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
cursor = db.cursor()

#check host activity
cursor.execute("SELECT `hostID` FROM `hosts` WHERE `status`=1 and `activity`<>0")
if cursor.fetchone()!=None:
	print "There are host(s) doing some activity, please wait until they finish"
	sys.exit()

#check task queue
cursor.execute("SELECT `taskID` FROM `tasks` WHERE `status`<>2")
if cursor.fetchone()!=None:
	print "There are running task(s) in queue, please wait until they finish"
	sys.exit()

cursor.execute("SELECT `IPAddress` FROM `hosts` WHERE `isGlobalController`=1")
globalIP=cursor.fetchone()[0]
cursor.execute("SELECT `IPAddress` FROM `hosts` WHERE `isStorageHolder`=1")
nfsIP=cursor.fetchone()[0]

#check this host is nfs server
if str(myIP)!=str(nfsIP):
	print "This operation must be done at NFS Server only."
	sys.exit()

#check IP count
newGuestCount=len(backupData['guests'])
cursor.execute("SELECT COUNT(`IPAddress`) FROM `guest_ip_pool` WHERE `IPAddress` NOT IN (SELECT `IPAddress` FROM `guests`)")
restIPCount=cursor.fetchone()[0]

if restIPCount<newGuestCount:
	print "Do not have enough IP Address..."
	sys.exit()

#check templates hash and create matching
print "Getting hash of templates..."
cursor.execute("SELECT `templateID`, `fileName` FROM `templates`")
allTemplate=cursor.fetchall()
newTemplateDict={}
for element in allTemplate:
	templateSize=os.path.getsize(setting.TEMPLATE_PATH+element[1])
	templateHash=general.md5_for_file(setting.TEMPLATE_PATH+element[1])

	newTemplateDict[(templateSize,templateHash)]=element[0]

for oldTemplate in backupData['templates'].values():
	if (oldTemplate['size'],oldTemplate['hash']) in newTemplateDict.keys():
		pass
	else:
		print "template %s not found."%oldTemplate['fileName']
		sys.exit()

#check space on storage
spaceNeed=0
for aFile in os.listdir(backupPath):
	spaceNeed+=os.path.getsize(backupPath+aFile)

freeSpace=general.getFreeSpace(setting.STORAGE_PATH)

if spaceNeed>freeSpace:
	print "Do not have enough space ("+str(spaceNeed-freeSpace)+" more bytes needed)"
	sys.exit()

#add each guest to this system
for aGuest in backupData['guests']:
	
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
		print "Out of IP address"
		sys.exit()
	else:
		#select the minimum from freeIP
		newIP=freeIP[0][0]
		for eachIP in freeIP:
			if network.IPAddr(eachIP[0]).getProduct()<network.IPAddr(newIP).getProduct():
				newIP=eachIP[0]

	#find image file name
	usedImageNames=os.listdir(setting.IMAGE_PATH)
	oldName='.'.join(aGuest['oldFileName'].split('.')[0:-1])
	volumeFileName=oldName+'.img'
	count=2
	while volumeFileName in usedImageNames :
		volumeFileName=oldName+'('+str(count)+').img'
		count+=1
	
	if aGuest['inboundBandwidth']==None:
		inboundString="NULL"
	else:
		inboundString="'%s'"%(aGuest['inboundBandwidth'])

	if aGuest['outboundBandwidth']==None:
		outboundString="NULL"
	else:
		outboundString="'%s'"%(aGuest['outboundBandwidth'])
	
	oldTemplate=backupData['templates'][str(aGuest['oldTemplateID'])]
	newTemplateID=newTemplateDict[(oldTemplate['size'],oldTemplate['hash'])]

	cursor.execute('''
	INSERT INTO `guests` (`guestName`, `MACAddress`, `IPAddress`, `volumeFileName`, `templateID`, `status`,`activity`,`memory`,`vCPU`,`inboundBandwidth`,`outboundBandwidth`) VALUES
	('%(guestName)s', '%(MACAddress)s', '%(IPAddress)s', '%(volumeFileName)s', '%(templateID)s', '%(status)s','%(activity)s', '%(memory)s', '%(vCPU)s', %(inboundBandwidth)s, %(outboundBandwidth)s);
	'''%{
	'guestName':aGuest['guestName'],
	'MACAddress':newMAC,
	'IPAddress':newIP,
	'volumeFileName':volumeFileName,
	'templateID':newTemplateID,
	'status':0,		#aGuest['status'],
	'activity':0,		
	'memory':aGuest['memory'],
	'vCPU':aGuest['vCPU'],
	'inboundBandwidth':inboundString,
	'outboundBandwidth':outboundString
	})

	guestID=cursor.lastrowid
	
	#copy file and rename
	shutil.copy2(backupPath+aGuest['oldFileName'],setting.IMAGE_PATH+volumeFileName)
	
	#if aGuest['status']==2:
	#	shutil.copy2(backupPath+general.imgToSav(aGuest['oldFileName']),setting.IMAGE_PATH+general.imgToSav(volumeFileName))

	print "guestID:%s ( %s --> %s)"%(guestID,aGuest['oldIPAddress'],str(newIP))

#update dhcp from database
print "Update DHCP server..."
result=connection.socketCall(str(globalIP),setting.LOCAL_PORT,'dhcp_update_from_database',['{socket_connection}'])
if result!='OK':
	print "Error: "+result

db.close()
print "Finish."
