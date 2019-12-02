import libvirt
import time
import sys,os
from xml.dom import minidom
import traceback
import multiprocessing

import setting
from util.general import getCurrentTime

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

def runMonitor():
	"""
	conn = libvirt.open(None)
	if conn == None:
		print 'Failed to open connection to the hypervisor'
		return
	"""
	cpu_count=multiprocessing.cpu_count()

	conn=None	#process in loop will fix it later

	pre={}

	counter=0
	try:
		while True:
			print counter
			counter+=1
			try:
				domains = conn.listDomainsID()
			except:
				print "listDomainsID error"
				time.sleep(1)
				#loop until i can get new connection
				print "Try to connect to hypervisor"
				while True:
					try:
						conn = libvirt.open(None)
						if conn!=None:
							print "Can connect to hypervisor"
							break
						else:
							print '.'
							time.sleep(1)
					except:
						print "an error happen"
						time.sleep(1)

				continue
			
			freshUUID=[]

			for id in domains:
				try:
					dom=conn.lookupByID(id)
				except:
					print "lookupByID error"
					break
				#print dom.name(),dom.UUIDString()
				infoString=''
				######TIME ZONE######
				if not (id in pre.keys()):
					firstTime=True
					pre[id]={'timestamp':getCurrentTime()}
				else:
					firstTime=False
					newTimestamp=getCurrentTime()
					timeRange=newTimestamp-pre[id]['timestamp']
					pre[id]['timestamp']=newTimestamp 
					infoString+="UPDATE:%s\n"%(str(newTimestamp))

				#######CPU ZONE#########
				try:
					if not ('cpuTime' in pre[id].keys()):
						pre[id]['cpuTime']=dom.info()[4]
					else:
						newCpuTime=dom.info()[4]
						cpuTimeRange=newCpuTime-pre[id]['cpuTime']
						#percentCPU=(cpuTimeRange*100.0)/(timeRange*1000.0*1000.0*1000.0*dom.info()[3])
						percentCPU=(cpuTimeRange*100.0)/(timeRange*1000.0*1000.0*1000.0*cpu_count)
					
						pre[id]['cpuTime']=newCpuTime
						#print "cpuUsage",max(0.0, min(100.0, percentCPU))
						infoString+="CPU_USAGE:%s\n"%(str(max(0.0, min(100.0, percentCPU))))
						infoString+="CPU_TIME:%s\n"%(str(newCpuTime))
				except:
					print 'ERROR at CPU ZONE'
					
				#######IF ZONE#########
				try:
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
							#print "rateRx",rateRx,"rateTx",rateTx
							infoString+="INTERFACE_RX_RATE:%s\n"%(str(rateRx))
							infoString+="INTERFACE_TX_RATE:%s\n"%(str(rateTx))
							infoString+="INTERFACE_RX_USED:%s\n"%(str(rxBytes))
							infoString+="INTERFACE_TX_USED:%s\n"%(str(txBytes))
					else:
						pass	#do nothing about interface
				except:
					print 'ERROR at INTERFACE ZONE'
				#######IO ZONE########
				try:
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
							#print "rateRead",rateRead,"rateWrite",rateWrite
							infoString+="DISK_READ_RATE:%s\n"%(str(rateRead))
							infoString+="DISK_WRITE_RATE:%s\n"%(str(rateWrite))
							infoString+="DISK_READ_USED:%s\n"%(str(readBytes))
							infoString+="DISK_WRITE_USED:%s\n"%(str(writeBytes))
					else:
						pass	#do nothing about disk io
				except:
					print 'ERROR at DISK_IO ZONE'  

				#print "================================================="
				#write data to the file
				if firstTime==False:
					targetFile=open(setting.CURRENT_INFO_PATH+dom.UUIDString().replace('-','')+'.info','w')
					targetFile.write(infoString)
					targetFile.close()
					freshUUID.append(dom.UUIDString().replace('-','')+'.info')
			
			#clear old file
			for afile in os.listdir(setting.CURRENT_INFO_PATH):
				if afile.endswith(".info") and (afile not in freshUUID):
					try:
						os.remove(setting.CURRENT_INFO_PATH+afile)
					except:
						continue

			time.sleep(setting.GUEST_MONITOR_PERIOD)
	except:
		print "errorerrorerrorerrorerror"
		traceback.print_exc()