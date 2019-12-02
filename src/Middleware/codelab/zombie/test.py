import time
import os
import sys
import signal

child=[]

def handleSIGCHLD(signum,frame):
	#print "<<<<<<get signal>>>>>>>>>"
	#time.sleep(1)
	try:
		while (0,0)!= os.waitpid(-1, os.WNOHANG):
			pass
	except:
		pass
	#print ""
	#signal.signal(signal.SIGCHLD, handleSIGCHLD)

signal.signal(signal.SIGCHLD, handleSIGCHLD)

for i in range(5):
	pid=os.fork()
	if pid==0:
		if i==0:
			time.sleep(15)
		if i==1:
			time.sleep(5)
		if i==2:
			time.sleep(15)
		if i==3:
			time.sleep(5)
		if i==4:
			time.sleep(20)
		os._exit(0)
	else:
		child.append(pid)

#for pid in child:
#	os.waitpid(pid,0)

count=0
while True:
	time.sleep(0.1)
	count+=1
	print count
	#if count>=6:
	#	os.wait()

