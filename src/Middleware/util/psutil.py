'''
process utility
'''
import os
import re
import time

def getPidList():
	return [pid for pid in os.listdir('/proc') if pid.isdigit()]


def waitProcessFinish(pid):
	if pid not in getPidList():
		return
	else:
		while True:
			try:
				statusString=open(os.path.join('/proc',pid,'status'),'r').read()
				match=re.search(r"Name:\s+(?P<NAME>.+)\nState:\s+(?P<STATE>.+)\nTgid:",statusString)
				name=match.groupdict()['NAME'].strip()
				state=match.groupdict()['STATE'].strip()
			except:
				break
			
			if name!='python' or state=='Z (zombie)':
				break
			else:
				time.sleep(1)
	return

"""
def killIfExist(processID):
	if existProcess(processID):
		killProcess(processID)
		
def killProcess(processID):
	os.kill(pid, signal.SIGKILL)
	killedpid, stat = os.waitpid(pid, os.WNOHANG)
	if killedpid == 0:
	print >> sys.stderr, "ACK! PROCESS NOT KILLED?"

def existProcess(processID):
"""


