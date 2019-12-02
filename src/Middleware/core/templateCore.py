import setting
from util import connection,cacheFile,network,general
from util import shortcut
from dhcp import dhcpController
from planning import planTool

import MySQLdb
import json
import os
import random

def template_create_from_guest(taskID,detail):
	#get parameter
	sourceGuestID=detail['sourceGuestID']
	description=detail['description']

	#start the work
	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	#find sourceGuestID and template data
	cursor.execute("""SELECT 
	`templates`.`size`, 
	`templates`.`minimumMemory`, 
	`templates`.`maximumMemory`,
	`templates`.`OS`,
	`guests`.`volumeFileName`,
	`guests`.`status`,
	`guests`.`activity`
	FROM `templates` INNER JOIN `guests` ON `templates`.`templateID`=`guests`.`templateID`
	WHERE `guests`.`guestID`=%s
	"""%(sourceGuestID))
	tmpData=cursor.fetchone()
	if tmpData==None:
		return 'sourceGuestID not found'
	if tmpData[5]!=0 or tmpData[6]!=0:
		return 'source guest is busy'
	
	imageSize=int(tmpData[0])	#unit is byte
	#find storageHolder
	cursor.execute("SELECT `hostID`, `IPAddress` FROM `hosts` WHERE `isStorageHolder`=1")
	storageHolder=cursor.fetchone()
	
	#check storage
	storageInfo=connection.socketCall('localhost',setting.MONITOR_PORT,'get_current_storage_info', [str(storageHolder[1])])
	if json.loads(storageInfo)==[]:
		return "Data is not ready, please try again later."
	freeSpace=int(json.loads(storageInfo)[0]['storage_info']['free'])	#unit is Kbyte
	if imageSize>freeSpace*1024:
		return "Do not have enough space for duplicate this image"
	
	#find image file name
	usedImageNames=[]
	cursor.execute("SELECT `fileName` FROM `templates`")
	tmpFileName=cursor.fetchone()
	while tmpFileName!=None:
		usedImageNames.append(tmpFileName[0])
		tmpFileName=cursor.fetchone()
	
	volumeFileName=tmpData[4].split('.')[0]+'_template.img'
	count=2
	while volumeFileName in usedImageNames :
		volumeFileName=guestName+'('+str(count)+').img'
		count+=1
	
	cursor.execute('''
	INSERT INTO `templates` (`fileName`, `OS`, `size`, `description`, `minimumMemory`, `maximumMemory`, `activity`) VALUES
	('%(filename)s', '%(OS)s', '%(size)s', '%(description)s', '%(minimumMemory)s', '%(maximumMemory)s', '%(activity)s');
	'''%{
	'size':tmpData[0],
	'minimumMemory':tmpData[1],
	'maximumMemory':tmpData[2],
	'OS':tmpData[3],
	'filename':volumeFileName,
	'description':description,	
	'activity':1			#cloning
	})		

	templateID=cursor.lastrowid
	
	#add activity duplicating
	cursor.execute("UPDATE `guests` SET `activity`=6 WHERE `guestID`=%s"%(sourceGuestID))

	result=connection.socketCall(str(storageHolder[1]),setting.LOCAL_PORT,'template_create',[str(tmpData[4]),volumeFileName,str(templateID),str(taskID)])
	
	cursor.execute("UPDATE `guests` SET `activity`=0 WHERE `guestID`=%s"%(sourceGuestID))

	db.close()
	
	if result!='OK':
		return 'something error'
	
	content='<template templateID="%s" />'%(str(templateID))
	
	if not shortcut.storeFinishMessage(taskID,content):
		return "cannot storeFinishMessage"

	return "OK"

def template_remove(taskID,detail):
	#get parameter
	templateID=detail['templateID']
	
	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	
	cursor.execute("SELECT `guestID` FROM `guests` WHERE `templateID`=%s"%(str(detail['templateID'])))

	if cursor.fetchone()!=None:
		return 'There are guests that use this template'
	
	cursor.execute("SELECT `IPAddress` FROM `hosts` WHERE `isStorageHolder`=1")
	storageHolder=cursor.fetchone()[0]
	
	db.close()
	
	result=connection.socketCall(str(storageHolder),setting.LOCAL_PORT,'template_remove',[str(templateID)])
		
	if result!='OK':
		return result
	
	content=''
	
	if not shortcut.storeFinishMessage(taskID,content):
		return "cannot storeFinishMessage"

	return "OK"