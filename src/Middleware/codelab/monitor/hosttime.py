import os
import time
import multiprocessing

jiffyPerSec=float(os.sysconf(os.sysconf_names['SC_CLK_TCK']))
cpu_count=int(multiprocessing.cpu_count())

oldTimestamp=-1
while True:
	timestamp=time.time()
	
	f=open('/proc/stat','r')
	data=f.readline().split(' ')
	if '' in data:
		data.remove('')
	f.close()
	idleTime=float(data[4])/jiffyPerSec
	
	if oldTimestamp!=-1:
		#print idleTime,oldIdleTime,idleTime-oldIdleTime
		#print timestamp,oldTimestamp
		print 100.0-(idleTime-oldIdleTime)*100.0/(cpu_count*(timestamp-oldTimestamp))	
	
	oldTimestamp=timestamp
	oldIdleTime=idleTime	

	time.sleep(1)
