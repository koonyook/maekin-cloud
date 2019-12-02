import sys
import json

try:
	startTime=float(sys.argv[1])
	stopTime=float(sys.argv[2])
except:
	startTime=float(raw_input("startTime:"))
	stopTime=float(raw_input("stopTime:"))

IPList=[
'158.108.34.112',
]
#'158.108.34.112',
#'158.108.34.113',
#'158.108.34.114',
#'158.108.34.115',
#]

import subprocess,shlex
from util import connection,network,cacheFile
import MySQLdb

import setting

def cpuToPower(cpu):
	if cpu<0.0:	#sleep
		return 8.8
	elif cpu<50.0:
		return 63.8+22.0*(cpu/50.0)
	else:
		return 85.8+15.4*(cpu-50.0)/50.0

result = subprocess.Popen(shlex.split('''mkdir -p %s'''%(setting.ANALYSE_PATH)), stdout=subprocess.PIPE)
result.wait()

infoHost=cacheFile.getDatabaseIP()
db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
cursor = db.cursor()

#resolve hostID from IP
IDList=[]
for hostIP in IPList:
	cursor.execute("SELECT `hostID` FROM  `hosts` WHERE `IPAddress`='%s' "%(hostIP))
	tmp=cursor.fetchone()
	if tmp!=None:
		IDList.append(tmp[0])

powerList=[]

#get all sleep data
cursor.execute(''' 
	SELECT * FROM
	(SELECT `taskID`,`opcode`,TIMESTAMPDIFF(SECOND,'1970-01-01 00:00:00',`finishTimestamp`) as `finishTime`, `detail` FROM `tasks` WHERE `finishStatus`=1) as a
	WHERE (`opcode`=2003 OR `opcode`=2004) AND (`finishTime`>='%s' AND `finishTime`<='%s') ORDER BY `finishTime` '''%(startTime,stopTime))
hostAction=cursor.fetchall()

for hostID in IDList:
	#get all log data of cputime in time scope (1. HostLoad, 2. oldHostLoad )
	cursor.execute("SELECT `hostLoadID`,`timeStamp`,`idleTime`,`btime` FROM `oldHostLoad` WHERE `hostID`=%s and `timeStamp`>='%s' and `timeStamp`<='%s' "%(hostID,startTime,stopTime))
	allData = cursor.fetchall()
	cursor.execute("SELECT `hostLoadID`,`timeStamp`,`idleTime`,`btime` FROM `hostLoad` WHERE `hostID`=%s and `timeStamp`>='%s' and `timeStamp`<='%s' "%(hostID,startTime,stopTime))
	allData+=cursor.fetchall()
	#sort all data by timeStamp
	allData=sorted(allData,key=lambda x: x[1])
	
	#calculate log into list
	cal=[]
	for i in range(len(allData)):
		if i==len(allData)-1:
			break
		if allData[i][3]!=allData[i+1][3]:
			#difference btime
			continue
		#same btime
		timeRange=allData[i+1][1]-allData[i][1]
		idleDiff=allData[i+1][2]-allData[i][2]
		percentUsage=max(min(100.0-(idleDiff*100.0/(timeRange*2)),100.0),0.0)
		cal.append((allData[i][1], percentUsage))
	
	
	for action in hostAction:
		detail=json.loads(action[3])
		if detail['hostID']==str(hostID):
			if action[1]==2003: #close
				cal.append((float(action[2]),-1.0))
			elif action[1]==2004: #wake up
				cal.append((float(action[2]),101.0))
	
	cal=sorted(cal,key=lambda x: x[0])
	
	#cut data during sleep
	cleanData=[]
	i=0
	
	while i<len(cal):
		if cal[i][1]==-1.0:
			cleanData.append(cal[i])
			i+=1
			while i<len(cal):
				if cal[i][1]==101.0:
					cleanData.append((cal[i][0],0.0))
					i+=1
					break
				else:
					i+=1
		else:
			cleanData.append(cal[i])
			i+=1
	
	if cleanData==[]:
		cleanData.append((startTime,-1.0))

	#write clean data to file
	aFile=open(setting.ANALYSE_PATH+str(hostID)+"-cpu.csv",'w')
	aFile.write("%.7f,%.7f,%.2f\n"%(startTime,startTime-startTime,0.0))
	for x in cleanData:
		aFile.write("%.7f,%.7f,%.2f\n"%(x[0],x[0]-startTime,x[1]))
	aFile.close()
	#convert to power consumption sequence
	powerUsage=[]
	for x in cleanData:
		powerUsage.append((x[0],cpuToPower(x[1])))
	
	aFile=open(setting.ANALYSE_PATH+str(hostID)+"-pow.csv",'w')
	aFile.write("%.7f,%.7f,%.2f\n"%(startTime,startTime-startTime,cpuToPower(0.0)))
	for x in powerUsage:
		aFile.write("%.7f,%.7f,%.2f\n"%(x[0],x[0]-startTime,x[1]))
	aFile.close()

	powerList.append(powerUsage)

db.close()

#calculate sumation
sumPower=[]
n=len(IDList)
index=[0]*n
while True:
	#find host that provide next mintime
	minTime=-1
	targetIndex=-1
	for i in range(n):
		if index[i]+1 < len(powerList[i]) and (powerList[i][index[i]+1][0]<minTime or minTime==-1):
			minTime=powerList[i][index[i]+1][0]
			targetIndex=i
	
	if targetIndex!=-1:
		index[targetIndex]+=1
		sumWatt=0.0
		for i in range(n):
			sumWatt+=powerList[i][index[i]][1]
		sumPower.append((minTime,sumWatt))
	else:
		break

#write result to file
aFile=open(setting.ANALYSE_PATH+"power.csv",'w')
aFile.write("%.7f,%.7f,%.2f\n"%(startTime,startTime-startTime,0.0))
for x in sumPower:
	aFile.write("%.7f,%.7f,%.2f\n"%(x[0],x[0]-startTime,x[1]))
aFile.close()
