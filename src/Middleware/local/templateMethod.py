import setting

from util import network,cacheFile,ping,general
from util import shortcut
from info import dbController
from storage import nfsController

import os
import shutil
import time
import threading
import subprocess,shlex
import libvirt
import MySQLdb
import json
import traceback

class LongTemplateCreating(threading.Thread):

	def setArguments(self,argv):
		self.sourceFileName = argv[0]
		self.targetFileName = argv[1]
		self.templateID		= argv[2]

	def run(self):
		global threadResult
		try:
			#shutil.copy2(setting.IMAGE_PATH+self.sourceFileName,setting.TEMPLATE_PATH+self.targetFileName)
			result = subprocess.Popen(shlex.split("qemu-img convert %s -O qcow2 %s"%(setting.IMAGE_PATH+self.sourceFileName,setting.TEMPLATE_PATH+self.targetFileName))) 
			result.wait()
			
			result = subprocess.Popen(shlex.split("chmod 777 %s"%(setting.TEMPLATE_PATH+self.targetFileName))) 
			result.wait()

			activity=0
			print "Create new template success"
			
			threadResult="OK"

		except:
			threadResult=MySQLdb.escape_string(traceback.format_exc())
			activity=-1
			print "Create new template error"

		#finish and tell database that you finish
		infoHost=cacheFile.getDatabaseIP()
		db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
		cursor = db.cursor()
		cursor.execute('''UPDATE `templates` SET `activity`=%s WHERE `templateID`=%s'''%(str(activity),self.templateID))
		db.close()
		

def template_create(argv):
	'''
	create from a guest image

	should be called at storageHolder only
	argv[0]=sourceFileName
	argv[1]=targetFileName
	argv[2]=templateID

	argv[3]=taskID
	'''
	taskID=argv[3]

	aThread=LongTemplateCreating()
	aThread.setArguments(argv)
	aThread.start()
	

	#main thread will see the size of new file and store progress in <finishMessage>
	currentFileSize=0
	while aThread.isAlive():
		try:
			currentFileSize=os.path.getsize(setting.TEMPLATE_PATH+argv[1])
		except os.error:
			currentFileSize=0
		
		message='<currentFileSize>%s</currentFileSize>'%(str(currentFileSize))
		shortcut.storeFinishMessage(taskID,message)
		print message
		aThread.join(5)		#update progress every five seconds
	
	return threadResult

def template_remove(argv):
	'''
	remove template image and data in database
	must be called at nfs server*
	'''
	templateID=argv[0]
	
	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()

	cursor.execute("SELECT `fileName` FROM `templates` WHERE `activity`=0 AND `templateID`=%s"%(templateID))
	tmp=cursor.fetchone()
	if tmp==None:
		return 'template not found or template is busy'
	
	fileName=tmp[0]
	cursor.execute("DELETE FROM `templates` WHERE `templateID`=%s"%(templateID))
	db.close()

	try:
		os.remove(setting.TEMPLATE_PATH+fileName)
	except:
		return "cannot remove image file completely"

	return "OK"
