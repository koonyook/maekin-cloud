import subprocess,shlex
from util import connection,network

import setting


startIP="158.108.34.85"
stopIP="158.108.34.99"

for product in range(network.IPAddr(startIP).getProduct(),network.IPAddr(stopIP).getProduct()+1):
	currentIP=str(network.IPAddr(product))
	errorFlag=False
	try:
		content=connection.socketCall(currentIP,setting.LOCAL_PORT,'clean_shutdown')

	except:
		pass
	
	print currentIP,"shutdown"
