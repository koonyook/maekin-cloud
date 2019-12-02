import time
import thread
import threading
import sys
import os
import signal

class childThread ( threading.Thread ):
	def run ( self ):
		x=99.1234
		while True:
			x=(x*x+x)/(x+1)
			y=(3*x)
			x=y-x

x=int(raw_input("How many thread? :"))

for i in range(x):
	childThread().start()

raw_input("Press enter to stop process...")
myPID=os.getpid()
os.kill(myPID,signal.SIGTERM)
