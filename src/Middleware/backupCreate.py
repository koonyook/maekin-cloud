#this script must be run on the host that be nfs server

# python backupCreate.py <backup directory path>

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
	print "python backupCreate.py <backup_directory_path>"
	sys.exit()
else:
	backupPath=sys.argv[1]

print "Checking..."

if not backupPath.endswith('/'):
	backupPath=backupPath+'/'

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

#save all guest
cursor.execute("SELECT `guestID` FROM `guests` WHERE `status`=1")
allGuest=cursor.fetchall()
for aGuest in allGuest:
	targetGuestID=aGuest[0]
	print 'Saving guest %s.'%(str(targetGuestID))
	finishInfo=requestAndWait(globalIP,setting.API_PORT,'/guest/save?guestID=%s'%(str(targetGuestID)))
	dom = minidom.parseString(finishInfo)
	result=getValue(dom,'finishStatus')
	if result=='1':
		pass
	else:
		print "Error saving guest."
		sys.exit()

#check required amount of storage
fileList=[]
cursor.execute("SELECT `volumeFileName`, `status` FROM `guests`")
allGuest=cursor.fetchall()
sumSpace=0
for element in allGuest:
	if element[1]==2:
		try:
			sumSpace+=os.path.getsize(setting.IMAGE_PATH+element[0])+os.path.getsize(setting.IMAGE_PATH+general.imgToSav(element[0]))
			fileList.append(element[0])
			fileList.append(general.imgToSav(element[0]))
		except os.error:
			print setting.IMAGE_PATH+element[0]+" or "+setting.IMAGE_PATH+general.imgToSav(element[0])+" not found."
			sys.exit()
	else:
		try:
			sumSpace+=os.path.getsize(setting.IMAGE_PATH+element[0])
			fileList.append(element[0])
		except os.error:
			print setting.IMAGE_PATH+element[0]+" not found."
			sys.exit()


result = subprocess.Popen(shlex.split('''mkdir -p %s'''%(backupPath)), stdout=subprocess.PIPE)
result.wait()

try:
	freeSpace=general.getFreeSpace(backupPath)
except:
	print packupPath+" not found."
	sys.exit()

if sumSpace+10000>freeSpace:
	print "need more space("+str(sumSpace+10000-freeSpace)+" more bytes needed)"
	sys.exit()

print "Start copying..."
#move data to backupPath
counter=0
for fileName in fileList:
	shutil.copy2(setting.IMAGE_PATH+fileName,backupPath+fileName)
	counter+=1
	print "progress (%d/%d)"%(counter,len(fileList))

#collect templates information
print "Getting hash of templates..."
cursor.execute("SELECT `templateID`, `fileName` FROM `templates`")
allTemplate=cursor.fetchall()
templateDict={}
for element in allTemplate:
	templateDict[element[0]]={
		'size':os.path.getsize(setting.TEMPLATE_PATH+element[1]),
		'hash':general.md5_for_file(setting.TEMPLATE_PATH+element[1]),
		'fileName':element[1]
	}

#save information to file (json format)
print "Getting guests' information..."
cursor.execute("SELECT `guestName`,`IPAddress`,`volumeFileName`,`templateID`,`status`,`memory`,`vCPU`,`inboundBandwidth`,`outboundBandwidth` FROM `guests` ORDER BY `guestID`")
allGuest=cursor.fetchall()
guestList=[]
for element in allGuest:
	guestList.append({
		'guestName':element[0],
		'oldIPAddress':element[1],
		'oldFileName':element[2],
		'oldTemplateID':element[3],
		'status':element[4],
		'memory':element[5],
		'vCPU':element[6],
		'inboundBandwidth':element[7],
		'outboundBandwidth':element[8]
	})

aFile=open(backupPath+setting.CLOUD_BACKUP_FILENAME,'w')
aFile.write(json.dumps({
	'templates':templateDict,
	'guests':guestList
}))

print "Finish backup, don't forget to add required template manually at destination cloud before install this backup."
