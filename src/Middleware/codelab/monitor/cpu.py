import libvirt
import time
import sys
from xml.dom import minidom

def getDiskPath(domain):
	dom=domain
	xmlString=dom.XMLDesc(0)
	doc=minidom.parseString(xmlString)
	diskPath=None
	for disk in doc.getElementsByTagName('disk'):
		if disk.attributes['device'].value == 'disk':
			diskPath=disk.getElementsByTagName('target')[0].attributes['dev'].value
			break
	return diskPath

def getInterfacePath(domain):
	dom=domain
	xmlString=dom.XMLDesc(0)
	doc=minidom.parseString(xmlString)
	ifPath=None
	for interface in doc.getElementsByTagName('interface'):
		if interface.attributes['type'].value == 'bridge':
			ifPath=interface.getElementsByTagName('target')[0].attributes['dev'].value
			break
	return ifPath

conn = libvirt.open(None)
if conn == None:
	print 'Failed to open connection to the hypervisor'
	sys.exit(0)

pre={}
while True:
	domains = conn.listDomainsID()
	for id in domains:
		dom=conn.lookupByID(id)
		print dom.name()
		######TIME ZONE######
		if not (id in pre.keys()):
			pre[id]={'timestamp':time.time()}
		else:
			newTimestamp=time.time()
			timeRange=newTimestamp-pre[id]['timestamp']
			pre[id]['timestamp']=newTimestamp 
		
		#######CPU ZONE#########
		if not ('cpuTime' in pre[id].keys()):
			pre[id]['cpuTime']=dom.info()[4]
		else:
			newCpuTime=dom.info()[4]
			cpuTimeRange=newCpuTime-pre[id]['cpuTime']
			percentCPU=(cpuTimeRange*100.0)/(timeRange*1000.0*1000.0*1000.0*dom.info()[3])
			
			pre[id]['cpuTime']=newCpuTime
			print "cpuUsage",max(0.0, min(100.0, percentCPU))
		
		#######IF ZONE#########
		ifPath=getInterfacePath(dom)
		if ifPath:
			ifStat=dom.interfaceStats(ifPath)
			rxBytes=ifStat[0]
			txBytes=ifStat[4]
			if not ('rxBytes' in pre[id].keys()):
				pre[id]['rxBytes']=rxBytes
				pre[id]['txBytes']=txBytes
			else:
				rxRange=rxBytes-pre[id]['rxBytes']
				txRange=txBytes-pre[id]['txBytes']
				rateRx=rxRange/timeRange 	#Bytes per sec
				rateTx=txRange/timeRange
				
				pre[id]['rxBytes']=rxBytes
				pre[id]['txBytes']=txBytes
				print "rateRx",rateRx,"rateTx",rateTx
		else:
			pass	#do nothing about interface
			
		#######IO ZONE########
		diskPath=getDiskPath(dom)
		if diskPath:
			diskStat=dom.blockStats(diskPath)
			readBytes=diskStat[1]
			writeBytes=diskStat[3]
			if not ('readBytes' in pre[id].keys()):
				pre[id]['readBytes']=readBytes
				pre[id]['writeBytes']=writeBytes
			else:
				readRange=readBytes-pre[id]['readBytes']
				writeRange=writeBytes-pre[id]['writeBytes']
				rateRead=readRange/timeRange
				rateWrite=writeRange/timeRange
				
				pre[id]['readBytes']=readBytes
				pre[id]['writeBytes']=writeBytes
				print "rateRead",rateRead,"rateWrite",rateWrite
		else:
			pass	#do nothing about disk io
		print "================================================="
	time.sleep(2)
