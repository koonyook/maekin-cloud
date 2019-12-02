import setting

from util import connection,general,cacheFile,network
from util import shortcut
from info import dbController

from service import caService,dbService,nfsService,globalService

import MySQLdb
import json

class Task(object):

	class Poll():
		def index(self,taskID):
			infoHost=cacheFile.getDatabaseIP()
			db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
			cursor = db.cursor()
			
			cursor.execute('''SELECT `opcode`,`detail`,`status`,`finishStatus`,`finishMessage`,`createTimestamp`,`finishTimestamp`
				FROM `tasks` WHERE `taskID`=%s
			'''%(str(taskID)))
			db.close()
			
			taskData=cursor.fetchone()

			if taskData==None:
				return shortcut.response('error', '', 'taskID not found')
			
			templateString=open(setting.MAIN_PATH+'webapi/template/task_poll.xml').read()
			content=templateString%{
				'taskID':str(taskID),
				'opcode':str(taskData[0]),
				'detail':taskData[1],
				'status':str(taskData[2]),
				'finishStatus':str(taskData[3]),
				'finishMessage':taskData[4],
				'createTimestamp':taskData[5],
				'finishTimestamp':taskData[6]
			}

			return shortcut.response('success', content)

		index.exposed = True

	poll = Poll()
