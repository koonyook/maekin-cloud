import sys, time
from socket import *
import json
import copy
import setting

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor, task
from twisted.application.internet import MulticastServer

from daemon.daemon import Daemon
from util import cputil, ifutil, memutil, storageutil, logutil

#from Middleware.util import connection
#from Middleware.util import general

class mmond(Daemon):
	
	def run(self):
		reactor.listenMulticast(5555, PublishD())
		reactor.run()
		#connection.runserver(5556, general.getCommandDict(import))

class PublishD(DatagramProtocol):
	channel_port = 5555
	channel_group = '224.0.0.1'
	node = {}
	laststat = {}

	def startProtocol(self):
		#self.myip = [ip for ip in gethostbyname_ex(gethostname())[2] if not ip.startswith("127.")][0]
		self.myip = ifutil.getselfip('br0')
		while self.myip == None:
			time.sleep(10)
			self.myip = ifutil.getselfip('br0')

		self.transport.joinGroup(self.channel_group)
		#self.greeting('hello_maekin')
		pub = task.LoopingCall(self.publish)
		pub.start(1)

	def datagramReceived(self, data, (host, port)):
		if self.isSelf(host):
			return
		#print data
		if host not in self.node:
			self.node[host] = {}
		if data.find('hm;') != -1:
			info = json.loads(data.split(';')[1])
			self.node[host]['last_seen'] = time.time()
			for key in info:
				self.node[host][key] = info[key]		
		self.save()

	def isSelf(self, ip):
		return self.myip == ip

	def publish(self):
		data = self.getMine()
		try:
			self.transport.write( 'hm;' + json.dumps(data), (self.channel_group, self.channel_port) )
		except IOError, e:
		# an IOError exception occurred (socket.error is a subclass)
			if e.errno == 101:
				#do_some_recovery
				logutil.log('mmond','Warning','Network connectivity lost.')
			else:	# other exceptions we reraise again
				logutil.log('mmond','Warning','exception no {0}'.format(e.errno))
				raise
		self.node[self.myip] = data
		self.node[self.myip]['last_seen'] = time.time()
		self.save()

	def getMine(self):
		cpuinfo = {}
		cpuinfo['number'] = len(cputil.getInfo())
		cpuinfo['model'] = cputil.getInfo()[0]['model name']
		cpuinfo['cache'] = cputil.getInfo()[0]['cache size']
		cpuinfo['speed'] = cputil.getInfo()[0]['cpu MHz']
		
		meminfo = {}
		memtotal, unit = memutil.getInfo()['MemTotal']
		meminfo['size'] = memtotal + ' ' + unit
		meminfo['type'] = 'HOD'
		meminfo['speed'] = 'HOD'
		
		spec = {'cpu':cpuinfo, 'memory':meminfo}
		loadavg = cputil.getLoad()
		cmeminfo = memutil.getInfo()
		netinfo = ifutil.getInfo()
		#print netinfo
		#print len(self.lastif)
		# ------ convert tx,rx to rate -------
		if len(self.laststat) == 0:
			ifrate = []
			#self.lastif = copy.deepcopy(netinfo)
			self.laststat = netinfo
			for itf in netinfo:
			#	self.lastif[itf['interface']]={'tx':itf['tx'],'rx':itf['rx']}
				#itf['rx'] = '0'
				#itf['tx'] = '0'
				#netinfo[itf]['rx'] = '0'
				#netinfo[itf]['tx'] = '0'
				ifrate.append({'interface':itf,'tx':'0','rx':'0'})
		else:
			ifrate = []
			for itf in netinfo:
				if itf.find('vnet') >= 0:
					continue
				if itf not in self.laststat:
					continue
				ifrate.append({
					'interface' : itf,
					'tx' : str(int(netinfo[itf]['tx']) - int(self.laststat[itf]['tx'])),
					'rx' : str(int(netinfo[itf]['rx']) - int(self.laststat[itf]['rx']))
				})
			self.laststat = netinfo
		#print '-------------- netinfo ---------------'
		#print netinfo
		#print '-------------- lastif ----------------'
		#print self.lastif
		#print '-------------- ifrate ----------------'
		#print ifrate
		# ----- end ----
		storageinfo = storageutil.getInfo()
		
		#self.node[self.myip] = {'cpu_info' : loadavg, 'network_info':netinfo, 'spec':spec, 'memory_info':cmeminfo, 'storage_info':storageinfo, 'last_seen':time.time() }

		return {'cpu_info' : loadavg, 'network_info':ifrate, 'spec':spec, 'memory_info':cmeminfo, 'storage_info':storageinfo }

	def save(self):
		f = open( setting.MAEKIN_VAR_PATH + 'info' , 'w' )
		f.write( json.dumps( self.node ) )
		f.close()
