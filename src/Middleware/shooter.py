#usage
#python shooter.py taskShooter/scenario01.txt rr &
#python shooter.py taskShooter/scenario01.txt &

concurrent_size=10
outputFile="/var/log/maekin.shooter.out"
errorFile="/var/log/maekin.shooter.err"

#clear log file
open(outputFile,'w').close()
open(errorFile,'w').close()

import setting

import sys,os
import time
import subprocess,shlex
import MySQLdb
import json

import sched, time
from threading import Timer

from util import connection,cacheFile
from util.general import getCurrentTime
from shell.shellUtil import requestTo

def frange(start,stop,step):
	result=[]
	r = start
	while r < stop:
		result.append(r)
		r += step
	
	return result

def printFinishTime():
	print "finishTime(+20) = %.7f"%(getCurrentTime())
	print "Conclusion"
	for guest in guestList:
		if guest.totalWork==0:
			print "%s error=%d total=%d"%(guest.ip,guest.errorWork,guest.totalWork)
		else:
			print "%s error=%d total=%d (%f percent error)"%(guest.ip,guest.errorWork,guest.totalWork,float(guest.errorWork)*100.0/float(guest.totalWork))

class GuestPlan:
	def __init__(self,ip):
		self.ip=ip
		self.workList=[]

		self.totalWork=0
		self.errorWork=0
	
	def addStart(self,sec,hostID=None):
		self.workList.append((sec,"start",hostID))
	
	def addStop(self,sec):
		self.workList.append((sec,"stop"))
	
	def addWork(self,workType,startTime,stopTime,frequency):
		#for sec in frange(startTime,stopTime,frequency):
		#	self.workList.append((sec,workType))
		self.workList.append((startTime,workType,stopTime,frequency))
	
	def sortTime(self):
		self.workList=sorted(self.workList,key=lambda x: x[0])
	
	def haveRightSequence(self):
		state=0
		for event in self.workList:
			if event[1]=='start':
				if state==0:
					state=1
				else:
					print "wrong start at",self.ip,"time =",event[0]
					return False
			elif event[1]=='stop':
				if state==1:
					state=0
				else:
					print "wrong stop at",self.ip,"time =",event[0]
					return False
			else: #work
				if state==0:
					print "wrong work at",self.ip,"work =",event[1],"time =",event[0]
					return False
			
		return True
	
	def runScenario(self,zeroPoint):
		self.zeroPoint=zeroPoint
		self.runNextGroup(0)
	
	def runNextGroup(self,startIndex):
		for i in range(startIndex,startIndex+concurrent_size):
			if i<len(self.workList):
				Timer(self.workList[i][0]+self.zeroPoint-getCurrentTime(),self.do_work,(i,)).start()
				lastIndex=i

		if lastIndex+1<len(self.workList):
			Timer(self.workList[lastIndex][0]-2+self.zeroPoint-getCurrentTime(),self.runNextGroup,(lastIndex+1,)).start()
		
	def do_work(self,i):
		#real work from self.workList[i]
		print self.ip,"%.2f"%(getCurrentTime()-self.zeroPoint), self.workList[i]
		work=self.workList[i]
		if work[1]=='start':
			globalIP=cacheFile.getGlobalControllerIP()
			if fixHost and work[2]!=None:
				result=requestTo(globalIP,setting.API_PORT,'/guest/startWithIP?guestIP=%s&targetHostID=%s'%(str(self.ip),work[2]))
			else:
				result=requestTo(globalIP,setting.API_PORT,'/guest/startWithIP?guestIP=%s'%(str(self.ip)))
		elif work[1]=='stop':
			globalIP=cacheFile.getGlobalControllerIP()
			result=requestTo(globalIP,setting.API_PORT,'/guest/forceOffWithIP?guestIP=%s'%(str(self.ip)))
		else:
			#result=connection.socketCall(self.ip,setting.LOCAL_PORT,work[1])
			result=connection.socketCall(self.ip,setting.LOCAL_PORT,'set_work',[json.dumps([work[1],work[3],work[0],work[2]]),json.dumps([]),'{socket_connection}'])
			self.totalWork+=1
			if result=='OK':
				pass
			else:	#error
				self.errorWork+=1
	
	def getLastTime(self):
		return self.workList[-1][2]
		#return self.workList[-1][0]

print "pid =",os.getpid()

sys.stdout.flush()
sys.stderr.flush()

#si = file(self.stdin, 'r')
so = file(outputFile, 'a+')
se = file(errorFile, 'a+', 0)

#os.dup2(si.fileno(), sys.stdin.fileno())
os.dup2(so.fileno(), sys.stdout.fileno())
os.dup2(se.fileno(), sys.stderr.fileno())

print "pid =",os.getpid()
inputFile=sys.argv[1]
try:
	option=sys.argv[2]
	if option=='rr':
		fixHost=True
	else:
		fixHost=False
except:
	fixHost=False

#inputFile="taskShooter/scenario.txt"
print "reading scenario data from",inputFile
aFile=open(inputFile,'r')
lines=aFile.readlines()
aFile.close()

guestList=[]
currentGuest=None
for line in lines:
	part=line.strip().split(' ')
	if part[0]=='ip':
		currentGuest=GuestPlan(part[1])
	elif part[0]=='start':
		try:
			tmpHostID=int(part[2])
		except:
			tmpHostID=None
		currentGuest.addStart(float(part[1])*60,tmpHostID)
	elif part[0]=='work':
		currentGuest.addWork(part[1],float(part[3])*60,float(part[4])*60,float(part[2]))
	elif part[0]=='stop':
		currentGuest.addStop(float(part[1])*60)
	elif part[0]=='end':
		guestList.append(currentGuest)
		currentGuest=None
	else:
		pass

maxLastTime=0
for guest in guestList:
	guest.sortTime()
	if not guest.haveRightSequence():
		print "please check",guest.ip
		sys.exit()
	if guest.getLastTime()>maxLastTime:
		maxLastTime=guest.getLastTime()
	
# work will start now
print "finish reading, shooting is starting in 5 seconds..."
zeroPoint=getCurrentTime()+5.0
print "startTime = %.7f"%(zeroPoint)
for guest in guestList:
	Timer(0.1, guest.runScenario, (zeroPoint,)).start()

Timer(zeroPoint+maxLastTime+20-getCurrentTime(), printFinishTime, ()).start()

