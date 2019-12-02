import time
import subprocess,shlex

import ping
import connection
import setting


def wakeAndWait(targetMAC,targetIP):
	
	#try to ping and hello
	while ping.check(targetIP,2)==False:
		subprocess.Popen(shlex.split("ether-wake -i br0 %s"%(str(targetMAC))))
		pass
	
	#check with socketCall until mklocd is up
	while True:
		result=connection.socketCall(targetIP,setting.LOCAL_PORT,'hello')
		if result=='OK':
			break
		else:
			time.sleep(2)
