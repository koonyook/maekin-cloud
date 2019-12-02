#import setting (don't import setting)
import random
import os
import subprocess, shlex
import types
import time
import re
import hashlib

def getCurrentTime():
	return time.time()-time.timezone

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

def runDaemonCommandUntilOK(command,conn=None,sock=None):
	'''
	run command with opened socket should be controll
	'''

	pid=os.fork()
		
	if pid==0: #child
		if conn:
			conn.close()
		if sock:
			sock.close()
		
		while True:
			result = subprocess.Popen(shlex.split(command),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
			
			result.wait()
			output=result.communicate()[0]
			match = re.search(r"FAILED",output)
			if match==None:
				break
			else:
				time.sleep(1)

		os._exit(0)
	else:
		os.waitpid(pid,0)	#block until child finish
	
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

def isGoodName(aName,allowDot=False):
	'''
	good name should contain alphabet and number only
	'''
	if allowDot:
		for char in aName:
			if not ( char=='.' or ('a'<=char and char<='z') or ('A'<=char and char<='Z') or ('0'<=char and char<='9')):
				return False
		return True
	else:
		for char in aName:
			if not (('a'<=char and char<='z') or ('A'<=char and char<='Z') or ('0'<=char and char<='9')):
				return False
		return True

def getFreeSpace(directoryPath):
	'''
	return free space of target directory in Byte
	'''
	p = subprocess.Popen(shlex.split('df -P '+directoryPath), stdout=subprocess.PIPE)
	p.wait()
	s = p.communicate()[0].strip().split('\n')[1]

	return int(s.strip().split()[3])*1024

def md5_for_file(filepath, block_size=2**20):
	'''
	return md5 hash of a file in hex digit
	'''
	f=open(filepath,'r')
	md5 = hashlib.md5()
	while True:
		data = f.read(block_size)
		if not data:
			break
		md5.update(data)
	f.close()
	return md5.hexdigest()
