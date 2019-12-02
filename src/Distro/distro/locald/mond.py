import sys, time
from socket import *
import json
import setting

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor, task
from twisted.application.internet import MulticastServer

from daemon.daemon import Daemon
from util import cputil, ifutil, memutil

#from Middleware.util import connection
#from Middleware.util import general

class hostmonld(Daemon):
	
	def run(self):
		reactor.listenMulticast(5555, Helloer())
		reactor.run()
		#connection.runserver(5556, general.getCommandDict(import))

class Helloer(DatagramProtocol):
	channel_port = setting.HMM_MULTICAST_PORT
	channel_group = setting.HMM_MULTICAST_ADDRESS
	node = []

	def startProtocol(self):
		self.myip = [ip for ip in gethostbyname_ex(gethostname())[2] if not ip.startswith("127.")][0]
		self.transport.joinGroup(self.channel_group)
		#self.greeting('hello_maekin')
		self.transport.write('hello_maekin', (self.channel_group, self.channel_port))
		chkAlive = task.LoopingCall(isAlive)
		task.start(random.randrange(1,100,1)/float(50))

	def datagramReceived(self, data, (host, port)):
		if data == 'hello_maekin' and host not in self.node and host != self.myip:
			self.node.append(host)
			f = open(setting.MAEKIN_VAR_PATH + 'phyhost', 'w')
			f.write(str(self.node))
			print 'n>' + host
			self.transport.write('hello_maekin', (host,self.channel_port))
		elif data == 'bye_maekin' and host in self.node:
			self.node.remove(host)
		elif data == 'ruok?':
			self.transport.write('alive', (self.channel_group, self.channel_port))
		elif data == 'get_host_spec':
			rdata = {}
			rdata['IP'] = node[0]

			cpuinfo = {}
			cpuinfo['number'] = len(cputil.getInfo())
			cpuinfo['model'] = cputil.getInfo()[0]['model name']
			cpuinfo['cache'] = cputil.getInfo()[0]['cache size']

			meminfo = {}
			memtotal, unit = memutil.getInfo()[0]['MemTotal'][0]
			meminfo['size'] = memtotal + ' ' + unit
			meminfo['type'] = 'HOD'
			meminfo['speed'] = 'HOD'

			spec = {'cpu':cpuinfo, 'memory':meminfo}
			rdata['spec'] = spec

			self.transport.write(json.dumps(rdata), (host, 5555))

	def isAlive():
		node = []
		self.transport.write('ruok?', (self.channel_group, self.channel_port))

	def greeting(self, msg):
		# Send UDP broadcast packets
		'''
		s = socket(AF_INET, SOCK_DGRAM)
		s.bind(('', 0))
		s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
		'''
		#data = repr(time.time()) + '\n'
		#data = 'maekinhost'
		#s.sendto(msg, ('<broadcast>', self.broadcast_port))
		
