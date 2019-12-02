import setting

from util import network,cacheFile,ping,general
from util import connection
from util import debugger
from info import dbController
from dhcp import dhcpController
from service import globalService

import os
import time
import threading
import subprocess,shlex
import libvirt
import MySQLdb
import json
import shutil
from xml.dom import minidom

from util.xmlUtil import getValue
from util import network 

def get_local_raw_guest_data(argv):
	'''
	send raw data of every guest from libvirt api
	'''
	myIP=network.getMyIPAddr()
	result=[]

	conn = libvirt.open(None)
	if conn == None:
		print 'Failed to open connection to the hypervisor'
		return

	domainIDList=conn.listDomainsID()
	for domainID in domainIDList:
		domainDict={}
		dm=conn.lookupByID(domainID)
		dom=minidom.parseString(dm.XMLDesc(0))
		domainDict['MACAddress']=getValue(dom,'mac','address')
		domainDict['UUID']=dm.UUIDString().replace('-','')
		domainDict['runningState']=dm.info()[0]
		domainDict['name']=dm.name()
		domainDict['isActive']=dm.isActive()
		
		domainDict['hostIP']=str(myIP)
		result.append(domainDict)

	return json.dumps(result)