import json

import setting

initDict={
	'myLastIP':None,
	'masterDB':None,
	'masterDB_MAC':None,
	'slaveDB':None,
	'globalController':None,
	'network':None
}

def getCurrentDict():
	try:
		aFile=open(setting.CACHE_FILE,'r')
		currentDict=json.loads(aFile.read())
		aFile.close()
	except:
		currentDict=initDict
	
	return currentDict

def clearValue():
	setValue(myLastIP='-',masterDB='-',masterDB_MAC='-',slaveDB='-',globalController='-',network='-')

def setValue(myLastIP=None,masterDB=None,masterDB_MAC=None,slaveDB=None,globalController=None,network=None):
	'''
	set any value that not be None
	'-' is meaning of clear value
	'''
	currentDict=getCurrentDict()

	if myLastIP!=None:
		if myLastIP=='-':
			currentDict['myLastIP']=None
		else:
			currentDict['myLastIP']=str(myLastIP)
	if masterDB!=None:
		if masterDB=='-':
			currentDict['masterDB']=None
		else:
			currentDict['masterDB']=str(masterDB)
	if masterDB_MAC!=None:
		if masterDB_MAC=='-':
			currentDict['masterDB_MAC']=None
		else:
			currentDict['masterDB_MAC']=str(masterDB_MAC)
	if slaveDB!=None:
		if slaveDB=='-':
			currentDict['slaveDB']=None
		else:
			currentDict['slaveDB']=str(slaveDB)
	if globalController!=None:
		if globalController=='-':
			currentDict['globalController']=None
		else:
			currentDict['globalController']=str(globalController)
	if network!=None:
		if network=='-':
			currentDict['network']=None
		else:
			currentDict['network']=network		#network={'subnet','gateway','dns'}

	aFile=open(setting.CACHE_FILE,'w')
	aFile.write(json.dumps(currentDict))
	aFile.close()

	return currentDict

def getDatabaseIP():
	return getCurrentDict()['masterDB']

def getDatabaseMAC():
	return getCurrentDict()['masterDB_MAC']

def getSlaveDatabaseIP():
	return getCurrentDict()['slaveDB']

def getMyLastIP():
	return getCurrentDict()['myLastIP']

def getGlobalControllerIP():
	return getCurrentDict()['globalController']