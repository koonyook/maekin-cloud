#import setting (don't import setting)
import random
import os
import subprocess, shlex
import types
import inspect
import time

def getCurrentTime():
	return time.time()-time.timezone

def getOuterFunctionName():
	outerFunctionName=None
	frame = inspect.currentframe()
	try:
		outerFunctionName=inspect.getouterframes(frame)[3][3]	#very specific in a work
	finally:
		del frame
	return outerFunctionName

def getCommandDict(*modules):
	'''
	when you call
		from local import method
	method is a module
	'''
	result={}
	for module in modules:		
		for command in dir(module):
			if command.startswith('__') and command.endswith('__'):
				continue
			if type(module.__dict__[command]) is not types.FunctionType:
				continue
			elif module.__dict__[command].__module__ != module.__name__:
				continue
			else:
				if command in result.keys():
					print "warning: replicated method name "+str(command) 
				else:
					result[command]=module.__dict__[command]

	return result

def runDaemonCommand(command,conn=None,sock=None,pipe=True):
	'''
	run command with opened socket should be controll
	'''
	if conn==None and sock==None:
		forking=False
		pid=0	
	else:
		forking=True
		pid=os.fork()
		
	if pid==0: #child
		if conn:
			conn.close()
		if sock:
			sock.close()

		if pipe:
			result = subprocess.Popen(shlex.split(command),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		else:
			result = subprocess.Popen(shlex.split(command))
		
		result.wait()
		
		if forking==True:
			os._exit(0)
	else:
		os.waitpid(pid,0)	#block until child finish
	
	if forking==False:
		return result
	else:
		return True

def isUUID(uuid):
	if type(uuid) not in [type('string'),type(u'unicode')]:
		return False
	uuid = uuid.replace('-','')
	if len(uuid)!=32:
		return False
	for c in uuid:
		if not (c in ['0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f']):
			return False
	return True

def transformUUID(hexString):	#for uuid only
	ret = ''
	for i in range(16):
		ret=ret+chr(int(hexString[i*2:i*2+2],16))
	return ret

def randomOne(aList):
	length=len(aList)
	if length==0:
		return None
	
	randomNumber=random.randint(0,length-1)

	return aList[randomNumber]

def imgToSav(imgFileName):
	'''
	input : 'djlksjfl.img'
	output: 'djlksjfl.sav'
	'''
	savFileName = imgFileName.split('.')
	savFileName[-1]='sav'
	savFileName = '.'.join(savFileName)

	return savFileName