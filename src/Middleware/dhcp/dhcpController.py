import setting
#from python library
import time
import subprocess, shlex
import re
import MySQLdb
#from my library
from util import network,cacheFile
from util import general

def waitConfigTest():
	while True:
		result=subprocess.Popen(shlex.split("service dhcpd configtest"),stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		output=result.communicate()
		if output[1]=='Syntax: OK\n' or output[1]=='':
			return True
		else:
			print "dhcp config syntax error:\n"+output[1]
			time.sleep(1)
	
def start(conn=None, sock=None):
	waitConfigTest()
	general.runDaemonCommand("service dhcpd start",conn,sock)
	return True

def restart(conn=None, sock=None):
	waitConfigTest()
	general.runDaemonCommand("service dhcpd restart",conn,sock)
	return True

def stop():
	general.runDaemonCommand("service dhcpd stop")
	return True

def clearConfigFile():
	configFile=open(setting.DHCP_CONFIG_FILE,'w')
	configFile.close()
	return True

def isValidData(networkID, subnetMask, defaultRoute=None, dns=[], hostBindings=[]):
	'''
	dns = list of IPAddr
	hostBindings = list of (MACAddr,IPAddr,hostNameString)
	return boolean
	'''
	if not network.isMatch(networkID,subnetMask):
		return False
	
	if  defaultRoute!=None and not defaultRoute.isInNetwork(networkID,subnetMask):
		return False

	macList = []
	ipList = [networkID,defaultRoute]
	#nameList = []

	for element in dns:
		if element in ipList:
			return False
		ipList.append(element)
	
	for element in hostBindings:
		if element[0] in macList or element[0].isMulticast() or element[1] in ipList or not element[1].isInNetwork(networkID,subnetMask) or element[2]=='': #or element[2] in nameList 
			return False
		
		macList.append(element[0])
		ipList.append(element[1])
		#nameList.append(element[2])
	
	return True

def refreshConfig():
	dhcpInfo=getDHCPInfoFromDatabase()
	overwriteConfig(dhcpInfo['networkID'],dhcpInfo['subnetMask'],dhcpInfo['defaultRoute'],dhcpInfo['dns'],dhcpInfo['hostBindings'])
	return True

def overwriteConfig(networkID, subnetMask, defaultRoute=None, dns=[], hostBindings=[]):
	hostTemplateString = open(setting.MAIN_PATH+'dhcp/template/eachBinding.template','r').read()
	usedHostName=[]
	bindingString=''
	for element in hostBindings:
		cleanHostName=element[2]
		counter=2
		while cleanHostName in usedHostName:
			cleanHostName=element[2]+'.'+str(counter)
			counter+=1
		bindingString+=hostTemplateString%{
			'MAC_ADDRESS':element[0],
			'IP_ADDRESS':element[1],
			'HOST_NAME':cleanHostName
			}
		usedHostName.append(cleanHostName)
	
	mainTemplateString = open(setting.MAIN_PATH+'dhcp/template/dhcpd.template','r').read()
	
	#default route
	if defaultRoute==None:
		commentDefaultRoute='#'
		defaultRoute=''
	else:
		commentDefaultRoute=''

	#dns
	if dns==[]:
		commentDNS='#'
		dnsString=''
	else:
		commentDNS=''
		tmp=[]
		for ip in dns:
			tmp.append(str(ip))
		dnsString=','.join(tmp)

	writtenString = mainTemplateString%{
		'MAIN_PATH':setting.MAIN_PATH,
		'SUBNET':networkID,
		'NETMASK':subnetMask,
		'COMMENT_DEFAULT_ROUTE':commentDefaultRoute,
		'DEFAULT_ROUTE':defaultRoute,
		'COMMENT_DOMAIN_NAME_SERVERS':commentDNS,
		'DOMAIN_NAME_SERVERS':dnsString,
		'BINDINGS':bindingString
		}
	#overwrite to target file
	configFile=open(setting.DHCP_CONFIG_FILE,'w')
	configFile.write(writtenString)
	configFile.close()

def configAll(networkID, subnetMask, defaultRoute=None, dns=[], hostBindings=[],conn=None,sock=None):
	'''
	no address be in string type
	'''
	#verify parameter
	if not isValidData(networkID, subnetMask, defaultRoute, dns, hostBindings):
		print 'invalid data set'
		return False
	overwriteConfig(networkID, subnetMask, defaultRoute, dns, hostBindings)
	#restart service
	restart(conn,sock)
	return True
"""
def getDHCPInfoFromConfigFile():
	'''
	read dhcpd config file and return a dict
	{networkID, subnetMask, defaultRoute=None, dns=[], hostBindings}

	**must implement this method because i must do this before db is enable
	'''
	#content = open('example.conf','r').read()
	content = open(setting.DHCP_CONFIG_FILE,'r').read()

	mainMatch=re.match(r"^include\s*\"(?P<INCLUDE>.+)\";\s*subnet\s*(?P<SUBNET>(\d+\.){3}\d+)\s+netmask\s+(?P<NETMASK>(\d+\.){3}\d+)\s*{\s*(?P<COMMENT_DEFAULT_ROUTE>#|)\s*option\s+routers\s+(?P<DEFAULT_ROUTE>((\d+\.){3}\d+)|)\s*;\s*(?P<COMMENT_DOMAIN_NAME_SERVERS>#|)\s*option\s+domain-name-servers\s+(?P<DOMAIN_NAME_SERVERS>(((\d+\.){3}\d+\s*,\s*)*(\d+\.){3}\d+)|)\s*;\s*(?P<BINDINGS>(host\s+.+\s*{\s*hardware\s+ethernet\s+([\dABCDEF]{2}:){5}[\dABCDEF]{2}\s*;\s*fixed-address\s+(\d+\.){3}\d+\s*;\s*}\s*)*)}",content)
	mainInfo=mainMatch.groupdict()
	
	
	if mainInfo['COMMENT_DEFAULT_ROUTE']=='#' or mainInfo['DEFAULT_ROUTE']=='':
		defaultRoute=None
	else:
		defaultRoute=network.IPAddr(mainInfo['DEFAULT_ROUTE'])

	if mainInfo['COMMENT_DOMAIN_NAME_SERVERS']=='#' or mainInfo['DOMAIN_NAME_SERVERS']=='':
		dns=[]
	else:
		dns=[]
		for ip in mainInfo['DOMAIN_NAME_SERVERS'].split(','):
			dns.append(network.IPAddr(ip))
	
	hostConfig = mainInfo['BINDINGS']
	hostMatches=re.finditer(r"host\s+(?P<HOST_NAME>.+)\s*{\s*hardware\s+ethernet\s+(?P<MAC_ADDRESS>([\dABCDEF]{2}:){5}[\dABCDEF]{2})\s*;\s*fixed-address\s+(?P<IP_ADDRESS>(\d+\.){3}\d+)\s*;\s*}",hostConfig)
	hostBindings=[]
	for element in hostMatches:
		tmp=element.groupdict()
		hostBindings.append((network.MACAddr(tmp['MAC_ADDRESS']),network.IPAddr(tmp['IP_ADDRESS']),tmp['HOST_NAME']))

	return {
		'networkID':network.IPAddr(mainInfo['SUBNET']),
		'subnetMask':network.IPAddr(mainInfo['NETMASK']),
		'defaultRoute':defaultRoute,
		'dns':dns,
		'hostBindings':hostBindings
		}
"""
def getDHCPInfoFromDatabase():
	'''
	read db and return a dict
	{networkID, subnetMask, defaultRoute=None, dns=[], hostBindings}

	**data must be ready in database
	'''
	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	cursor.execute("SELECT `key`,`value` from `cloud_variables`;")
	cloudData=cursor.fetchall()
	
	dataDict={}
	for element in cloudData:
		key=element[0]
		value=element[1]

		if key=='network_id':
			dataDict['networkID']=network.IPAddr(value)
		elif key=='subnet_mask':
			dataDict['subnetMask']=network.IPAddr(value)
		elif key=='default_route':
			try:
				dataDict['defaultRoute']=network.IPAddr(value)
			except:
				dataDict['defaultRoute']=None
		elif key=='dns_servers':
			tempList=value.split(',')
			dataDict['dns']=[]
			for eachDNS in tempList:
				try:
					dataDict['dns'].append(network.IPAddr(eachDNS))
				except:
					continue

	dataDict['hostBindings']=[]
	cursor.execute('''SELECT `MACAddress`,`IPAddress`,`Name` FROM 
	(
		(SELECT `MACAddress`,`IPAddress`,`hostName` as `Name` FROM `hosts`)
		UNION
		(SELECT `MACAddress`,`IPAddress`,`guestName` as `Name` FROM `guests`)
	) AS X
	''')
	bindData=cursor.fetchall()
	db.close()
	
	for element in bindData:
		dataDict['hostBindings'].append((network.MACAddr(element[0]),network.IPAddr(element[1]),element[2]))
	
	return dataDict

def unbind(hostList,conn=None,sock=None):
	'''
	hostList = list of (MAC,IP)
	error when do not match with old info
	'''
	#dhcpInfo=getDHCPInfoFromConfigFile()
	dhcpInfo=getDHCPInfoFromDatabase()
	hostBindings = dhcpInfo['hostBindings']
	removeList=[]
	for element in hostList:
		isFound=False
		for target in hostBindings:
			if (element[0]==target[0]) and (element[1]==target[1]):
				if not (target in removeList):
					removeList.append(target)
				isFound=True
		if not isFound:
			print 'unbind not found'
			#return False	hacking to database and destroy non-finish-cloning guest easily

	for target in removeList:
		hostBindings.remove(target)
	
	dhcpInfo['hostBindings']=hostBindings

	overwriteConfig(dhcpInfo['networkID'],dhcpInfo['subnetMask'],dhcpInfo['defaultRoute'],dhcpInfo['dns'],dhcpInfo['hostBindings'])

	restart(conn,sock)

	return True

def bind(hostList,conn=None,sock=None):
	'''
	hostList = list of (MAC,IP,HOST_NAME)
	'''
	#fix hostList if they are string
	fixedHostList=[]
	for element in hostList:
		if type(element[0])==type('str'):
			macObj=network.MACAddr(element[0])
		else:
			macObj=element[0]
		if type(element[1])==type('str'):
			ipObj=network.IPAddr(element[1])
		else:
			ipObj=element[1]
		fixedHostList.append((macObj,ipObj,element[2]))
	
	hostList=fixedHostList

	#dhcpInfo=getDHCPInfoFromConfigFile()
	dhcpInfo=getDHCPInfoFromDatabase()
	
	#cut the same ip
	for eachHost in hostList:
		same=False
		for tmpHost in dhcpInfo['hostBindings']:
			if eachHost[1]==tmpHost[1]:
				same=True
				break
		
		if same==False:
			dhcpInfo['hostBindings'].append(eachHost)
	
	#dhcpInfo['hostBindings']+=hostList

	if not isValidData(dhcpInfo['networkID'],dhcpInfo['subnetMask'],dhcpInfo['defaultRoute'],dhcpInfo['dns'],dhcpInfo['hostBindings']):
		print 'Invalid dhcpInfo'
		print dhcpInfo
		return False
	
	overwriteConfig(dhcpInfo['networkID'],dhcpInfo['subnetMask'],dhcpInfo['defaultRoute'],dhcpInfo['dns'],dhcpInfo['hostBindings'])

	restart(conn,sock)

	return True

def updateFromDatabase(conn=None,sock=None):

	dhcpInfo=getDHCPInfoFromDatabase()
	
	overwriteConfig(dhcpInfo['networkID'],dhcpInfo['subnetMask'],dhcpInfo['defaultRoute'],dhcpInfo['dns'],dhcpInfo['hostBindings'])

	restart(conn,sock)

	return True
