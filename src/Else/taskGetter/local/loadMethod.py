import os
import socket
import time
import threading
import subprocess,shlex
import json
from threading import Timer
#import __builtin__

from util.general import getOuterFunctionName
from util.general import getCurrentTime
import setting

class Collector():
	def __init__(self,argv):
		self.startTime=getCurrentTime()
		self.workType=getOuterFunctionName()
		self.argv=argv
	
	def finish(self):
		self.finishTime=getCurrentTime()
		aFile=open(setting.TIME_LOG_FILE,'a')
		aFile.write("%s %.7f %.7f %.7f %s\n"%(self.workType,self.startTime,self.finishTime,self.finishTime-self.startTime,json.dumps(self.argv)))
		aFile.close()

class TimeThread(threading.Thread):
	def __init__(self,argv):
		#if len(__builtin__.pidList)>0:
		#	targetpid=__builtin__.pidList[-1]
		#	del __builtin__.pidList
		#	print "wait for",targetpid
		#	os.waitpid(targetpid,0)
		#	print "run my work"
		threading.Thread.__init__(self)
		self.timer=Collector(argv)
	
	def run(self):
		self.realWork()
		self.timer.finish()

#########################
######## EXAMPLE ########
#########################

class testThread(TimeThread):
	def realWork(self):
		time.sleep(3)

def test_type(argv):
	'''
	example
	'''
	testThread(argv).start()	#start new thread

	return "OK"

###################################

class softThread(TimeThread):
	def realWork(self):
		total=1
		i=1
		while i<10000:
			total*=i
			i+=1
		result=len(str(total))
				

def soft_work(argv):
	'''
	example
	'''
	softThread(argv).start()	#start new thread

	return "OK"


##########################################
##########################################

def frange(start,stop,step):
	result=[]
	r = start
	while r < stop:
		result.append(r)
		r += step
	
	return result

class TaskPlan:
	def __init__(self,workType,startTime,stopTime,frequency,argv):
		self.workList=[]
		self.totalWork=0
		self.errorWork=0
		self.argv=argv
		
		for sec in frange(startTime,stopTime,frequency):
			self.workList.append((sec,workType))
		print "workList:", len(self.workList)
		
	def runScenario(self,zeroPoint):
		self.zeroPoint=zeroPoint
		self.runNextGroup(0)
	
	def runNextGroup(self,startIndex):
		for i in range(startIndex,startIndex+10): #10=concurrent_size
			if i<len(self.workList):
				Timer(self.workList[i][0]+self.zeroPoint-getCurrentTime(),self.do_work,(i,)).start()
				lastIndex=i

		if lastIndex+1<len(self.workList):
			Timer(self.workList[lastIndex][0]-2+self.zeroPoint-getCurrentTime(),self.runNextGroup,(lastIndex+1,)).start()
		
	def do_work(self,i):
		#real work from self.workList[i]
		#print "%.2f"%(getCurrentTime()-self.zeroPoint), self.workList[i]
		work=self.workList[i]
		
		result=eval(work[1]+'(self.argv)')
		self.totalWork+=1
		if result=='OK':
			pass
		else:	#error
			self.errorWork+=1
	
	def getLastTime(self):
		return self.workList[-1][0]
	
	def dummy(self):
		print "finish this work set"

class SetWork(threading.Thread):
	def __init__(self,detail,argv,closeConnEvent):
		threading.Thread.__init__(self)
		self.workType=detail[0]
		self.frequency=detail[1]
		self.usageTime=detail[3]-detail[2]
		self.argv=argv
		self.closeConnEvent=closeConnEvent
	
	def run(self):
		self.closeConnEvent.wait()
		zeroPoint=getCurrentTime()+5.0
		pid=os.fork()
		
		if pid==0:
			st=0.0
		else:
			myPID=os.getpid()
			childPID=pid
			os.system("taskset -p 0x00000001 %d"%(myPID))
			os.system("taskset -p 0x00000002 %d"%(childPID))

			#subprocess.Popen(shlex.split("taskset -p 0x00000001 %d"%(myPID)))
			#subprocess.Popen(shlex.split("taskset -p 0x00000004 %d"%(childPID)))
			st=0.0+self.frequency

		plan=TaskPlan(self.workType,st,self.usageTime,self.frequency*2,self.argv)
		Timer(0.0, plan.runScenario, (zeroPoint,)).start()
		Timer(zeroPoint+plan.getLastTime()+10-getCurrentTime(), plan.dummy, ()).start()
		
		if pid!=0: #parent
			os.wait()


def set_work(argv):
	'''
	argv[0]=json[workType,frequent,startTime,stopTime]
	argv[1]=json[argv]
	argv[2]={socket_connection}=[conn,s,closeConnEvent]
	'''
	detail=json.loads(argv[0])
	closeConnEvent=argv[2][2]
	argv=json.loads(argv[1])

	SetWork(detail,argv,closeConnEvent).start()	#start new thread

	return "OK"

