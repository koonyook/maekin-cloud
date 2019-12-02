#this module should be call from local controller only
import setting
from util import general,cacheFile

import subprocess, shlex
import MySQLdb

def start(conn=None, sock=None):
	general.runDaemonCommand("service nfs start",conn,sock)
	return True

def restart(conn=None, sock=None):
	general.runDaemonCommand("service nfs restart",conn,sock)
	return True

def stop():
	general.runDaemonCommand("service nfs stop")
	return True


def configServer(hosts):
	'''
	use this method before start nfs service.
	hosts = list of ip that are allowed to mount from this server
	'''
	result = subprocess.Popen(shlex.split('''mkdir -p -m 777 %s'''%(setting.IMAGE_PATH)), stdout=subprocess.PIPE)
	result.wait()
	
	result = subprocess.Popen(shlex.split('''mkdir -p -m 777 %s'''%(setting.TEMPLATE_PATH)), stdout=subprocess.PIPE)
	result.wait()

	result = subprocess.Popen(shlex.split('''chmod -R 777 %s'''%(setting.STORAGE_PATH)), stdout=subprocess.PIPE)
	result.wait()

	print "config exports:",hosts
	configFile=open('/etc/exports','w')
	configFile.write(setting.STORAGE_PATH) #IMAGE_PATH)
	for element in hosts:
		configFile.write(" %s(rw,sync,fsid=0,no_root_squash)"%(str(element)))
	configFile.close()
	print "config exports finished"	

def refreshExport():
	'''
	refresh export file from database
	'''
	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	cursor.execute("SELECT `IPAddress` FROM `hosts`")
	data=cursor.fetchall()
	
	hostIPList=[]
	for element in data:
		hostIPList.append(element[0])

	configServer(hostIPList)


def mount(targetIP):
	'''
	mount from nfs server(targetIP) to TARGET_IMAGE_PATH and TARGET_TEMPLATE_PATH
	'''
	result = subprocess.Popen(shlex.split('''mount -t nfs4 %s:/%s %s'''%(str(targetIP),setting.IMAGE_PATH.replace(setting.STORAGE_PATH,''),setting.TARGET_IMAGE_PATH)), stdout=subprocess.PIPE)
	result.wait()
	output=result.communicate()[0]
	if output!='':
		return False #sometimes it is busy

	result = subprocess.Popen(shlex.split('''mkdir -p -m 777 %s'''%(setting.TARGET_TEMPLATE_PATH)), stdout=subprocess.PIPE)
	result.wait()
	
	result = subprocess.Popen(shlex.split('''mount -t nfs4 %s:/%s %s'''%(str(targetIP),setting.TEMPLATE_PATH.replace(setting.STORAGE_PATH,''),setting.TARGET_TEMPLATE_PATH)), stdout=subprocess.PIPE)
	result.wait()
	output=result.communicate()[0]
	if output!='':
		return False #sometimes it is busy

	return True

def umount():
	'''
	unmount at TARGET_IMAGE_PATH and TARGET_TEMPLATE_PATH
	'''
	result = subprocess.Popen(shlex.split('''umount %s'''%(setting.TARGET_TEMPLATE_PATH)), stdout=subprocess.PIPE)
	result.wait()
	output=result.communicate()[0]
	if output!='':
		return False #sometimes it is busy

	result = subprocess.Popen(shlex.split('''umount %s'''%(setting.TARGET_IMAGE_PATH)), stdout=subprocess.PIPE)
	result.wait()
	output=result.communicate()[0]
	if output!='':
		return False #sometimes it is busy
	return True
