import sys
try:
	startTime=float(sys.argv[1])
	stopTime=float(sys.argv[2])
except:
	startTime=float(raw_input("startTime:"))
	stopTime=float(raw_input("stopTime:"))

IPList=[
'158.108.34.85',
]
"""
'158.108.34.86',
'158.108.34.87',
'158.108.34.88',
'158.108.34.89',
'158.108.34.90',
'158.108.34.91',
'158.108.34.92',
'158.108.34.93',
'158.108.34.94',
]
'158.108.34.95',
'158.108.34.96',
'158.108.34.97',
'158.108.34.98',
'158.108.34.99',
]
"""
workList=[
'soft_work',
]

import subprocess,shlex
from util import connection,network
import MySQLdb
import setting

result = subprocess.Popen(shlex.split('''mkdir -p %s'''%(setting.ANALYSE_PATH)), stdout=subprocess.PIPE)
result.wait()

for workType in workList:
	timeData=[]
	for currentIP in IPList:
		lines=open(setting.TEST_LOG_PATH+currentIP+'.log','r').readlines()
		for line in lines:
			part=line.strip().split(' ')
			if part[0]==workType and float(part[1])>startTime and float(part[1])<stopTime:
				timeData.append((part[1],part[3]))
	
	#write result to file
	aFile=open(setting.ANALYSE_PATH+workType+"-time.csv",'w')
	for x in timeData:
		aFile.write("%s,%.7f,%s\n"%(x[0],float(x[0])-startTime,x[1]))
	aFile.close()
