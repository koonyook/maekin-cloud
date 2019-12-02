import setting

import sys
import time
import subprocess,shlex
from xml.dom import minidom

import MySQLdb
import json

from dhcp import dhcpController
from util import network
from util import connection

from service import caService,dbService,nfsService,globalService

#find my MAC Address (*must know to get right ip address for set static ip first)
myMAC = network.getMyMACAddr()
myIP = None

inputFile=sys.argv[1]

#read data from startup.xml
print "reading data from",inputFile
dom = minidom.parseString(open(inputFile,'r').read())
try:
	cloudUUID = dom.getElementsByTagName('UUID')[0].childNodes[0].nodeValue
except:
	print 'UUID format is wrong'
	sys.exit()

try:
	cloudName = dom.getElementsByTagName('name')[0].childNodes[0].nodeValue
except:
	print 'name format is wrong'
	sys.exit()

try:
	guestPool = []
	for element in dom.getElementsByTagName('IP'):
		startNum=network.IPAddr(element.attributes['start'].value).getProduct()
		stopNum=network.IPAddr(element.attributes['stop'].value).getProduct()+1
		for num in range(startNum,stopNum):
			newIP = network.IPAddr(num)
			if not (newIP in guestPool):
				guestPool.append(newIP)
except:
	print 'guest IP address pool format is wrong'
	sys.exit()

try:
	temp = dom.getElementsByTagName('network')[0]
except:
	print 'network format is wrong'
	sys.exit()

try:
	networkID=network.IPAddr(temp.attributes['id'].value)
except:
	print 'network id format is wrong'
	sys.exit()

try:
	subnetMask=network.IPAddr(temp.attributes['mask'].value)
except:
	print 'mask format is wrong'
	sys.exit()

try:
	if temp.attributes['defaultRoute']!=None:
		defaultRoute=network.IPAddr(temp.attributes['defaultRoute'].value)
	else:
		defaultRoute=None
except:
	print 'defaultRoute format is wrong'
	sys.exit()

try:
	dns=[]
	for element in dom.getElementsByTagName('dnsAddress'):
		dns.append(network.IPAddr(element.attributes['IP'].value))
except:
	print 'dnsAddress format is wrong'
	sys.exit()

tmpHostNameList=[]
try:
	hostBindings=[]
	for element in dom.getElementsByTagName('Bind'):
		#append to hostBindings
		hostBindings.append((
			network.MACAddr(element.attributes['MAC'].value),
			network.IPAddr(element.attributes['IP'].value),
			element.attributes['hostName'].value
		))
		
		#check repeated hostName
		if element.attributes['hostName'].value in tmpHostNameList:
			print 'Error, repeated hostName.'
			sys.exit()
		else:
			tmpHostNameList.append(element.attributes['hostName'].value)

		#find what is my ip
		if str(myMAC)==element.attributes['MAC'].value:
			myIP=network.IPAddr(element.attributes['IP'].value)
			currentHost=hostBindings[-1]
except:
	print 'Bind format is wrong'
	sys.exit()

if myIP==None:
	print "MAC Address of this host not found in startup file, please check then startup again"
	sys.exit()

#bridgeMode of global controller must be static
if defaultRoute==None:
	usedGateway=None
else:
	usedGateway=str(defaultRoute)

if len(dns)==0:
	usedDns=None
else:
	usedDns=str(dns[0])

network.configToStatic(str(myIP), str(subnetMask), gateway=usedGateway, dns=usedDns, ifdown=True)

#setting via dhcpController( and start service in one command)
print "Config and starting DHCP Server..."
dhcpConfigResult=dhcpController.configAll(networkID,subnetMask,defaultRoute,dns,hostBindings)
if dhcpConfigResult==False:
	print "invalid DHCP setting"
	sys.exit()

#wait for a while (for sure that every host get ip from dhcp)
print "Wait for each host to get IP Address ..."
time.sleep(3)



#---------finish distribution of ip addresses to every host----------

#-------try to say hello with local controller of each daemon--------
#these two list for report to admin to known and can fix it later
while True:
	activeHost=[]
	failHost=[]
	for binding in hostBindings:
		targetIP=binding[1]
		result=connection.socketCall(targetIP, setting.LOCAL_PORT, 'hello')
		if result=='OK': #success
			activeHost.append(binding)
		else:
			failHost.append(binding)

	if len(activeHost)==len(hostBindings):
		print "That's great, all of host is active!"
		break
	elif len(activeHost)>0:
		print 'Active host list(%d):'%(len(activeHost))
		for element in activeHost:
			print '\t'+str(element)
		print 'Deactive host list(%d):'%(len(failHost))
		for element in failHost:
			print '\t'+str(element)
		
		print "Do you want to get more active hosts(y/n)?",
		ans=raw_input()
		if ans=='n':
			break
	elif activeHost==[]:
		print "cannot find any active host, please check...\n\t- startup.xml file\n\t- your network\n\t- local controller on each host"
		print "then, return to check active hosts again...",
		raw_input()
	print "OK, I am checking..."

#--------------------------------------------------------
#-------assign all HOSTNAME to all of host---------------
#--------------------------------------------------------
print "assigning hostname..."
for element in activeHost:
	result=connection.socketCall(element[1], setting.LOCAL_PORT, 'assign_hostname',[element[2]])
	if result!='OK':
		print infoHost, "has problem to be assigned hostName."
		sys.exit()

#finish assign hostname

defaultHostIndex=-1
for i in range(len(activeHost)):
	if str(activeHost[i][0])==str(myMAC):
		defaultHostIndex=i
		break

if defaultHostIndex==-1:
	print "This host has a problem, please check service on this host."
	sys.exit()

#--------------------------------------------------------------------
#-------choose an active host to be Information Server---------------
#--------------------------------------------------------------------
# take it easy now (choose first active binding)
print "Starting Database..."
infoHost=activeHost[defaultHostIndex]
result=connection.socketCall(infoHost[1], setting.LOCAL_PORT, 'you_are_information_server',['{socket_connection}',setting.DB_ROOT_PASSWORD,setting.DB_NAME])
if result!='OK':
	print infoHost, "has problem to be information server, please check installation."
	sys.exit()

#--------------------------------------------------------------------
#-------choose an active host to be NFS Server-----------------------
#----THEN command it to extract all template image to that shared directory (only that host)
#--------------------------------------------------------------------
print "Starting NFS Server..."
nfsHost=activeHost[defaultHostIndex]
hostIPList=[]
for element in hostBindings:
	hostIPList.append(str(element[1]))

result=connection.socketCall(nfsHost[1], setting.LOCAL_PORT, 'you_are_nfs_server',[json.dumps(hostIPList),"{socket_connection}"])
#print "this is result:",result
if result!='OK':
	print nfsHost, "has problem to be nfs server, please check installation."
	sys.exit()

#----------------------------------------------------
#-------choose an active host to be CA---------------	#only tell it to confirm and prepare the first step
#----------------------------------------------------
cerHost=activeHost[defaultHostIndex]


################################################
## save all important information to database ##
################################################

#db = MySQLdb.connect(str(infoHost[1]), 'root', setting.DB_ROOT_PASSWORD, setting.DB_NAME )
db = MySQLdb.connect(str(infoHost[1]), setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
cursor = db.cursor()
#update cloud_variables
params=[]
params.append((cloudUUID, 'cloud_uuid',))
params.append((cloudName, 'cloud_name',))
params.append((networkID, 'network_id',))
params.append((subnetMask, 'subnet_mask',))
params.append((defaultRoute, 'default_route',))
dnsStringList=[]
for element in dns:
	dnsStringList.append(str(element))
params.append((','.join(dnsStringList), 'dns_servers',))

for element in params:
	cursor.execute('''
		UPDATE  `cloud_variables` SET  `value` =  '%s' WHERE  `key` =  '%s';
	'''%element)

#clear table and insert guest_ip_pool
cursor.execute('''
	DELETE FROM `guest_ip_pool` WHERE 1;
''')

# example of string that will be produced is ('158.108.22.22'), ('158.108.33.33')
print guestPool
guestPoolStringList=[]
for element in guestPool:
	guestPoolStringList.append("('%s')"%(element))
cursor.execute('''
	INSERT INTO `guest_ip_pool` (`IPAddress`) VALUES %s;
'''%(", ".join(guestPoolStringList)))

#insert hosts
cursor.execute('''
	DELETE FROM `hosts` WHERE 1;
''')

hostStringList=[]
for element in hostBindings:
	if element in activeHost:
		isHost="1"
		status="1"
	else:
		isHost="1"
		status="0"
	
	if element==currentHost:
		isGlobalController="1"
	else:
		isGlobalController="0"
	
	if element==infoHost:
		isInformationServer="1"
	else:
		isInformationServer="0"
	
	if element==nfsHost:
		isStorageHolder="1"
	else:
		isStorageHolder="0"

	if element==cerHost:
		isCA="1"
	else:
		isCA="0"

	activity="0"
	
	#ask cpuCore and cpuSpeed (for use in future)
	hostSpec=connection.socketCall(str(element[1]), setting.LOCAL_PORT, 'ask_your_spec')
	hostSpec=json.loads(hostSpec)
	cpuCore=hostSpec['cpu']['number']
	cpuSpeed=hostSpec['cpu']['speed']

	hostStringList.append("('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')"%(element[2],element[0],element[1],isHost,isGlobalController,isInformationServer,isStorageHolder,isCA,status,activity,cpuCore,cpuSpeed))

cursor.execute('''
	INSERT INTO `hosts` (`hostName`, `MACAddress`, `IPAddress`, `isHost`, `isGlobalController`, `isInformationServer`, `isStorageHolder`,`isCA`, `status`, `activity`, `cpuCore`, `cpuSpeed`) VALUES %s;
'''%(", ".join(hostStringList)))

#clear guests
cursor.execute('''
	DELETE FROM `guests` WHERE 1;
''')

#insert templates (this should bring from startupTemplateQuery.sql file
cursor.execute('''
	DELETE FROM `templates` WHERE 1;
''')

#cursor.execute(open(setting.MAIN_PATH+'info/startupTemplateQuery.sql','r').read())		#this line will be done after copying of disk 2

db.close()



#--------------------------------------------------------------------
#---choose another active host to be Slave Information Server--------
#--------------------------------------------------------------------
# take it easy now (choose second active binding)
slaveInfoHost=None
""" #this comment for stable version (no slave db)
if len(activeHost)>1:
	for host in activeHost:
		if str(infoHost[1])!=str(host[1]): #check with ip
			slaveInfoHost=host
			break
	
	success=dbService.makeSlave(targetHostIP=str(slaveInfoHost[1]),masterHostIP=str(infoHost[1]))
	if not success:
		print infoHost, "has problem to create slave information server, please check installation."
		sys.exit()
"""

########################################################
######### Create Public Key Infrastructure #############
########################################################
print "Creating Public Key Infrastructure..."
print "(This action take much time. Please wait...)"
#tell ca server to do the first thing
result=connection.socketCall(cerHost[1], setting.LOCAL_PORT, 'you_are_ca_server')
if result!='OK':
	print cerHost, "has problem to be CA server, please check installation."
	sys.exit()

#tell every active host to update Certificate from CA (and restart libvirtd service)
for host in activeHost:
	print "wait for",host
	result=connection.socketCall(host[1], setting.LOCAL_PORT, 'update_pki', ['{socket_connection}',str(cerHost[1])])	#save load of database
	if result!='OK':
		print host, "has problem to update_pki, please check installation."
		sys.exit()

#every thing before this line cannot use nfs 

#************************************************
#*** update to cacheFile of every active host *** 
#************************************************
#(when they know they must mount and be NFS Client First)
#(then run mkplanner on every host)
print "Mounting shared storage at each host..."

if slaveInfoHost!=None:
	slaveInfoHostIP=str(slaveInfoHost[1])
else:
	slaveInfoHostIP='-'

cloudDataDict={
	'masterDB':str(infoHost[1]),
	'masterDB_MAC':str(infoHost[0]),
	'slaveDB':slaveInfoHostIP,
	'globalController':str(myIP),
	'network':{
		'subnet':str(subnetMask),
		'gateway':usedGateway,
		'dns':usedDns
	}
}
concludeDataString=json.dumps(cloudDataDict)
for host in activeHost:
	result=connection.socketCall(host[1], setting.LOCAL_PORT, 'update_cloud_info', ['{socket_connection}',concludeDataString,'nfs','planner'])
	if result!='OK':
		print host, "has problem to connect to information server or update something, please check installation."
		sys.exit()
	#print "press any key to continue..."	#debug

#-----------------------------------------------------
#------choose another active host to be slave CA------
#------must do this after update cacheFile only ------
#-----------------------------------------------------
slaveCA=None
""" this comment for stable version (no slave CA)
if len(activeHost)>1:
	for host in activeHost:
		if str(cerHost[1])!=str(host[1]): #check with ip
			slaveCA=host
			break
	
	success=caService.makeSlave(targetHostIP=str(slaveCA[1]))
	if not success:
		print slaveCA, "has problem to create slave CA, please check installation."
		sys.exit()
"""
##########################################
## start global controller at this host ##
##########################################
#raw_input("before mkapi start")

#generate auto whitelist on global controller host
print "Generating whitelist file..."
aFile=open(setting.API_WHITELIST_FILE,'w')
for host in activeHost:
	aFile.write(str(host[1])+'\n')
aFile.close()

print "Starting API Server..."
result = subprocess.Popen(shlex.split("service mkapi start")) #stdout=subprocess.PIPE will make broken pipe error
#result = subprocess.Popen(shlex.split("service mkapi start"), stdout=subprocess.PIPE)
result.wait()
#raw_input("after mkapi start")

########################################################
############ talk with monitoring service ##############
########################################################
#sequence of data is (GlobalController IP Address, setting.API_PORT, LOCAL_PORT)
#for HA must uncomment
#result=connection.socketCall('127.0.0.1', setting.MONITOR_PORT, 'hello_monitoring_service', [str(myIP),str(setting.API_PORT), str(setting.LOCAL_PORT)])

# tell status and end
print 'Your management tools can connect to API via IP Address',myIP
