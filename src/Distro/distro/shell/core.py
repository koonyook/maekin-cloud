import os, time
import json
import subprocess

def start():
	#checkif hmm is running
	ps = subprocess.Popen("ps -eaf | grep hmm", shell=True, stdout=subprocess.PIPE)
	ps.wait()
	output = ps.communicate()[0]
	if output.find('hmm start') < 0:
		print 'hmm is not running'
		return None
	#else:
	#	print 'hmm running'

	#checkif /maekin/var/info exist?
	if not checkINFO():
		print 'info file not exist'
		return None
	
	
	updateint = 1	# seceonds

	while(True):
		header()
		try:
			currData = getCurrentData()
		except ValueError as ve:
			print 'Read error!'
		for host in currData:
			showBrief(host, currData[host])
		time.sleep(updateint)

def checkINFO():
	return os.path.isfile('/maekin/var/info')

def getCurrentData():
	try:
		f = open('/maekin/var/info')
	except IOError as e:
		print 'Something wrong? \'info\' not exist.'
	currentinfo = json.loads(f.read())
	return currentinfo

def getPID():
	try:
		f = open('/var/run/hmm.pid')
	except IOError as e:
		print 'pid file not exist.'
		return None
	return f.read()

def header():
	os.system('clear')
	pid = int(getPID())
	#rows, columns = os.popen('stty size', 'r').read().split()
	print 'HMM pid : %s' % str(pid)

def showBrief(hostname, hostdata):
	print 'Host : ' + hostname

	i = 0
	sum = 0 
	for attrib in hostdata['cpu_info']:
		i = i + 1
		sum = sum + float(attrib)
	print '    CPU Load : %.3f (%s core)' %(sum/i, i)

	print '    Memory : ',
	#for attrib in hostdata['memory_info']:
	mfree = int(hostdata['memory_info']['MemFree'][0])/1000
	mmax = int(hostdata['memory_info']['MemTotal'][0])/1000
	print '%s / %s MB' % (mmax-mfree, mmax)

	print '    Network : ',
	for attrib in hostdata['network_info']:
		if attrib['interface'] == 'eth0':
			print 'RX %s kb/s' % (int(attrib['rx'])/1000),
			print 'TX %s kb/s' % (int(attrib['tx'])/1000)
	#print '\tspec?'
	#for attrib in hostdata['spec']:
	#	print attrib
	print '\n',

def showDetail(hostname, hostdata):
	print '    Host : ' + hostname
	#for attrib in hostdata:
		#print '\t%s' % attrib
	'''	
	print '    Storage'
	#for attrib in hostdata['storage_info']:
	#	print attrib,
	#	print '%s kB' % hostdata['storage_info'][attrib]
	print '        VM image : %s kB' % hostdata['storage_info']['image_usage']
	print '        Capacity : %s kB' % hostdata['storage_info']['capacity']
	print '        Maekin used : %s kB' % hostdata['storage_info']['maekin_usage']
	print '        Free Space : %s kB' % hostdata['storage_info']['free']
	'''
	print '    CPU Load'
	i = 0
	for attrib in hostdata['cpu_info']:
		i = i + 1
		print '        Core %d : %s' % (i,attrib)

	print '    Memory : ',
	#for attrib in hostdata['memory_info']:
	mfree = int(hostdata['memory_info']['MemFree'][0])/1000
	mmax = int(hostdata['memory_info']['MemTotal'][0])/1000
	print '%s / %s MB' % (mmax-mfree, mmax)

	print '    Network'
	for attrib in hostdata['network_info']:
		if attrib['interface'] == 'lo':
			continue
		print '        ',
		print attrib['interface']
		print '            Receive %s kb/s' % (int(attrib['rx'])/1000)
		print '            Send    %s kb/s' % (int(attrib['tx'])/1000)
	#print '\tspec?'
	#for attrib in hostdata['spec']:
	#	print attrib
	print '    Last seen : ',
	print time.strftime("%a, %d %b %Y %H:%M:%S +0700", time.localtime(hostdata['last_seen']))
	print '\n',

if __name__ == '__main__':
	start()
