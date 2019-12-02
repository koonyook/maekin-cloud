from util import connection,cacheFile,general
from util import shortcut
import setting
from scheduling import queue

import json
import os
import MySQLdb

################################
######## Template Zone #########
################################
class Template(object):

	class GetInfo():
		'''
		get template info from database only
		'''
		def index(self,templateID=None):
			infoHost=cacheFile.getDatabaseIP()
			db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
			cursor = db.cursor()
			
			if templateID==None:
				conditionString="";
			else:
				conditionString="WHERE `templateID`=%s"%(str(templateID))
			
			cursor.execute('''SELECT 
			`templateID`, `OS`,`size`,`description`,`minimumMemory`,`maximumMemory`,`activity`
			FROM `templates`'''+conditionString+";")
			
			table=cursor.fetchall()
			db.close()	
			
			templateString=open(setting.MAIN_PATH+'webapi/template/template_getInfo.xml').read()
			result=''
			for row in table:
				templateDict={
				'templateID':str(row[0]),
				'OS':str(row[1]),
				'size':str(row[2]),
				'description':str(row[3]),
				'minimumMemory':str(row[4]),
				'maximumMemory':str(row[5]),
				'activity':str(row[6])
				}

				result+=templateString%templateDict
			
			return shortcut.response('success', result)
			
		index.exposed = True
	
	class CreateFromGuest():
		'''
		create a template from created guest
		'''
		def index(self,sourceGuestID,description):

			detail={
			'command':'template_create_from_guest',
			'sourceGuestID':sourceGuestID,
			'description':description
			}

			taskID=queue.enqueue(detail)

			return shortcut.responseTaskID(taskID)
			
		index.exposed = True

	class Remove():
		'''
		remove template permanently
		(all of guest that clone from this template must be destroy first)
		'''
		def index(self,templateID):
			infoHost=cacheFile.getDatabaseIP()
			db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
			cursor = db.cursor()
			cursor.execute("SELECT `guestID` FROM `guests` WHERE `templateID`=%s"%(str(templateID)))
			tmp=cursor.fetchone()
			db.close()
			if tmp!=None:
				return shortcut.response('error', '', 'There are guests that use this template')
			
			detail={
			'command':'template_remove',
			'templateID':templateID
			}

			taskID=queue.enqueue(detail)

			return shortcut.responseTaskID(taskID)
			
		index.exposed = True
	
	class Add():
		'''
		add template from the image file 
		that already paste to setting.TEMPLATE_PATH of nfs host
		'''
		def index(self,fileName,OS,description,minimumMemory,maximumMemory):
			#number format checking
			try:
				if int(minimumMemory)<0 or int(maximumMemory)<int(minimumMemory):
					return shortcut.response('error', '', 'maximumMemory must larger or equal to minimumMemory')
			except:
				return shortcut.response('error', '', 'memory must be integer')
			
			infoHost=cacheFile.getDatabaseIP()
			db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
			cursor = db.cursor()
			
			#search for fileName (must ask to the nfs server)
			cursor.execute("SELECT `IPAddress` FROM `hosts` WHERE `isStorageHolder`=1")
			storageHolderIP=cursor.fetchone()[0]
			result=connection.socketCall(str(storageHolderIP),setting.LOCAL_PORT,'get_file_size',[setting.TEMPLATE_PATH+fileName])

			try:
				fileSize=int(json.loads(result)[0])
				if fileSize<=0:
					return shortcut.response('error', '', 'file not found')
			except:
				return shortcut.response('error', '', result)
			
			#check replication of fileName
			cursor.execute("SELECT `fileName` FROM `templates` WHERE `fileName`='%s'"%(fileName))
			if cursor.fetchone()!=None:
				return shortcut.response('error', '', 'fileName was used by other template')
			
			#template use different directory with guest
			#cursor.execute("SELECT `volumeFileName` FROM `guests` WHERE `volumeFileName`='%s'"%(fileName))
			#if cursor.fetchone()!=None:
			#	return shortcut.response('error', '', 'fileName was used by a guest')
			
			if not fileName.endswith('.img'):
				return shortcut.response('error', '', 'please set fileName in pattern of something.img format')

			cursor.execute('''
			INSERT INTO `templates` (`fileName`, `OS`, `description`, `minimumMemory`, `maximumMemory`,`size`,`activity`) VALUES
			('%(fileName)s', '%(OS)s', '%(description)s', '%(minimumMemory)s', '%(maximumMemory)s', '%(size)s', '%(activity)s');
			'''%{
			'fileName':fileName,
			'OS':MySQLdb.escape_string(OS),
			'description':MySQLdb.escape_string(description),
			'minimumMemory':minimumMemory,
			'maximumMemory':maximumMemory,
			'size':fileSize,
			'activity':0,
			})

			templateID=cursor.lastrowid
			
			db.close()

			content='<template templateID="%s" />'%(str(templateID))
			return shortcut.response('success', content)
			
		index.exposed = True

	getInfo = GetInfo()
	createFromGuest = CreateFromGuest()
	remove = Remove()
	add = Add()
	
