import setting

from util import network,cacheFile,ping,general
from util import connection
from util import debugger
from info import dbController

import os
import time
import threading
import subprocess,shlex
import libvirt
import MySQLdb
import json
import shutil

def wake_up_database(argv):
	'''
	check that this is real database or not (and start it if it is real)
	'''
	conn =argv[0][0]
	s    =argv[0][1]
	
	myMAC=network.getMyMACAddr()
	dbMAC=cacheFile.getDatabaseMAC()
	if str(dbMAC)!=str(myMAC):
		return str(dbMAC)	#recomendation

	dbController.start(setting.DB_ROOT_PASSWORD,conn,s)
	
	try:
		db = MySQLdb.connect("localhost", "root", setting.DB_ROOT_PASSWORD, setting.DB_NAME)
		cursor = db.cursor()

		cursor.execute("SELECT `MACAddress` FROM `hosts` WHERE `isInformationServer`=1")
		ans=cursor.fetchone()[0]
		if ans==str(myMAC):
			#yes this is real
			return "OK"
		else:
			return ans	#recomendation
	except:
		dbController.stop()
		return "Sorry, this is not a real database"


def you_are_information_server(argv):
	'''
	dest = master only
	start up database service, create table
	'''
	conn =argv[0][0]
	s    =argv[0][1]
	#get parameter
	#rootpassword=argv[1]
	#dbname=argv[2]
	
	dbController.setMasterConfig()	#very important for make it can be connected via remote host
	dbController.stop()
	dbController.start(setting.DB_ROOT_PASSWORD,conn,s)
	dbController.createDB(setting.DB_ROOT_PASSWORD, setting.DB_NAME)

	print dbController.createInitialTables('root', setting.DB_ROOT_PASSWORD, setting.DB_NAME)

	#This line allow robot user to connect to database
	dbController.createUser(setting.DB_ROOT_PASSWORD,setting.DB_USERNAME,setting.DB_PASSWORD)

	return 'OK'

def create_your_slave_db(argv):
	'''
	dest = master only
	and should be call after finish NFS system
	'''
	targetHostIP=argv[0]

	db = MySQLdb.connect("localhost", "root", setting.DB_ROOT_PASSWORD)
	cursor = db.cursor()
	cursor.execute("FLUSH TABLES WITH READ LOCK;")
	cursor.execute("SHOW MASTER STATUS;")
	data=cursor.fetchone()
	
	fileData=data[0]
	positionData=data[1]

	myIP=network.getMyIPAddr()
	result = subprocess.Popen(shlex.split("mysqldump %s -u root --password='%s'"%(setting.DB_NAME,setting.DB_ROOT_PASSWORD)), stdout=subprocess.PIPE)
	#result.wait()
	output=result.communicate()[0]
	#print "before write file"
	#dumpFile=open(setting.DB_DUMP_FILE,'w')
	#dumpFile.write(output)
	#dumpFile.close()
	result=connection.socketCall(targetHostIP,setting.LOCAL_PORT,'you_are_slave_db',['{socket_connection}',str(myIP),fileData,str(positionData),output])
	print "~~~",result
	
	cursor.execute("UNLOCK TABLES;")
	
	db.close()

	if result=='OK':
		#this is the first transaction that will be replicated to slave automaticaly
		db = MySQLdb.connect("localhost", "root", setting.DB_ROOT_PASSWORD, setting.DB_NAME)
		cursor = db.cursor()
		cursor.execute("UPDATE `hosts` SET `isInformationServer`=2 WHERE `IPAddress`='%s'"%(str(targetHostIP)))
		db.close()
		#tell slave ip to every host (it will be used when master down)
		dbController.broadcastNewSlaveInformationServer(slaveHostIP=targetHostIP,masterHostIP=str(myIP))
	
	return result

def you_are_slave_db(argv):
	'''
	dest = slave only
	'''
	conn =argv[0][0]
	s    =argv[0][1]

	masterHost=argv[1]
	fileData=argv[2]
	positionData=argv[3]

	dumpString=argv[4]
	dumpFile=open(setting.DB_DUMP_FILE,'w')
	dumpFile.write(dumpString)
	dumpFile.close()

	dbController.setSlaveConfig(str(masterHost))	#very important for make it can be connected via remote host
	dbController.stop()
	dbController.start(setting.DB_ROOT_PASSWORD,conn,s)
	dbController.createDB(setting.DB_ROOT_PASSWORD, setting.DB_NAME,True)	#drop and create new database
	print "before runSQL"
	dumpResult = dbController.runSQL(setting.DB_DUMP_FILE,"root",setting.DB_ROOT_PASSWORD,setting.DB_NAME,"localhost")
	if dumpResult==False:
		return "runSQL error, please check .sql file"
	
	db = MySQLdb.connect("localhost", "root", setting.DB_ROOT_PASSWORD)
	cursor = db.cursor()
	cursor.execute("SLAVE STOP;")
	cursor.execute("CHANGE MASTER TO MASTER_HOST='%s', MASTER_USER='%s', MASTER_PASSWORD='%s', MASTER_LOG_FILE='%s', MASTER_LOG_POS=%s;"
		%(str(masterHost),setting.DB_USERNAME,setting.DB_PASSWORD,fileData,positionData))
	print "before slave start"
	cursor.execute("SLAVE START;")
	
	db.close()
	
	print "after slave start"

	os.remove(setting.DB_DUMP_FILE)

	return 'OK'

def you_are_db_migration_destination(argv):
	'''
	migrate from source to dest of socketCall
	'''
	conn =argv[0][0]
	s    =argv[0][1]
	
	#targetFile=setting.DB_NFS_DUMP_FILE
	
	targetFile=setting.DB_DUMP_TEMP_FILE
	dumpString=argv[1]
	dumpFile=open(targetFile,'w')
	dumpFile.write(dumpString)
	dumpFile.close()

	myIP=network.getMyIPAddr()
	
	dbController.setMasterConfig()	#very important for make it can be connected via remote host
	dbController.start(setting.DB_ROOT_PASSWORD,conn,s)
	dbController.createDB(setting.DB_ROOT_PASSWORD, setting.DB_NAME,True)	#drop and create new database
	dbController.createUser(setting.DB_ROOT_PASSWORD,setting.DB_USERNAME,setting.DB_PASSWORD)

	dumpResult = dbController.runSQL(targetFile,"root",setting.DB_ROOT_PASSWORD,setting.DB_NAME,"localhost")
	if dumpResult==False:
		return "runSQL error, please check .sql file"
	
	db = MySQLdb.connect("localhost", "root", setting.DB_ROOT_PASSWORD, setting.DB_NAME)
	cursor = db.cursor()
	cursor.execute("UPDATE `hosts` SET `isInformationServer`=1 WHERE `IPAddress`='%s'"%(str(myIP)))
	db.close()
	
	os.remove(targetFile)

	return 'OK'

def turn_slave_to_master_db(argv):
	'''
	dest = slave only
	1. turn
	2. update db
	3. tell every host
	'''
	conn =argv[0][0]
	s    =argv[0][1]
	
	myIP=network.getMyIPAddr()
	myMAC=network.getMyMACAddr()

	db = MySQLdb.connect("localhost", "root", setting.DB_ROOT_PASSWORD)
	cursor = db.cursor()
	cursor.execute("SLAVE STOP;")
	db.close()

	dbController.setMasterConfig()
	dbController.stop()
	dbController.start(setting.DB_ROOT_PASSWORD,conn,s)

	dbController.createUser(setting.DB_ROOT_PASSWORD,setting.DB_USERNAME,setting.DB_PASSWORD)

	db = MySQLdb.connect("localhost", "root", setting.DB_ROOT_PASSWORD)
	cursor = db.cursor()
	cursor.execute("UPDATE `hosts` SET `isInformationServer`=1 WHERE `IPAddress`='%s'"%(str(myIP)))
	db.close()

	dbController.broadcastNewMasterInformationServer(str(myIP),str(myMAC))

	#should create new slave if there is another active host

	return 'OK'



def destroy_slave_host_info(argv):
	'''
	dest = slave only
	'''
	
	myIP=network.getMyIPAddr()

	db = MySQLdb.connect("localhost", "root", setting.DB_ROOT_PASSWORD)
	cursor = db.cursor()
	cursor.execute("SLAVE STOP;")
	
	cursor.execute("DROP DATABASE IF EXISTS %s"%(setting.DB_NAME))	#this line was added later

	db.close()
	dbController.stop()

	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	cursor.execute("UPDATE `hosts` SET `isInformationServer`=0 WHERE `IPAddress`='%s'"%(str(myIP)))
	db.close()
	
	dbController.broadcastNewSlaveInformationServer('-')

	return 'OK'

"""
def update_info_host(argv):
	'''
	obsolete
	dest = every active host
	look like update_cloud_info but this method do not renew mounting nfs server
	'''
	masterInfoHost=argv[0]
	cacheFile.setValue(masterDB=masterInfoHost)
	
	slaveInfoHost=cacheFile.getSlaveDatabaseIP()

	if masterInfoHost==slaveInfoHost:
		cacheFile.setValue(slaveDB='-')		#clear slave file in case of that slave turn to master
	return 'OK'

def update_slave_info_host(argv):
	'''
	obsolete
	dest = every active host
	'''
	slaveInfoHost=argv[0]
	cacheFile.setValue(slaveDB=slaveInfoHost)
	return 'OK'
"""

def migrate_database_to(argv):
	'''
	this method must be called at master database only
	and should be call after finish NFS system
	1. destroy slave
	2. dump and send to targetHost to create new master
	3. stop mysqld service
	'''
	targetHostIP=argv[0]

	#find slave to destroy from my database
	db = MySQLdb.connect("localhost", "root", setting.DB_ROOT_PASSWORD, setting.DB_NAME)
	cursor = db.cursor()
	cursor.execute("SELECT `IPAddress` FROM `hosts` WHERE `isInformationServer`=2")
	activeSlave=cursor.fetchone()
	if activeSlave!=None:
		slaveIP=activeSlave[0]
		connection.socketCall(targetHostIP,setting.LOCAL_PORT,'destroy_slave_host_info')

	myIP=network.getMyIPAddr()
	
	cursor.execute("FLUSH TABLES WITH READ LOCK;");

	result = subprocess.Popen(shlex.split("mysqldump %s -u root --password='%s'"%(setting.DB_NAME,setting.DB_ROOT_PASSWORD)), stdout=subprocess.PIPE)
	#result.wait()
	output=result.communicate()[0]

	#dumpFile=open(setting.DB_NFS_DUMP_FILE,'w')
	#dumpFile.write(output)
	#dumpFile.close()

	result=connection.socketCall(targetHostIP,setting.LOCAL_PORT,'you_are_db_migration_destination',['{socket_connection}',output])
	cursor.execute("UNLOCK TABLES;")
	
	cursor.execute("DROP DATABASE IF EXISTS %s"%(setting.DB_NAME))	#this line was added later
	
	db.close()

	if result=='OK':
		dbController.stop()
		
		db = MySQLdb.connect(targetHostIP, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME)
		cursor = db.cursor()
		cursor.execute("UPDATE `hosts` SET `isInformationServer`=0 WHERE `IPAddress`='%s'"%(str(myIP)))
		db.close()
		
		dbController.broadcastNewMasterInformationServer(targetHostIP)

		return 'OK'
	else:
		return result

def stop_database_server(argv):
	'''
	nothing more than stop mysqld
	'''
	dbController.stop()
	return 'OK'