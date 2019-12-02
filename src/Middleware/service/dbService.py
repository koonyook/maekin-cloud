'''
every method in this file must can be called at any host
'''
import setting

from util import network,cacheFile
from util import connection
from util import debugger
from info import dbController


def makeSlave(targetHostIP,masterHostIP=None):
	if masterHostIP==None:
		masterHostIP=cacheFile.getDatabaseIP()
	
	result=connection.socketCall(masterHostIP, setting.LOCAL_PORT, 'create_your_slave_db',[str(targetHostIP)])
	if result!='OK':
		return False

	return True

def promote():
	'''
	this method turn that slave to a master
	must can do without master
	'''
	slaveHostIP=cacheFile.getSlaveDatabaseIP()
	
	if slaveHostIP==None:
		return False

	result=connection.socketCall(slaveHostIP,setting.LOCAL_PORT,'turn_slave_to_master_db',['{socket_connection}'])
	
	if result=='OK':
		return True
	else:
		return False

def migrate(targetHostIP):
	'''
	this method can be called at any host
	'''
	
	infoHost=cacheFile.getDatabaseIP()
	result=connection.socketCall(infoHost,setting.LOCAL_PORT,'migrate_database_to',[str(targetHostIP)])

	if result=='OK':		
		return True
	else:
		return False
