'''
this module are splited from queue module to avoid loop of importing
do not merge this module with queue module
'''

from util import connection,cacheFile,network,general
import setting
import static

import MySQLdb
import json
import os
import traceback

def addSubTasks(parentTaskID,details):
	'''
	details is list of details (sort by sequence of doing)
	'''
	try:
		infoHost=cacheFile.getDatabaseIP()
		db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
		cursor = db.cursor()
		cursor.execute("SELECT `createTimestamp` FROM `tasks` WHERE `taskID`=%s"%(str(parentTaskID)))
		createTimestamp=cursor.fetchone()[0]
		db.close()
	except:
		print "something wrong with database"
		return False
	
	#add blank_task when details has no task
	if len(details)==0:
		details=[{'command':'blank_task'}]

	details.reverse()
	querySet=[]
	for detail in details:
		try:
			form = static.commandToDetail[detail['command']]
		except:
			print 'Error: no command found'
			return False
		
		opcode = form['opcode']

		for parameter in form['param']:
			if parameter not in detail.keys():
				print 'Error: parameter not found -> '+parameter
				return False
		
		if form['isMission']:
			isMission = 1
		else:
			isMission = 0
		
		querySet.append('''INSERT INTO `tasks` (`opcode`, `isMission`, `detail`, `createTimestamp`, `parentTaskID`) VALUES
		( %(opcode)s, %(isMission)s, '%(detail)s', '%(timestamp)s', %(parentTaskID)s);'''%
		{
			'opcode':str(opcode),
			'isMission':str(isMission),
			'detail':json.dumps(detail),
			'timestamp':str(createTimestamp),
			'parentTaskID':str(parentTaskID)
		})
	try:
		infoHost=cacheFile.getDatabaseIP()
		db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
		cursor = db.cursor()

		for query in querySet:
			cursor.execute(query)
		db.close()

		return True

	except:
		print "something wrong with database"
		return False
