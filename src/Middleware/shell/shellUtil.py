'''utility for shellMethod'''
import inspect
import sys, os, time                                                        
import urllib
import string
from xml.dom import minidom

from util.xmlUtil import getValue
import mychar
from util import cacheFile

import threading

class _Getch:
    """Gets a single character from standard input.  Does not echo to the
screen."""
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()

    def __call__(self): return self.impl()


class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()

getch = _Getch()		#from shellUtil import getch
                                                              


def getMyFunctionName():
	outerFunctionName=None
	frame = inspect.currentframe()
	try:
		outerFunctionName=inspect.getouterframes(frame)[1][3]
	finally:
		del frame
	return outerFunctionName

def requestTo(ip,port,path,token=None,data=None):
	try:
		returnFile=urllib.urlopen("http://%s:%s%s"%(str(ip),str(port),str(path)))
		result=returnFile.read()
	except: # IOError:
		return None
	
	return result

def requestAndWait(ip,port,path,token=None,data=None,backupIP=None):
	oldIP=ip
	oldPort=port
	oldToken=token

	taskInfo=requestTo(ip,port,path,token,data)
	dom = minidom.parseString(taskInfo)
	taskID=getValue(dom,'task','taskID')
	if taskID==None:
		return taskInfo
	
	counter=0
	loopRange=len(mychar.WAIT_LOOP)
	sys.stdout.write("\r\n") #for move up
	while True:
		taskInfo=requestTo(ip,port,'/task/poll?taskID=%s'%(taskID),token)
		if taskInfo==None:
			#error zone (1:migrateGlobalController, 2:close, 3:real error)
			time.sleep(3)
			taskInfo=requestTo(ip,port,'/task/poll?taskID=%s'%(taskID),token)
			if taskInfo==None and backupIP!=None:	#case of migrateGlobalController
				taskInfo=requestTo(backupIP,port,'/task/poll?taskID=%s'%(taskID),token)
			elif taskInfo==None and backupIP==None:		#case of close the host of globalController***
				#ask cacheFile until it update new global controller
				while True:
					newData=cacheFile.getGlobalControllerIP() 
					if newData!=None and newData!=ip:
						ip=newData
						break
					sys.stdout.write(mychar.MOVE_UP+mychar.CLEAR_LINE+"\r"+mychar.WAIT_LOOP[counter%loopRange]+" It's working, please wait.\r\n")
					time.sleep(1)
					counter+=1
				token=requestTo(ip,port,'/connect/getToken')
				taskInfo=requestTo(ip,port,'/task/poll?taskID=%s'%(taskID),token)
		if taskInfo==None:  # real error
			sys.stdout.write(mychar.CLEAR_LINE+'\rConnection error.\r\n')
			return None
		
		dom = minidom.parseString(taskInfo)
		status=getValue(dom,'status')
		if status=='0':
			sys.stdout.write(mychar.MOVE_UP+mychar.CLEAR_LINE+'\r'+mychar.WAIT_LOOP[counter%loopRange]+' Waiting in queue.\r\n')
		if status=='1':	#it's working
			#check progress
			progress=getValue(dom,'progress')
			if progress!=None:
				sys.stdout.write(mychar.MOVE_UP+mychar.CLEAR_LINE+'\r'+mychar.WAIT_LOOP[counter%loopRange]+' Progress: '+progress+"\r\n")
			else:
				sys.stdout.write(mychar.MOVE_UP+mychar.CLEAR_LINE+"\r"+mychar.WAIT_LOOP[counter%loopRange]+" It's working, please wait.\r\n")
		if status=='2':
			sys.stdout.write(mychar.CLEAR_LINE+'\rFinished.\r\n')
			if path.startswith("/host/close") or path.startswith("/host/remove"):
				if ip!=oldIP or port!=oldPort or token!=oldToken:
					return {
						'newIP':ip,
						'newPort':port,
						'newToken':token
						}
				else:
					return taskInfo
			else:
				return taskInfo

		time.sleep(1)
		counter+=1

def getTable(data):
	'''
	data is a list of truple
	*the first row is header of table
	
	table will be like this
+---------+------------------------------+--------------+
| ID      | host name                    | status       |
+---------+------------------------------+--------------+
	'''
	#print data
	column=len(data[0])
	maxList=[0]*column
	for element in data:
		for i in range(column):
			if len(str(element[i]))>maxList[i]:
				maxList[i]=len(str(element[i]))
	
	horizontal='+'
	for element in maxList:
		horizontal+=('-'*(element+2))+'+'
	horizontal+='\n'

	result=horizontal
	for i in range(len(data)):
		aline='|'
		for j in range(column):
			aline+=' '+str(data[i][j])+(' '*(maxList[j]-len(str(data[i][j]))))+' |'
		result+=aline+'\n'
		if i==0 or i==len(data)-1:
			result+=horizontal

	return result

class PressKeyThread ( threading.Thread ):
	def run ( self ):
		#print os.getpid()
		k=getch()	
		return

class MonitorPanel:
	
	def __init__(self):
		#sys.stdout.write(mychar.SAVE)
		self.alreadyPrint=False

	def update(self,data):
		if not self.alreadyPrint:
			sys.stdout.write(data.replace('\n','\r\n'))
			sys.stdout.write('\r\nPress any key to quit.\r\n')
			#move cursor back and save
			sys.stdout.write(mychar.MOVE_UP*(string.count(data,'\n')+2))
			sys.stdout.write(mychar.SAVE)
			self.alreadyPrint=True
		else:
			sys.stdout.write(mychar.RESTORE+mychar.CLEAR_DOWN)
			sys.stdout.write(data.replace('\n','\r\n'))
			sys.stdout.write('\r\nPress any key to quit.\r\n')
	
