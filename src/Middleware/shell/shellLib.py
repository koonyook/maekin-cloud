#main method is start()

#this shell can run on any computer that install maekin package [that provide middleware library for me]
import sys
import urllib
import time
import types
from xml.dom import minidom
import re
import traceback
import MySQLdb

import setting
from util import cacheFile
from util import network
from util import general
import shellMethod
import static

def start():
	#classify that this is a host of cloud or not
	apiIP=None
	apiPort=None
	infoHostIP=cacheFile.getDatabaseIP()
	
	if infoHostIP!=None:
		try:
			db = MySQLdb.connect(infoHostIP, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
			cursor = db.cursor()
			cursor.execute("SELECT `IPAddress` FROM `hosts` WHERE `isGlobalController`=1")
			apiIP=cursor.fetchone()[0]
			db.close()
			apiPort=setting.API_PORT
		except:
			apiIP=None
			print "Cannot connect to api automaticaly."
	while True:
		#loop to connect to api
		if apiIP==None:
			apiData=raw_input("Please insert ip address and port of api (ex. 111.222.33.4:1010) \n or type `quit` to exit :")
			
			if apiData=='quit':
				return

			try:
				apiIP,apiPort=apiData.split(':')
				network.IPAddr(apiIP)
			except:
				print "Invalid IP Address or port"
				apiIP=None
		
		#try to connect to mkapi
		if apiIP!=None:
			try:
				returnFile=urllib.urlopen("http://%s:%s/connect/getToken"%(str(apiIP),str(apiPort)))
				token=returnFile.read()
				break
			except IOError:
				print "Connect to %s:%s error"%(str(apiIP),str(apiPort))
				apiIP=None

	#now we get apiIP that can use
	print "Connect to %s:%s success"%(str(apiIP),str(apiPort))
	
	commandDict=general.getCommandDict(shellMethod)

	while True:
		buffer=raw_input(static.BLUE_COLOR+"mksh>"+static.END_COLOR)
		
		buffer=buffer.strip()

		if buffer=='quit' or buffer=='exit':
			break
		
		result=runCommand(buffer,[apiIP,apiPort,token,commandDict])
		
		if isinstance(result, (dict,)):
			if 'newIP' in result.keys():
				apiIP=result['newIP']
			if 'newPort' in result.keys():
				apiPORT=result['newPort']
			if 'newToken' in result.keys():
				token=result['newToken']


def runCommand(buffer,param):
	commandDict=param[3]

	argv=buffer.split(' ')
	try:
		while True:
			argv.remove('')
	except:
		pass
	
	if len(argv)==0:
		return None

	if argv[0] not in commandDict.keys():
		print 'command %s not found, use "help" command to see the command list or use "quit" to exit.'%(argv[0])
		return None

	try:
		return commandDict[argv[0]](argv[1:len(argv)],param)
	except:
		print "unexpected error:"
		traceback.print_exc()
