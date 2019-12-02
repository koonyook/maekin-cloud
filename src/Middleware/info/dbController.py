'''
use from localhost only
'''
import setting
from util import connection,network,general,cacheFile

#from python library
import subprocess, shlex
import MySQLdb
import json
import time

def setMasterConfig():
	'''
	must restart mysqld after this method
	'''
	configFile=open('/etc/my.cnf','w')
	writtenString=open(setting.MAIN_PATH+'info/masterTemplate_my.cnf','r').read()
	configFile.write(writtenString%{'MY_IP_ADDRESS':str(network.getMyIPAddr()),'DB_NAME':setting.DB_NAME})
	configFile.close()
	return True

def setSlaveConfig(masterIP):
	'''
	must restart mysqld after this method
	'''
	configFile=open('/etc/my.cnf','w')
	writtenString=open(setting.MAIN_PATH+'info/slaveTemplate_my.cnf','r').read()
	configFile.write(writtenString%{
		'MY_IP_ADDRESS':str(network.getMyIPAddr()),
		'MASTER_IP_ADDRESS':str(masterIP),
		'SLAVE_USER':setting.DB_USERNAME,
		'SLAVE_PASSWORD':setting.DB_PASSWORD,
		'DB_NAME':setting.DB_NAME})
	configFile.close()
	return True
"""
def start(rootpassword='-'):
	result = subprocess.Popen(shlex.split('''service mysqld start'''), stdout=subprocess.PIPE)
	result.wait()
	output=result.communicate()[0]
	if len(output)>50:	#this is the first time of start
		result2 = subprocess.Popen(shlex.split('''mysqladmin -u root password '%s' '''%(rootpassword)), stdout=subprocess.PIPE)
		result2.wait()
	return True
"""
def start(rootpassword="-",conn=None, sock=None):
	general.runDaemonCommand("service mysqld start",conn,sock)
	#output=result.communicate()[0]
	#if output!=None and len(output)>50:	#this is the first time of start
	
	#this line will error but it will not give bug (error as normal, cuz i cannot check it's the first time or not)
	result2 = subprocess.Popen(shlex.split("mysqladmin -u root password '%s'"%(rootpassword)), stdout=subprocess.PIPE)
	result2.wait()
	return True

def restart(conn=None, sock=None):
	general.runDaemonCommand("service mysqld restart",conn,sock)
	return True

def stop():
	general.runDaemonCommand("service mysqld stop")
	return True

def createDB(rootpassword,dbname,clean=False):
	db = MySQLdb.connect("localhost", "root", rootpassword)
	cursor = db.cursor()
	if clean==True:

		while True:
			cursor.execute("SHOW DATABASES LIKE '%s';"%(dbname))
			if cursor.fetchone()==None:
				break
			else:
				cursor.execute("DROP DATABASE IF EXISTS %s;"%(dbname))
				time.sleep(1)

		cursor.execute("CREATE DATABASE %s;"%(dbname))

	else:
		cursor.execute("CREATE DATABASE IF NOT EXISTS %s;"%(dbname))
	
		
	db.close()
	return True

	""" #these lines work but fool
	result = subprocess.Popen(shlex.split("mysql -u root --password='%s'"%(rootpassword)), stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.STDOUT)
	output = result.communicate(input="create database %s;\nexit\n"%(dbname))[0]
	#print output
	result.wait()
	if output.startswith("ERROR"):
		return False
	return True
	"""

def createUser(rootpassword,newusername,newpassword):
	db = MySQLdb.connect("localhost", "root", rootpassword)
	cursor = db.cursor()
	dataDict = {'USERNAME':newusername,'PASSWORD':newpassword,'MY_IP':network.getMyIPAddr()}

	cursor.execute("grant all on *.* to '%(USERNAME)s'@'%%' identified by '%(PASSWORD)s';"%dataDict)
	cursor.execute("grant all on *.* to '%(USERNAME)s'@'%(MY_IP)s' identified by '%(PASSWORD)s';"%dataDict)
	cursor.execute("grant all on *.* to '%(USERNAME)s'@'localhost' identified by '%(PASSWORD)s';"%dataDict)
	cursor.execute("FLUSH PRIVILEGES;")

	db.close()
	return True

	''' #these lines work but fool
	result = subprocess.Popen(shlex.split("mysql -u root --password='%s'"%(rootpassword)), stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.STDOUT)
	print "createUser!!!"

	output = result.communicate(input=
"""grant all on *.* to '%(USERNAME)s'@'%%' identified by '%(PASSWORD)s';
grant all on *.* to '%(USERNAME)s'@'%(MY_IP)s' identified by '%(PASSWORD)s';
grant all on *.* to '%(USERNAME)s'@'localhost' identified by '%(PASSWORD)s';
FLUSH PRIVILEGES;
exit
"""%{'USERNAME':newusername,'PASSWORD':newpassword,'MY_IP':network.getMyIPAddr()})[0]
	result.wait()
	print "grant result:",output

	if output.startswith("ERROR"):
		return False
	return True
	'''


def deleteUser(username):
	db = MySQLdb.connect("localhost", "root", rootpassword)
	cursor = db.cursor()
	dataDict = {'USERNAME':username,'MY_IP':network.getMyIPAddr()}

	cursor.execute("revoke all privileges, grant option from '%(USERNAME)s'@'%(MY_IP)s';"%dataDict)
	cursor.execute("revoke all privileges, grant option from '%(USERNAME)s'@'%%';"%dataDict)
	cursor.execute("revoke all privileges, grant option from '%(USERNAME)s'@'localhost';"%dataDict)
	cursor.execute("FLUSH PRIVILEGES;")

	db.close()
	return True

	''' #these lines work but fool
	result = subprocess.Popen(shlex.split("mysql -u root --password='%s'"%(rootpassword)), stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.STDOUT)
	output = result.communicate(input=
"""revoke all privileges, grant option from '%(USERNAME)s'@'%(MY_IP)s';
revoke all privileges, grant option from '%(USERNAME)s'@'%%';
revoke all privileges, grant option from '%(USERNAME)s'@'localhost';
FLUSH PRIVILEGES;
exit
"""%{'USERNAME':username,'MY_IP':network.getMyIPAddr()})[0]
	
	return True
	'''

def runSQL(filePath, username, password, dbname=None, targetIP="localhost"):
	'''
	run sql from file
	'''
	try:
		process = subprocess.Popen(shlex.split("mysql -u %s --password='%s' %s"%(username,password,dbname)), stdout=subprocess.PIPE, stdin=subprocess.PIPE)
		output = process.communicate('source '+filePath)[0]
		print "runSQLoutput:",output
		return True
	except:
		return False
	'''	#old method not work with dumped file
	try:
		sql = open(filePath,'r').read()
		
		db = MySQLdb.connect(targetIP, username, password, dbname )

		cursor = db.cursor()
		for query in sql.split(';')[0:-1]:
			cursor.execute(query)

		db.close()
		return True
	except:
		return False
	'''

def createInitialTables(username, password, dbname):
	'''use MySQLdb and import from exported query string from phpMyAdmin(startupQuery.sql)'''
	return runSQL(setting.MAIN_PATH+'info/startupQuery.sql',username,password,dbname,"localhost")

def broadcastNewMasterInformationServer(masterHostIP,masterHostMAC=None):
	'''
	can be call at any host
	'''
	#myIP=network.getMyIPAddr()
	print "masterHostIP:",masterHostIP
	db = MySQLdb.connect(masterHostIP, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME)
	cursor = db.cursor()
	if masterHostMAC==None:
		cursor.execute("SELECT `MACAddress` FROM `hosts` WHERE `IPAddress`='%s'"%(str(masterHostIP)))
		masterHostMAC=cursor.fetchone()[0]
	
	cursor.execute("SELECT `IPAddress` FROM `hosts` WHERE `status`=1 ;")
	activeHost=cursor.fetchall()
	db.close()
	dataString=json.dumps({
		'masterDB':str(masterHostIP),
		'masterDB_MAC':str(masterHostMAC),
	})
	for host in activeHost:
		result=connection.socketCall(host[0], setting.LOCAL_PORT, 'update_cloud_info', ['{socket_connection}',dataString])

	return True

def broadcastNewSlaveInformationServer(slaveHostIP,masterHostIP=None):  #if leave slaveHostIP='-' means slave was delete
	'''
	can be call at any host
	tell every active host to keep slave ip in file
	
	'''
	if masterHostIP==None:
		masterHostIP=cacheFile.getDatabaseIP()

	print "slaveHostIP:",slaveHostIP
	db = MySQLdb.connect(masterHostIP, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME)
	cursor = db.cursor()
	cursor.execute("SELECT `IPAddress` FROM `hosts` WHERE `status`=1 ;")
	activeHost=cursor.fetchall()
	db.close()
	dataString=json.dumps({
		'slaveDB':str(slaveHostIP)
	})
	for host in activeHost:
		result=connection.socketCall(host[0], setting.LOCAL_PORT, 'update_cloud_info', ['{socket_connection}',dataString])

	return True
