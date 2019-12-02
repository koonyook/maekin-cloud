import setting
from util import connection,cacheFile,network,general
from util import shortcut
from dhcp import dhcpController
from scheduling import mission

import MySQLdb
import json
import os
import random
import time

def simple_mission(taskID,detail):
	'''
	first mission in queuing (must do quickly)
	'''
	subTask=detail['subTask']
	
	#infoHost=cacheFile.getDatabaseIP()
	#db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	#cursor = db.cursor()
	#cursor.execute("SELECT `createTimestamp` FROM `tasks` WHERE `taskID`=%s"%(str(taskID)))
	#createTimestamp=cursor.fetchone()[0]
	#db.close()

	detailList=[]

	detailList.append({'command':'task_b'})
	detailList.append({'command':'task_a'})
	detailList.append({'command':'task_b'})
	for i in range(int(subTask)):
		detailList.append({
			'command':'simple_task',
			'waitTime':str(i)
		})

	success=mission.addSubTasks(taskID,detailList)
	if success:
		return 'OK'
	else:
		return "addSubtasks fail"

def simple_mission_ending(taskID):
	'''
	this task will invoke when simple_mission finish all subTask
	'''
	finishMessage="I pass this mission"
	print shortcut.storeFinishMessage(taskID,finishMessage)
	print "mission finish store message"

	return "OK"

def simple_task(taskID,detail):
	'''
	first method for test task queuing
	'''
	waitTime=detail['waitTime']
	print waitTime
	time.sleep(int(waitTime))
	
	finishMessage="<abc>I can do it.</abc>"
	print shortcut.storeFinishMessage(taskID,finishMessage)
	#print "finish store message"

	return 'OK'

def task_a(taskID,detail):
	print 'task_a will sleep 10 sec'
	time.sleep(5)
	#i will create error
	a=int('a')
	time.sleep(5)
	print 'task_a finish'
	return 'OK'

def task_b(taskID,detail):
	print 'this is task_b: service dhcpd restart'
	dhcpController.restart()
	return 'OK'
