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

network.forceConfigToStaticFromCacheFile()

wakeList=[]

#wake up database
dbIP=cacheFile.getDatabaseIP()
dbMAC=cacheFile.getDatabaseMAC()
myMAC=network.getMyMACAddr()
wakeList.append(myMAC)

waker.wakeAndWait(dbMAC,dbIP)
if str(dbMAC) not in wakeList:
	wakeList.append(str(dbMAC))

#now i can say with that host
result=connection.socketCall(dbIP,setting.LOCAL_PORT,'wake_up_database',['{socket_connection}'])
if result!='OK':	#no, that is not real database
	if len(result)==17:
		#this should be recomended mac address
		subprocess.Popen(shlex.split("ether-wake -i br0 %s"%(str(result))))
		print "You may see a host that just opened automatically, try again at that host"
	else:
		print "Sorry, data on this host is obsolete. Try again at another host."
	sys.exit()

print "Bingo, you found the appropiate host to restore cloud."
print "Please wait..."

#now database is up
db = MySQLdb.connect(dbIP, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
cursor = db.cursor()

#wake up dhcp server
cursor.execute("SELECT `MACAddress`, `IPAddress` FROM `hosts` WHERE `isGlobalController`=1")
globalMAC,globalIP=cursor.fetchone()

if str(globalMAC) not in wakeList:
	waker.wakeAndWait(globalMAC,globalIP)
	wakeList.append(str(globalMAC))

result=connection.socketCall(globalIP,setting.LOCAL_PORT,'wake_up_dhcp',['{socket_connection}'])
if result!='OK':
	sys.exit()

#wake up ca
cursor.execute("SELECT `MACAddress`, `IPAddress` FROM `hosts` WHERE `isCA`=1")
caMAC,caIP=cursor.fetchone()

if str(caMAC) not in wakeList:
	waker.wakeAndWait(caMAC,caIP)
	wakeList.append(str(caMAC))

#wake up nfs server
cursor.execute("SELECT `MACAddress`, `IPAddress` FROM `hosts` WHERE `isStorageHolder`=1")
nfsMAC,nfsIP=cursor.fetchone()

if str(nfsMAC) not in wakeList:
	waker.wakeAndWait(nfsMAC,nfsIP)
	wakeList.append(str(nfsMAC))

result=connection.socketCall(nfsIP,setting.LOCAL_PORT,'wake_up_nfs',['{socket_connection}'])
if result!='OK':
	sys.exit()

#switch suspend host to shutoff host
cursor.execute("UPDATE `hosts` SET `status`=0 WHERE `status`=2")

#wake up host that have open status in database
cursor.execute("SELECT `MACAddress`, `IPAddress` FROM `hosts` WHERE `status`=1")
activeHost=cursor.fetchall()
for host in activeHost:
	if host[0] not in wakeList:
		waker.wakeAndWait(host[0],host[1])
		wakeList.append(host[0])

#destroy slave host info easily
cursor.execute("UPDATE `hosts` SET `isInformationServer`=0 WHERE `isInformationServer`=2")

#cursor.execute("SELECT `IPAddress` FROM `hosts` WHERE `isInformationServer`=2")
#slaveDB=cursor.fetchone()
#if slaveDB!=None:
#	result=connection.socketCall(slaveDB,setting.LOCAL_PORT,'destroy_slave_host_info')
#	if result!='OK':
#		print result
#		sys.exit()

#update_cloud_info + mount + start mkplanner
cursor.execute("SELECT `value` FROM `cloud_variables` WHERE `key`='subnet_mask'")
subnet=cursor.fetchone()[0]
cursor.execute("SELECT `value` FROM `cloud_variables` WHERE `key`='default_route'")
gateway=cursor.fetchone()[0]
cursor.execute("SELECT `value` FROM `cloud_variables` WHERE `key`='dns_servers'")
dns=cursor.fetchone()[0].split(',')[0]

cloudDataDict={
	'masterDB':str(dbIP),
	'masterDB_MAC':str(dbMAC),
	'slaveDB':'-',
	'globalController':str(globalIP),
	'network':{
		'subnet':subnet,
		'gateway':gateway,
		'dns':dns
	}
}
concludeDataString=json.dumps(cloudDataDict)
for host in activeHost:
	result=connection.socketCall(host[1], setting.LOCAL_PORT, 'update_cloud_info', ['{socket_connection}',concludeDataString,'nfs','planner'])
	if result!='OK':
		print host, "has problem to connect to information server or update something, please check installation."
		sys.exit()

#switch guest status from run and suspend to shutoff
cursor.execute("UPDATE `guests` SET `status`=0, `lastHostID`=NULL WHERE `status`=1")

db.close()

result=connection.socketCall(globalIP,setting.LOCAL_PORT,'wake_up_global_controller',['{socket_connection}'])
if result!='OK':
	sys.exit()

print "Finish restoring, now you can use this cloud."
