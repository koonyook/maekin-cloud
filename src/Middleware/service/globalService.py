'''
globalController + DHCP Server
every method in this file must can be called at any host
'''
import MySQLdb
import json

import setting

from util import network,cacheFile,general
from util import connection
from util import debugger
from info import dbController
from planning import planTool

""" no makeslave, every host can be slave
def makeSlave(targetHostIP):
	return True
"""
def promote(targetHostIP=None):
	'''
	assume that master are downed
	promote is very like startup
	
	if targetHostIP=None must random from active host
	'''
	return moveGlobalService('promote',targetHostIP)

def migrate(targetHostIP=None):
	'''
	this method cannot be call at mkworker (because mkworker will be terminated)
	*** this method must be call from mklocd
	'''
	return moveGlobalService('migrate',targetHostIP)


def moveGlobalService(mode,targetHostIP=None):
	'''
	if targetHostIP=None must random from active host
	'''
	if targetHostIP!=None:
		condition="AND `IPAddress`='%s'"%(str(targetHostIP))
	else:
		condition=''

	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	
	cursor.execute("SELECT `hostID`, `IPAddress` FROM `hosts` WHERE `isGlobalController`=0 AND `status`=1 %s"%(condition))
	
	candidates=cursor.fetchall()
	if len(candidates)==0:
		print 'host to be promoted to globalController not found'
		return False
	
	tmpHostList=[]
	for element in candidates:
		tmpHostList.append(element[0])
	
	targetHostID=planTool.weightRandom(tmpHostList)
		
	for element in candidates:
		if element[0]==targetHostID:
			targetHostIP=element[1]
			break
	
	aFile=open(setting.API_WHITELIST_FILE,'r')
	whitelistString=aFile.read()
	aFile.close()

	result=connection.socketCall(targetHostIP,setting.LOCAL_PORT,"you_are_next_global_controller",['{socket_connection}',mode,whitelistString])
	if result!="OK":
		return False
	
	#tell monitoring service
	connection.socketCall("localhost",setting.MONITOR_PORT,'hello_monitoring_service', [str(targetHostIP),str(setting.API_PORT), str(setting.LOCAL_PORT)])
	
	#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
	#!!!!!!tell management tools!!!!!!! (must talk with k2w2)
	#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
	
	#broadcast to every active host
	cursor.execute("SELECT `IPAddress` FROM `hosts` WHERE `status`=1")
	activeHosts=cursor.fetchall()
	db.close()

	dataString=json.dumps({
		'globalController':str(targetHostIP)
	})

	for host in activeHosts:
		result=connection.socketCall(host[0], setting.LOCAL_PORT, 'update_cloud_info', ['{socket_connection}',dataString])
		if result!='OK':
			print "connection problem, cannot update_cloud_info to",host[0]

	return True