'''
normal mode (can restore later)
	python cloudStop.py

destroy mode (cannot restore later, all image will be deleted)
	python cloudStop.py destroy
'''
import setting

import sys
import time
import subprocess,shlex
from xml.dom import minidom

import MySQLdb
import json

from dhcp import dhcpController
from storage import nfsController

from util import connection,cacheFile,network,general,waker

from service import caService,dbService,nfsService,globalService
from shell.shellUtil import requestAndWait
from util.xmlUtil import getValue

if 'destroy' in sys.argv:
	destroyMode=True
else:
	destroyMode=False

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

#force off all guest
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
		sys.exit()

#umount and stop mkplanner in all active host
cursor.execute("SELECT `IPAddress` FROM `hosts` WHERE `status`=1")
allHost=cursor.fetchall()
for aHost in allHost:
	targetHostIP=aHost[0]
	result=connection.socketCall(targetHostIP,setting.LOCAL_PORT,'nfs_umount')
	if result!='OK':
		print result
		sys.exit()
	
	result=connection.socketCall(targetHostIP,setting.LOCAL_PORT,'stop_mkplanner')
	if result!='OK':
		print result
		sys.exit()

#stop nfs
print 'stop nfs server'
if destroyMode:
	optionList=['destroy']
else:
	optionList=[]

result=connection.socketCall(nfsIP,setting.LOCAL_PORT,'stop_nfs_server',optionList)
if result!='OK':
	print 'stop_nfs_server Error'
	sys.exit()

#stop mysqld
print 'stop database server'
result=connection.socketCall(dbIP,setting.LOCAL_PORT,'stop_database_server')
if result!='OK':
	print 'stop_database_server Error'
	sys.exit()

#stop mkapi and dhcpd
print 'stop dhcp server and global controller'
result=connection.socketCall(globalIP,setting.LOCAL_PORT,'suspend_global_controller_and_dhcp_server')
if result!='OK':
	print 'suspend_global_controller_and_dhcp_server error'
	sys.exit()

print "Stopping cloud complete."
