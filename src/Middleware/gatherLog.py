import subprocess,shlex
from util import connection,network

import setting

result = subprocess.Popen(shlex.split('''mkdir -p %s'''%(setting.TEST_LOG_PATH)), stdout=subprocess.PIPE)
result.wait()

startIP="158.108.34.85"
stopIP="158.108.34.85"

for product in range(network.IPAddr(startIP).getProduct(),network.IPAddr(stopIP).getProduct()+1):
	currentIP=str(network.IPAddr(product))
	errorFlag=False
	try:
		content=connection.socketCall(currentIP,setting.LOCAL_PORT,'get_time_log_file')
		if content==None or content=="File not found":
			errorFlag=True
	except:
		errorFlag=True
	
	print currentIP, (not errorFlag)
	if errorFlag==False:
		aFile=open(setting.TEST_LOG_PATH+currentIP+'.log','w')
		aFile.write(content)
		aFile.close()
