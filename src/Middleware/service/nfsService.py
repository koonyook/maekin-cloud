'''
every method in this file must can be called at any host
'''
import setting

from util import network,cacheFile
from util import connection
from util import debugger
from info import dbController

"""
def makeSlave(targetHostIP):
	'''
	very hard , i shouldn't do this
	'''
	return True

def promote(slaveHostIP=None):
	'''
	no makeSlave -> no promote
	'''
	return True
"""
def migrate(targetHostIP=None):
	'''
	very big work and can take many hours of process = not practical = leave it

	can do in only way of offline
	( close all vm, block all service, and move it across hosts)
	'''

	return True
