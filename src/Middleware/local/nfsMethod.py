import setting

from util import network,cacheFile,ping,general,shortcut
from util import connection
from util import debugger
from info import dbController
from storage import nfsController

import os
import time
import threading
import subprocess,shlex
import libvirt
import MySQLdb
import json
import shutil

def wake_up_nfs(argv):
	conn=argv[0][0]
	s=argv[0][1]
	
	nfsController.start(conn,s)

	return "OK"

def you_are_nfs_server(argv):
	'''
	make this host be ready for be mount from others
	*** now this host don't know know INFO_HOST ***
	'''
	''' these code cannot be used (data in database does not ready
	infoHost=cacheFile.getDatabaseIP()
	#get all of host from database
	hosts=[]
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	cursor.execute("SELECT `IPAddress` FROM `hosts`;")
	for row in cursor:
		hosts.append(str(row[0]))
	db.close()
	'''
	hosts=json.loads(argv[0])
	conn=argv[1][0]
	s=argv[1][1]

	nfsController.configServer(hosts)
	#debugger.countdown(10,"before restart nfs controller")
	nfsController.restart(conn,s)
	#debugger.countdown(10,"before cut nfs")
	return 'OK'

def stop_nfs_server(argv):
	'''
	nothing more than stop nfs
	'''
	nfsController.stop()
	
	if 'destroy' in argv:
		for aFile in os.listdir(setting.IMAGE_PATH):
			try:
				os.remove(setting.IMAGE_PATH+aFile)
			except:
				continue

	return 'OK'

def nfs_mount(argv):
	'''
	only nmount on this host
	'''
	storageHostIP=argv[0]

	nfsController.mount(storageHostIP)
	return 'OK'

def nfs_umount(argv):
	'''
	only unmount on this host
	'''
	nfsController.umount()
	return 'OK'

def nfs_refresh_export(argv):
	'''
	be called at nfsServer only
	remove this ip from export file
	'''
	nfsController.refreshExport()
	return 'OK'

def check_nfs_migrate_destination_area(argv):
	'''
	for nfs migration destination only
	argv[0] is json of list of [filename(path),size]
	'''
	
	#check required additional area on this host
	allFileData=json.loads(argv[0])
	
	requireMore=0
	for fileData in allFileData:
		try:
			oldFileSize=os.path.getsize(fileData[0])		
		except os.error:
			oldFileSize=0
		
		requireMore+=(fileData[1]-oldFileSize)
	
	#check the free area from monitoring service
	myIP=str(network.getMyIPAddr())
	data=connection.socketCall("localhost",setting.MONITOR_PORT,"get_current_storage_info",[myIP])
	print "##data from z##",data
	data=json.loads(data)
	
	if len(data)==0:
		return "data is not ready"
	else:
		data=data[0]
		free=data['storage_info']['free']*1024
		if free<requireMore:
			return "not enough free space on target host"
		else:
			return "OK"	

def check_nfs_migrate_destination_has_coppied(argv):
	'''
	for nfs migration destination only
	argv[0] is json of list of [filename(path),size]
	'''
	
	#check required additional area on this host
	allFileData=json.loads(argv[0])
	
	for fileData in allFileData:
		try:
			if fileData[1]!=os.path.getsize(fileData[0]):
				return fileData[0]+' size is invalid' 
		except os.error:
			return fileData[0]+' not found'
	
	return 'OK'
"""		
class LongFilesTransfering(threading.Thread):
	'''
	this class should be fixed
	'''
	def setArguments(self,fileData):
		self.fileData = fileData

	def run(self):

		global workingIndex
		global threadResult

		workingIndex=0

		for workingIndex in range(len(self.fileData)):
			filename=self.fileData[workingIndex][0]
			try:
				shutil.copy2(setting.TARGET_IMAGE_PATH+filename,setting.STORAGE_PATH+filename)			
				print "Copy "+filename+" success"

			except:
				threadResult=MySQLdb.escape_string(traceback.format_exc())
				print "Copy error"
				return
				
		threadResult="OK"
	

def transfer_all_file(argv):
	'''
	copy file in new nfs host
	this should be fixed
	'''
	taskID=argv[1]
	fileData=json.loads(argv[0])

	global workingIndex
	workingIndex=0
	
	aThread=LongFilesTransfering()
	aThread.setArguments(fileData)
	aThread.start()
	
	#main thread will see the size of file and store progress in <finishMessage>
	accumulate=[0]
	for aFile in fileData:
		accumulate.append(accumulate[-1]+aFile[1])

	completeCopySize=accumulate[-1]

	while aThread.isAlive():
		try:
			currentFileSize=os.path.getsize(setting.STORAGE_PATH+fileData[workingIndex][0])
		except os.error:
			currentFileSize=0
		
		alreadyCopySize=accumulate[workingIndex]+currentFileSize
	
		message='<progress>%s</progress> <completeFile>%s</completeFile>'%(str(alreadyCopySize*100.0/completeCopySize)+'%',str(workingIndex))
		shortcut.storeFinishMessage(taskID,message)
		print message
		aThread.join(5)		#update progress every five seconds
	
	return threadResult
"""
def get_file_size(argv):
	'''
	answer file size
	argv = list of filePath
	return in list of fileSize (-1 is error)
	'''
	result=[]
	for filePath in argv:
		try:
			fileSize=os.path.getsize(filePath)
			result.append(fileSize)
		except os.error:
			result.append(-1)
	
	return json.dumps(result)