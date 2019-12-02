import sys
import shlex, subprocess
import os

import signal
import sys

sys.path.append("/maekin/lib/distro")
import setting
sys.path.append(setting.MAEKIN_LIB_PATH)
from middleware.util import connection
from util import ifutil
from util import general

class insertNode():
	def __init__(self):
		self.pxe_client = {}
		signal.signal(signal.SIGINT, self.signal_handler)
		self.gotIP = ifutil.getselfip('br0') != None

	'''
	check for httpd and tftp-server
	'''
	def checkRPM(rpm_name):
		cmd = 'rpm -q ' + rpm_name
		args = shlex.split(cmd)
		p = subprocess.Popen(args, stdout=subprocess.PIPE)
		p.wait()
		if p.communicate()[0].find('not installed') == -1:
			return True
		else:
			return False
	
	def prepareKS(self):
		ks_inherit = open(setting.MAEKIN_VAR_PATH+'anaconda-ks.cfg').read()
		inherit_data = {}
		inherit_data['server_ip'] = setting.PRIVATE_NETWORK_IP;
		partition_info = ''
		part_line = []
		log_vol_group_line = []
		for line in ks_inherit.split('\n'):
			if line.find('lang') >= 0:
				inherit_data['lang'] = line
			elif line.find('keyboard') >= 0:
				inherit_data['keyboard'] = line
			elif line.find('timezone') >= 0:
				inherit_data['timezone'] = line
			elif line.find('bootloader') >= 0:
				inherit_data['bootloader'] = line
			elif line.find('clearpart') >= 0 :
				partition_info = 'clearpart --initlabel --all\n'
			elif line.find('part') == 1:
				part_line.append(line.replace('#','') + '\n')
				#partition_info += line.replace('#','') + '\n'
			elif line.find('logvol') >= 0 or line.find('volgroup') >= 0:
				log_vol_group_line.append(line.replace('#','') + '\n')
				#partition_info += line.replace('#','') + '\n'
		for line in part_line:
			partition_info += line.replace('#','')
		for line in log_vol_group_line:
			partition_info += line.replace('#','')
		
		inherit_data['partitioninfo'] = partition_info
		
		inherit_data['rootpw'] = open('/etc/shadow', 'r').readline().split(':')[1]
		
		#for d in inherit_data:
			#print d,':', inherit_data[d]
		#	print d
		#return
		#print open(setting.MONITOR_MODULE_PATH+'template/ks.cfg').read()
		#return 
		ksfile = open(setting.MONITOR_MODULE_PATH+'template/ks.cfg').read()%inherit_data;
		f = open('/var/pxe/maekin/ks/ks.cfg', 'w')
		f.write( ksfile )
		f.close()

		noksfile = open(setting.MONITOR_MODULE_PATH+'template/noks.cfg').read()%inherit_data;
		f = open('/var/pxe/maekin/ks/noks.cfg', 'w')
		f.write( noksfile )
		f.close()
		print '%s[  %s  ]'%(general.TAB, general.green('OK'))
		
	'''
	config tftp-server	restart tftp-server
	'''
	def startTFTP(self):
		# enable tftp-server
		tftpsetting = open(setting.MONITOR_MODULE_PATH+'template/tftp').read()%{'tftp_disable':'no'}
		f = open('/etc/xinetd.d/tftp','w')
		f.write( tftpsetting )
		f.close()
		
		general.runsh('mkdir -p /var/lib/tftpboot/pxelinux.cfg/')
		pxesetting = open(setting.MONITOR_MODULE_PATH+'template/default').read()%{'server_ip':setting.PRIVATE_NETWORK_IP}
		f = open('/var/lib/tftpboot/pxelinux.cfg/default','w')
		f.write( pxesetting )
		f.close()

		general.runsh('service xinetd stop')
		print general.runsh('service xinetd start')[0],
		#print '%s[  %s  ]'%(general.TAB, general.green('OK'))

	def cleanupTFTP(self):
		tftpsetting = open(setting.MONITOR_MODULE_PATH+'template/tftp').read()%{'tftp_disable':'yes'}
		f = open('/etc/xinetd.d/tftp','w')
		f.write( tftpsetting )
		f.close()

		print general.runsh('service xinetd stop')[0],

	'''
	config httpd.conf	restart httpd
	'''
	def startHTTPD(self):
		httpdsetting = open(setting.MONITOR_MODULE_PATH+'template/pxeboot.conf').read()% \
			{	'network_id': setting.PRIVATE_NETWORK_ID ,
				'prefix' : setting.PRIVATE_PREFIX
			}
		f = open('/etc/httpd/conf.d/pxeboot.conf','w')
		f.write( httpdsetting )
		f.close()
		general.runsh('service httpd stop')
		print general.runsh('service httpd start')[0],
		#print '%s[  %s  ]'%(general.TAB, general.green('OK'))

	def cleanupHTTPD(self):
		os.unlink('/etc/httpd/conf.d/pxeboot.conf')
		try:
			open('/maekin/var/maekin-web')
		except IOError as e:
			#print 'Oh dear.'
			print general.runsh('service httpd stop')[0],
			return
		print general.runsh('service httpd reload')[0],

	'''
	config dhcpd.conf	restart dhcpd
	'''
	def startDHCPD(self):
		dhcpdsetting = open(setting.MONITOR_MODULE_PATH+'template/dhcpd.conf').read()% \
			{	'network_id': setting.PRIVATE_NETWORK_ID ,
				'netmask' : setting.PRIVATE_SUBNET,
				'ip_range' : setting.PRIVATE_RANGE,
				'server_ip' : setting.PRIVATE_NETWORK_IP,
				'host_declaration' : ''
			}
		f = open('/maekin/var/dhcp-distro.conf','w')
		f.write( dhcpdsetting )
		f.close()
		# create temp sub-interface
		subifsetting = open(setting.MONITOR_MODULE_PATH+'template/ifcfg-br0.1').read()% \
			{	'ip_addr': setting.PRIVATE_NETWORK_IP ,
				'netmask' : setting.PRIVATE_SUBNET,
			}
		f = open('/etc/sysconfig/network-scripts/ifcfg-br0.1','w')
		f.write( subifsetting )
		f.close()
		if general.runsh('ifup br0.1')[1] != '':
			print 'Exiting'
			exit(0)
		
		general.runsh('service dhcpd stop')
		print general.runsh('service dhcpd start')[0],
		#print '%s[  %s  ]'%(general.TAB, general.green('OK'))

	'''
	current_host = list of mac address
		[ '11:22:33:44:55:66' , 'aa:bb:cc:ee:dd:ff' ]
	'''
	def reloadDHCP(self):
		count = 0
		host_dec_string = ''
		for host in self.pxe_client:
			if self.pxe_client[host]['state'] != 'completed':
				host_dec_string += 'host netinstall%(netint_id)s { hardware ethernet %(netint_mac)s; fixed-address %(netint_ip)s; }\n'%{ 'netint_id' : str(count) , 'netint_mac' : host, 'netint_ip' : self.pxe_client[host]['ip']}
				count = count + 1
		dhcpdsetting = open(setting.MONITOR_MODULE_PATH+'template/dhcpd.conf').read()% \
			{	'network_id': setting.PRIVATE_NETWORK_ID ,
				'netmask' : setting.PRIVATE_SUBNET,
				'ip_range' : setting.PRIVATE_RANGE,
				'server_ip' : setting.PRIVATE_NETWORK_IP,
				'host_declaration' : host_dec_string
			}
		f = open('/maekin/var/dhcp-distro.conf','w')
		f.write( dhcpdsetting )
		f.close()
		
		general.runsh('service dhcpd restart')

	def cleanupDHCPD(self):
		os.unlink('/maekin/var/dhcp-distro.conf')
		general.runsh('touch /maekin/var/dhcp-distro.conf')

		general.runsh('ifdown br0.1')
		result = connection.socketCall('localhost',50000,'are_you_running_dhcpd',[])
		
		if result == 'yes':
			general.runsh('service dhcpd restart')
		else:
			print general.runsh('service dhcpd stop')[0],

	def signal_handler(self, signal, frame):
		print general.red('Exiting')
		print 'Doing some cleanup...',
		self.cleanupDHCPD()
		self.cleanupHTTPD()
		self.cleanupTFTP()
		if not self.gotIP:
			general.runsh('service mklocd start')[0]
			print 'Starting mklocd:%s[  %s  ]'%(general.TAB, general.green('OK'))
		sys.exit(0)

	def check_new_node(self,line):
		if line.find('DHCPACK') >= 0:
			ip, client_mac = line.split()[7],line.split()[9]
			result = connection.socketCall('localhost',50000,'have_this_mac',[client_mac])
			if result == 'yes':
				return
			if client_mac not in self.pxe_client.keys():
				#print 'New client(%s) connected, assigned to %s' % (client_mac,ip)
				self.pxe_client[client_mac] = {'ip' : ip, 'state':'pxe'}
				#return {'ip':ip,'mac':client_mac}
				self.reloadDHCP()
				self.show_ui()

	def check_ks_request(self,line):
		if line.find('ks.cfg') >= 0 and line.find('200') >= 0:
			ip = line.split()[0]
			for client in self.pxe_client:
				if self.pxe_client[client]['ip'] == ip:
					self.pxe_client[client]['state'] = 'kickstarting';
				self.reloadDHCP()
				self.show_ui()
	
	def check_install_request(self, line):
		if line.find('install.img') >= 0 and line.find('200') >= 0:
			ip = line.split()[0]
			for client in self.pxe_client:
				if self.pxe_client[client]['ip'] == ip:
					self.pxe_client[client]['state'] = 'installing';
				self.reloadDHCP()
				self.show_ui()
		if line.find('maekin-lib') >= 0 and line.find('200') >= 0:
			ip = line.split()[0]
			for client in self.pxe_client:
				if self.pxe_client[client]['ip'] == ip:
					self.pxe_client[client]['state'] = 'completed';
					self.create_pxe_localboot(client)
				self.reloadDHCP()
				self.show_ui()
		

	def create_pxe_localboot(self, mac):
		mac = mac.replace(':','-')
		general.runsh('cp /maekin/lib/distro/template/localboot /var/lib/tftpboot/pxelinux.cfg/01-'+mac)

	def show_ui(self):
		os.system('clear')
		print '= Insert-node : %s' %(general.green('READY'))
		print '= List ======== MAC ========= IP ====== STATE'
		
		if len(self.pxe_client) > 0:
			for client in self.pxe_client:
				state = self.pxe_client[client]['state']
				print '+ %s\t%s\t' %(client, self.pxe_client[client]['ip']),
				if state == 'pxe':
					print general.yellow(state)
				elif state == 'completed':
					print general.green(state)
					self.addToXML(client)
				else:
					print general.yellow(state)
		else:
			print '%s No one request for network installing!'%(general.red('+'))
			print '%s Waiting for new PXE client...'%(general.red('+'))
	
	def addToXML(self, mac):
		f = open(setting.MAEKIN_VAR_PATH+'startup.xml').read().split('\n')
		i = 1
		head = []
		tail = []
		mid = 0
		for l in f:
			if mid == 1 or l.find('</host>') >= 0:
				tail.append(l)
				mid = 1
			else:
				head.append(l)
		str = '\t\t\t<Bind MAC="%(MAC)s" IP="x.x.x.x" hostName="steam.your.domain.com" />'
		
		for line in head:
			if line.find(mac) >= 0:
				return
		
		f = open(setting.MAEKIN_VAR_PATH+'startup.xml','w')
		for l in head:
			f.write(l+'\n')
		f.write(str%{'MAC':mac}+'\n')
		for l in tail:
			f.write(l+'\n')
		f.close()
	
	def insert_procedure(self):
		# assume all package installed
		# checkRPM('httpd')
		# checkRPM('tftp-server')
		# cehckRPM('dhcpd')
		if not self.gotIP:
			#print 'Stoping mklocd: ',
			print general.runsh('service mklocd stop')[0],
			#print '%s[  %s  ]'%(general.TAB, general.green('OK'))
		
		print 'Prepareing kickstart file: ',
		try:
			self.prepareKS()
		except Exception as e:
			print "%s[%s]"%(general.TAB, general.red('FAILED'))
		#print 'Starting httpd: ',
		self.startHTTPD()
		#print 'Starting xinetd: ',
		self.startTFTP()
		#print 'Starting dhcpd: ',
		self.startDHCPD()
		
		#print 'Press Ctrl+C to quit'
		#print 'waiting for new node...'
		self.show_ui()
		log = open('/var/log/messages', 'r')
		log.seek(0,2)
		httplog = open('/var/log/httpd/access_log','r')
		httplog.seek(0,2)
		while True:
			syslog = log.readline()
			self.check_new_node( syslog )
			
			access_log = httplog.readline()
			self.check_ks_request( access_log )
			self.check_install_request( access_log )

if __name__ == '__main__':
	app = insertNode()
	app.insert_procedure()
