'''
every method in this file must can be called at any host
'''
import MySQLdb

import setting

from util import network,cacheFile
from util import connection
from util import debugger
from info import dbController


def makeSlave(targetHostIP):
	'''
	only copy 2 file from CA to target
	and update database
	'''
	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	
	cursor.execute('''SELECT 
	`IPAddress`
	FROM `hosts` WHERE `isCA`=1''')
	oldCAData=cursor.fetchone()
	db.close()

	if oldCAData==None:
		print 'Old CA not found'
		return False

	oldCAIP=oldCAData[0]

	result=connection.socketCall(oldCAIP,setting.LOCAL_PORT,"clone_ca",[targetHostIP,'makeSlave'])
	if result!="OK":
		return False
	
	return True

def promote(slaveHostIP=None):
	'''
	only update in database
	'''
	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	
	if slaveHostIP!=None:
		condition=" AND `IPAddress`='%s'"%(str(slaveHostIP))
	else:
		condition=''

	cursor.execute('''SELECT 
	`IPAddress`
	FROM `hosts` WHERE `isCA`=2 %s;'''%(condition))
	hostData=cursor.fetchone()
	if hostData==None:
		print 'active slave CA not found!'
		return False
	
	slaveHostIP=hostData[0]

	cursor.execute("UPDATE `hosts` SET `isCA`=1 WHERE `IPAddress`='%s';"%(slaveHostIP))
	db.close()	
	return True

def migrate(targetHostIP=None):
	'''
	only move 2 file from oldCA to newCA
	and update database
	'''
	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	
	cursor.execute('''SELECT 
	`IPAddress`
	FROM `hosts` WHERE `isCA`=1''')
	oldCAData=cursor.fetchone()
	db.close()

	if oldCAData==None:
		print 'Old CA not found'
		return False

	oldCAIP=oldCAData[0]

	result=connection.socketCall(oldCAIP,setting.LOCAL_PORT,"clone_ca",[targetHostIP,'migrate'])
	if result!="OK":
		return False
	
	return True
