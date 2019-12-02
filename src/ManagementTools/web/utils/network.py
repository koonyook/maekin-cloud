import subprocess, shlex
import re
import random
import string
import time



def kill_dhclient():
	'''
	check dhclient and kill it
	running of dhclient means old ifup is not finish yet
	'''
	result = subprocess.Popen(shlex.split('''ps -o pid -C dhclient'''), stdout=subprocess.PIPE)
	result.wait()
	lines=result.communicate()[0].split('\n')
	processID=None
	for line in lines:
		if 'PID' in line:
			continue
		try:
			processID=int(line)
			break
		except:
			continue
	
	if processID!=None:
		result = subprocess.Popen(shlex.split('''kill -9 %d'''%(processID)), stdout=subprocess.PIPE)
		result.wait()





	
def randomMAC():
	mac = [ 0x00, 0x16, 0x3e,
			random.randint(0x00, 0x7f),
			random.randint(0x00, 0xff),
			random.randint(0x00, 0xff) ]
	lowerString = ':'.join(map(lambda x: "%02x" % x, mac))
	return string.upper(lowerString)

def getMyGateway():
	'''
	get gateway from "ip route"
	'''
	result = subprocess.Popen(shlex.split('''ip route'''), stdout=subprocess.PIPE)
	result.wait()
	output=result.communicate()[0]
	#print output
	searchResult = re.search(r"default\s*via\s*(?P<GATEWAY>(\d+\.){3}\d+)\s*dev\s*br0",output)

	if searchResult==None:
		print "Do not have gateway now"
		print "Output is:",output
		return None
	
	myGateway=searchResult.groupdict()['GATEWAY']
	if myGateway==None:
		return None
	
	try:
		tmp=IPAddr(myGateway)
		return tmp
	except:
		print "getMyGateway() error"
		return None
	
def getMyDNS(forceGet=False):
	'''
	get dns from /etc/resolv.conf
	'''
	while True:
		try:
			f=open('/etc/resolv.conf','r')
			break
		except:
			if forceGet:
				time.sleep(1)
			else:
				return None

	dnsList=[]
	while True:
		output=f.readline()
		if output=='':
			break
		searchResult = re.search(r"nameserver\s*(?P<DNS>(\d+\.){3}\d+)",output)
		if searchResult!=None and searchResult.groupdict()['DNS']!=None:
			dnsList.append(IPAddr(searchResult.groupdict()['DNS']))
	
	if len(dnsList)==0:
		return None
	else:
		return dnsList[-1]

def getMyMACAddr():
	'''
	return MACAddr of eth0 interface of the host that call this function
	'''
	result = subprocess.Popen(shlex.split('''ifconfig eth0'''), stdout=subprocess.PIPE)
	result.wait()
	output=result.communicate()[0]
	#print output
	myMAC = re.search(r"HWaddr\s+(?P<MAC_ADDRESS>([\dABCDEF]{2}:){5}[\dABCDEF]{2})",output).groupdict()['MAC_ADDRESS']
	return MACAddr(myMAC)

def getMyNetMask():
	'''
	return Mask of br0 interface of the host that call this function
	'''
	result = subprocess.Popen(shlex.split('''ifconfig br0'''), stdout=subprocess.PIPE)
	result.wait()
	output=result.communicate()[0]
	#print output
	searchResult = re.search(r"Mask\s*:\s*(?P<MASK>(\d+\.){3}\d+)",output)

	if searchResult==None:
		print "Do not have IP now"
		return None
	
	myMask=searchResult.groupdict()['MASK']
	if myMask==None:
		return None	#do not have ip now
	
	try:
		tmp=IPAddr(myMask)
		return tmp
	except:
		print "getMyNetMask() error"
		return None

def getMyIPAddr():
	'''
	return IPAddr of br0 interface of the host that call this function
	'''
	result = subprocess.Popen(shlex.split('''ifconfig br0'''), stdout=subprocess.PIPE)
	result.wait()
	output=result.communicate()[0]
	#print output
	searchResult = re.search(r"inet addr\s*:\s*(?P<IP_ADDRESS>(\d+\.){3}\d+)",output)

	if searchResult==None:
		print "Do not have IP now"
		print "Output is:",output
		return None
	
	myIP=searchResult.groupdict()['IP_ADDRESS']
	if myIP==None:
		return None	#do not have ip now
	
	try:
		tmp=IPAddr(myIP)
		return tmp
	except:
		print "getMyIPAddr() error"
		return None

class IPAddr:
	'''	
	IP address
		- sequence
	'''

	def __init__(self,ip):
		# ip can be either an integer or a string

		if isinstance(ip, (int, long)):
			self.sequence=[0]*4

			self.sequence[3]=ip%(256**1)
			ip-=self.sequence[3]
			self.sequence[2]=ip%(256**2)
			ip-=self.sequence[2]
			self.sequence[1]=ip%(256**3)
			ip-=self.sequence[1]
			self.sequence[0]=ip%(256**4)
			ip-=self.sequence[0]
			
			if ip!=0:
				raise NameError('InvalidIP')
			else:
				self.sequence[3]/=(256**0)
				self.sequence[2]/=(256**1)
				self.sequence[1]/=(256**2)
				self.sequence[0]/=(256**3)

		else:
			ipString=str(ip)
			self.sequence=ipString.split('.')
			if len(self.sequence) != 4:
				raise NameError('InvalidIP')
			try:
				for i in range(len(self.sequence)):
					self.sequence[i]=int(self.sequence[i])
					if not (self.sequence[i] in range(256)):
						raise NameError('InvalidIP') 

			except ValueError:
				raise NameError('InvalidIP')
			except NameError:
				raise
			except:
				print "Unexpected error:", sys.exc_info()[0]
				raise 
	
	def getProduct(self):
		product=0;
		for num in self.sequence:
			product = product*256 + num
		return product

	def isSubnetMask(self):
		'''	
		return int of slash notation
		return False of false subnetmask 
		'''
		product=self.getProduct()
		divider=2**31;
		count=0;
		while product/divider==1:
			product=product%divider
			divider/=2
			count+=1
		
		if product==0:
			return count
		else:
			return False

	def isInNetwork(self,networkID,subnetMask):
		if self==networkID:
			return False
		
		networkProduct=networkID.getProduct()
		subnetProduct=subnetMask.getProduct()
		myProduct=self.getProduct()
		
		if (myProduct&subnetProduct) == networkProduct:
			return True
		else:
			return False

	def __eq__(self,other):
		return (str(self)==str(other))

	def __repr__(self):
		res=[]
		for num in self.sequence:
			res.append(str(num))
		return '.'.join(res)

class MACAddr:
	'''
	MAC Address
		-sequence
	'''

	def __init__(self,ipString):
		self.sequence=ipString.split(':')
		if len(self.sequence) != 6:
			raise NameError('InvalidIP')
		try:
			for i in range(len(self.sequence)):
				self.sequence[i]=int(self.sequence[i],16)
				if not (self.sequence[i] in range(256)):
					raise NameError('InvalidIP') 

		except ValueError:
			raise NameError('InvalidIP')
		except NameError:
			raise
		except:
			print "Unexpected error:", sys.exc_info()[0]
			raise 

	def isMulticast(self):
		#check if 8th bit is 1
		if self.sequence[0]%2==1:
			return True
		else:
			return False
	
	def __eq__(self,other):
		return (str(self)==str(other))

	def __repr__(self):
		res=[]
		for num in self.sequence:
			res.append("%02X"%num)
		return ':'.join(res)

def isMatch(networkID, subnetMask):
	'''
	NetworkID=IPAddr
	SubnetMask=IPAddr
	'''
	cidr = subnetMask.isSubnetMask()
	if not cidr:
		return False
	else:
		product=networkID.getProduct()
		
		moder = (2**32) - subnetMask.getProduct()
		if product%moder==0:
			return True
		else:
			return False
		
def getIPPoolStringList(ipList):
	'''
	ipList=list of string of ip
	return list of string
	'''
	if len(ipList)<=1:
		return ipList
	
	result=[]

	productList=[]
	for element in ipList:
		productList.append(IPAddr(element).getProduct())
	
	productList.sort()
	startIP=productList[0]
	stopIP=productList[0]
	for i in range(1,len(productList)):
		if productList[i]==productList[i-1]+1:
			stopIP=productList[i]
		else:
			if startIP!=stopIP:
				result.append(str(IPAddr(startIP))+'-'+str(IPAddr(stopIP)))
			else:
				result.append(str(IPAddr(startIP)))
			startIP=productList[i]
			stopIP=productList[i]
	
	if startIP!=stopIP:
		result.append(str(IPAddr(startIP))+'-'+str(IPAddr(stopIP)))
	else:
		result.append(str(IPAddr(startIP)))
	
	return result


