import libvirt
import sys
from xml.dom import minidom

conA = libvirt.open(None)
if conA == None:
	print 'Failed to open connection to the hypervisor'
	sys.exit(0)

conB = libvirt.open("qemu+tls://158.108.34.12/system")
if conB == None:
	print 'Failed to open connection to the hypervisor'
	sys.exit(0)

print conA
print conB


#print conn.numOfDefinedDomains() #Provides the number of defined but inactive domains.
#print conn.listDefinedDomains()

print conA.numOfDomains()		#Provides the number of active domains.
domains=conA.listDomainsID()
dom=conA.lookupByID(domains[0])
print dom.name()
result=dom.migrate(conB,libvirt.VIR_MIGRATE_LIVE,None,None,0)
print result
#print libvirt.VIR_MIGRATE_LIVE	#found
#print libvirt.VIR_MIGRATE_CHANGE_PROTECTION #not found
#print libvirt.VIR_MIGRATE_NON_SHARED_DISK #not found
'''
for id in domains:
	print '|||||||||||||||||||||||||||||||||||||'
	dom=conn.lookupByID(id)
	print dom.UUIDString()
	info=dom.info()
	print info
	state=info[0]
	maxMem=info[1]	#(KB)
	memory=info[2]	#used mem (KB)
	nrVirtCpu=info[3] #number of cpu
	totalCpuTime=info[4]		#nanosec

	vcpus=dom.vcpus()
	virVcpuInfo=vcpus[0]
	print virVcpuInfo
	for vcpu in virVcpuInfo:
		number = vcpu[0] #number of vcpu
		state = vcpu[1]	#view enum virVcpuState {0:offline,1:running,2:blocked}
		cpuTime = vcpu[2] #nonosec
		cpu = vcpu[3] #real cpu number or -1 if offline
	canRunIn=vcpus[1]
	print vcpus[1] #do not use now
	
	print dom.memoryStats() #many os return blank dictionary
	#################################
	xmlString=dom.XMLDesc(0)
	#get path of interface and storage from xmlString
	doc=minidom.parseString(xmlString)
	diskPath=None
	for disk in doc.getElementsByTagName('disk'):
		if disk.attributes['device'].value == 'disk':
			diskPath=disk.getElementsByTagName('target')[0].attributes['dev'].value
			break
	ifPath=None
	for interface in doc.getElementsByTagName('interface'):
		if interface.attributes['type'].value == 'bridge':
			ifPath=interface.getElementsByTagName('target')[0].attributes['dev'].value
			break
	if ifPath: 
		ifstat=dom.interfaceStats(ifPath) #use with network traffic [0]~rx [4]~tx 
		rx_bytes=ifstat[0]
		rx_packets=ifstat[1]
		rx_errs=ifstat[2]
		rx_drop=ifstat[3]
		tx_bytes=ifstat[4]
		tx_packets=ifstat[5]
		tx_errs=ifstat[6]
		tx_drop=ifstat[7]
		print rx_bytes,tx_bytes
	if diskPath:
		hdstat=dom.blockStats(diskPath)  #use with disk io [1]~read [3]~write
		readRequest=hdstat[0]
		readBytes=hdstat[1]
		writeRequest=hdstat[2]
		writeBytes=hdstat[3]
		print readBytes,writeBytes
'''
