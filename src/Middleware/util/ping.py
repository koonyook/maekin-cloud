import time
import subprocess,shlex
import re

def check(targetIP,timeout=2):
	result = subprocess.Popen(shlex.split('''ping -c 1 -W %d %s'''%(timeout,str(targetIP))), stdout=subprocess.PIPE)
	result.wait()
	output=result.communicate()[0]
	success = re.search(r",\s*(?P<SUCCESS>\d+)\s+received,",output).groupdict()['SUCCESS']
	if int(success)>0:
		return True
	else:
		return False