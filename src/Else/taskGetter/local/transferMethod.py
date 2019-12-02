import os
import socket
import time
import threading
import subprocess,shlex
import json

import setting

def get_time_log_file(argv):
	try:
		aFile=open(setting.TIME_LOG_FILE,'r')
		content=aFile.read()
		aFile.close()
	except:
		content="File not found"

	return content

def get_file(argv):
	try:
		targetFile=argv[0]
	
		aFile=open(targetFile,'r')
		content=aFile.read()
		aFile.close()
	except:
		content="File not found"

	return content