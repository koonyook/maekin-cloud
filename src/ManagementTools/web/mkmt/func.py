################################################################
## Setting
################################################################
online = True
middlewareAPIport = ':8080'
################################################################
## for import user lib
################################################################
import os,sys,json
from xml.dom import minidom
from time import localtime,strftime
lib_folder = os.path.dirname(os.path.abspath('utils/network.py'))
if lib_folder not in sys.path:
	sys.path.insert(0, lib_folder)
sys.path.append('/maekin/lib/managementtool/web/utils/')
from itertools import chain
from network import *
from randompass import *
from MKS import rUrl,getXML,getXMLVal,traXML
from func import *
################################################################
## for import django lib
################################################################
from mkmt.models import *
from django.http import HttpResponse
from django.shortcuts import render_to_response,redirect,get_object_or_404
from django.core.urlresolvers import reverse
from django.views.generic import list_detail
from django.template import RequestContext
from django.core.files import File
from django import forms
from django.db.models import Q
from django.forms import ModelForm
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth.forms import PasswordChangeForm
def get_or_none(model, **kwargs):
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        return None
################################################################
## function for controller
#################################################################
def checkNetwork(inp):
	
	key = inp.keys()
	netid =  IPAddr(inp['id'])
	netmask = IPAddr(inp['mask'])
	ipUsed = [inp['id'],inp['route']]
	hostAtDefaultIP = 0
	MACUsed = []
	hostName = []
	if not netmask.isSubnetMask():
		return 'ERROR!! subnetmask'
	if not isMatch(netid ,netmask):
		return 'mismatch subnetmask'
	for x in key:
		if x.startswith('dnsIP_'):
			if not inp[x]in ipUsed:
				ipUsed.append(inp[x])
			else:
				return 'ERROR!! already have IP'+ str(tmp)
			#tmp = IPAddr(inp[x])
			#if tmp.isMulticast:
			#	return 'ERROR!! dnsIP' + tmp
		elif x.startswith('ip'):
			tmp = IPAddr(inp[x])
			if inp[x] not in ipUsed:
				ipUsed.append(inp[x])
			else:
				return 'ERROR!! already have IP' + str(tmp)
			if x.startswith('ip_start'):
				if IPAddr(inp['ip_stop_'+str(x.split('_')[2])]).getProduct() < tmp.getProduct():
					return 'ERROR!! VM ip must start with lower'
			if not tmp.isInNetwork(netid,netmask):
				return 'ERROR!! VM ip not in network id'
		elif x.startswith('host_MAC'):
			tmp2 = MACAddr(inp[x])
			if  inp[x] not in MACUsed:
				MACUsed.append(inp[x])
			else:
				return 'ERROR!! already have MAC' + str(tmp2) + str(ipUsed)
			if tmp2.isMulticast():
				return 'ERROR!! MAC host is multicast' + tmp2
		elif x.startswith('host_IP'):
			tmp = IPAddr(inp[x])
			if inp[x] not in ipUsed:
				ipUsed.append(inp[x])
			else:
				return 'ERROR!! already have IP' + str(tmp)
			if not tmp.isInNetwork(netid,netmask):
				return 'ERROR!! host ip not in network id'
		else:
			if inp[x] not in hostName and inp[x] != '':
				hostName.append(inp[x])
			else:
				return 'ERROR!! hostname already exist'
	return ''
	
def writeXML(input):
	fp = open('./mkmt/static/tmpXML','w')
	f = File(fp)
	buf = '''
<startup>
<UUID> {UUID[0]} </UUID>
<name> {name[0]} </name>
<network id="{id[0]}" mask="{mask[0]}" defaultRoute="{route[0]}"/>
'''
	k = input.keys()
	k.sort()
	#return str(x)
	dns = 0
	host = 0
	ip = 0
	for x in k:
		if x.startswith('dnsIP'):
			dns += 1
		if x.startswith('host_MAC'):
			host += 1
		if x.startswith('ip_start'):
			ip += 1
	buf += '<dns>\n'
	for i in range(dns):
		buf += '<dnsAddress IP="{dnsIP_'+str(i)+'[0]}" />\n'
	buf += '</dns>\n<IPaddressPool>\n<host>\n'
	for i in range(host):
		buf += '<Bind MAC="{host_MAC_'+str(i)+'[0]}" IP="{host_IP_'+str(i)+'[0]}" hostName="{host_Name_'+str(i)+'[0]}" />\n'
	buf += '</host>\n<guest>\n'
	for i in range(ip):
		buf += '<IP start="{ip_start_'+str(i)+'[0]}" stop="{ip_stop_'+str(i)+'[0]}" />\n'
	buf += '</guest>\n</IPaddressPool>\n</startup>'
	#return buf
	f.write(buf.format(**input))
	f.close()
	return buf.format(**input)
def updateCloudInfo():
	info = getCloudInfo(getCurrentCloud().middleIP)
	if info != None:
		oldIPPool = len(getCurrentCloud().GuestPool.all())
		storeCloudStartup(getCurrentCloud().middleIP,info,False)
		newIPPool = len(getCurrentCloud().GuestPool.all())
		gVI = getCurrentGlobalVI()
		gVI.quotaIP = gVI.quotaIP + (newIPPool - oldIPPool)
		gVI.save()
		return "clear"
	else:
		return "Cloud connection Probelm"
def getCloudInfo(midIP):
	text = rUrl(midIP+':8080'+'/cloud/getInfo')
	if text.count('403 Forbidden') != 0:
		return 'Host is forbidden'
	elif not text.startswith('error') and  text != '':
		cloud_info = {}
		c = getXML(text,'content')[0]
		cloud_info['UUID'] = str(getXMLVal(c,'UUID'))
		cloud_info['name'] = str(getXMLVal(c,'name'))
		net = getXML(c,'network')[0]
		cloud_info['networkID'] = str(net.attributes['id'].value)
		cloud_info['mask'] = str(net.attributes['mask'].value)
		cloud_info['defaultRoute'] = str(net.attributes['defaultRoute'].value)
		if(str(getXMLVal(c,'dns')) != ''):
			cloud_info['dnsPool'] = str(getXMLVal(c,'dns')).split(',')
		else:
			cloud_info['dnsPool'] = []
		if(str(getXMLVal(c,'guest')) != ''):
			cloud_info['guestPool'] = str(getXMLVal(c,'guest')).split(',')
		else:
			cloud_info['guestPool'] = []
		cloud_info['automode'] = str(getXMLVal(c,'autoMode'))
		return cloud_info
	else:
		return 'Not found Cloud API'
def storeCloudStartup(midIP,info,isnew):
	if not isnew:
		#Cloud.objects.get(middleIP=input['MiddlewareIP']).delete()
		oldcloud = Cloud.objects.get(middleIP=midIP)
		oldcloud.middleIP=midIP
		oldcloud.name = info['name']
		oldcloud.default = info['defaultRoute']
		oldcloud.network = info['networkID']
		oldcloud.subnet = info['mask']
		oldcloud.mode = info['automode']
		oldcloud.DNSPool.clear()
		oldcloud.GuestPool.clear()
		for dnsIP in info['dnsPool']:
			dnsip = get_or_none(DnsIP,dnsAddressIP = dnsIP) 
			if dnsip == None:
				dnsip = DnsIP.objects.create(dnsAddressIP = dnsIP)
			oldcloud.DNSPool.add(dnsip)
		for guestIP in info['guestPool']:
			gIP = get_or_none(GuestIP,IP = guestIP) 
			if gIP == None:
				gIP = GuestIP.objects.create(IP = guestIP)
			oldcloud.GuestPool.add(gIP)
		oldcloud.save()
		return oldcloud
	if isnew:
		scloud = Cloud.objects.create(UUID=info['UUID'],name=info['name'],default=info['defaultRoute'],middleIP=midIP,network=info['networkID'],subnet=info['mask'],mode=info['automode'])
		for dnsIP in info['dnsPool']:
			dIP = DnsIP.objects.create(dnsAddressIP = dnsIP)
			scloud.DNSPool.add(dIP)
		for guestIP in info['guestPool']:
			gIP = GuestIP.objects.create(IP = guestIP)
			scloud.GuestPool.add(gIP)
		return scloud
def getCurrentGlobalVI():
	return VI.objects.get(id=0)
def getCurrentCloud():
	return currentCloud.objects.get(id=1).cloud
def getMiddlewareIP():
	return currentCloud.objects.get(id=1).cloud.middleIP
def getCurrentGuestPoolNetworkGroup():
	curcloud = getCurrentCloud() 
	pool = curcloud.GuestPool.all()
	tmp = []
	for ip in pool:	
		tmp.append(ip.IP)
	return getIPPoolStringList(tmp)
def cloud_rURL(url):
	if online:
		cloudURL = getMiddlewareIP()
		#cloudURL = Cloud.objects.get(id=1).middleIP
		data = rUrl(cloudURL+middlewareAPIport+url)
		if not data.startswith('error'):
			return data
	return ''
def storeAdminCloudTmp(input):
	#if User.objects.filter(username='CloudAdmin').count() == 0:
	#	tmpadminpass = GenPasswd2()
	#	User.objects.create_user('CloudAdmin','admin@'+cloudname+'_mkmt.com',tmpadminpass)
	#	Admin_mkmt.objects.create(userid = User.objects.get(username='CloudAdmin'))
	#else: tmpadminpass = User.objects.get(username='CloudAdmin').password
	#if User.objects.filter(username=input['AdminName']).count() == 0:
	if initCloud():
		User.objects.create_user(input['AdminName'],input['AdminEmail'],input['AdminPass'])
		Admin_mkmt.objects.create(user = User.objects.get(username=input['AdminName']))
	#return tmpadminpass
def initCloud():
	if Admin_mkmt.objects.all().count() == 0:
		return True
	else:
		return False
def createUser(username,email,password):
	newUser = User.objects.create_user(username, email, password)
	defaultRole =  Role.objects.filter(ownerVI=VI.objects.get(id=0),roleEdit=False)[0]
	defaultRole.user.add(newUser)
def getErrorDict(*inp):
	return {'text':inp[0],'backlink':inp[1],'backto':inp[2]}
def extractVMInfo(a):
	imageID = int(a.attributes['guestID'].value)
	name 	= str(a.attributes['guestName'].value)
	hostid 	= str(getXMLVal(a,'lastHostID'))
	uuid 	= str(getXMLVal(a,'lastUUID'))
	MAC 	= str(getXMLVal(a,'MAC'))
	IP 		= str(getXMLVal(a,'IP'))
	template = str(getXMLVal(a,'templateID'))
	memory 	= str(int(getXMLVal(a,'memory'))/1024/1024)
	vCPU 	= str(getXMLVal(a,'vCPU'))
	inbound = str(getXMLVal(a,'inbound'))
	outbound = str(getXMLVal(a,'outbound'))
	vm 		= {'imageID':imageID,'name':name,'hostid':hostid,'uuid':uuid,'MAC':MAC,'IP':IP,'template':template,'vCPU':vCPU,'memory':memory,'inbound':inbound,'outbound':outbound}
	text2 = cloud_rURL('/guest/getState?guestID='+str(imageID))
	guestRaw = getXML(text2,'guest')
	if len(guestRaw) > 0:
		b = guestRaw[0]
		vm['status'] = ['shutoff','on','saved'][int(getXMLVal(b,'status'))]
		vm['activity'] = ['none','cloning','booting','saveing','restoring'][int(getXMLVal(b,'activity'))]
		vm['runningState'] = ['none','running','out of memory','paused','shutting down','shutoff','crashed'][int(getXMLVal(b,'runningState'))]
		vmobj = get_or_none(VM,imageID=imageID)
		if not vmobj == None:
			vm['ownerVI'] = VM.objects.get(imageID=imageID).ownerVI.id
		else:
			vm['ownerVI'] = 0
		return vm
	else:
		return None
def getVMinfo(vmid=None):
	vm_info_list = []
	if vmid == None:
		text = cloud_rURL('/guest/getInfo')
		if text.startswith('error') or text == '':
			return ''
		for a in getXML(text,'guest'):
			vm_info = extractVMInfo(a)
			if vm_info != None:
				vm_info_list.append(vm_info)
		return vm_info_list
	else:
		text = cloud_rURL('/guest/getInfo?guestID='+str(vmid))
		if text != '' :
			if len(getXML(text,'guest')) > 0:	
				return extractVMInfo(getXML(text,'guest')[0])
		return []
def getVMStat(vmlist,getCPU,getMEM,getNET,getIO):
	vmListStat = []
	alldata = cloud_rURL('/guest/getCustomizedInfo?cpu='+getCPU+'&memory='+getMEM+'&network='+getNET+'&io='+getIO+'&guestIDs='+vmlist)
	for data in getXML(alldata,'guest'):
		vmID = int(data.attributes['guestID'].value)
		if  str(data.attributes['polling'].value) == 'success':
			vmStat = {}
			vmStat['vmID'] = vmID
			if getCPU == '1':
				vmStat['cpuAverage'] 	= str(getXMLVal(getXML(data,'cpuInfo')[0],'average'))
				vmStat['cpuCpuTime'] 	= str(getXMLVal(getXML(data,'cpuInfo')[0],'cpuTime'))
			if getMEM == '1':
				vmStat['memTotal'] 	= str(getXMLVal(getXML(data,'memoryInfo')[0],'memTotal'))
				vmStat['memUse'] 	= str(getXMLVal(getXML(data,'memoryInfo')[0],'memUse'))
			if getNET == '1':
				vmStat['netRX'] 	= str(getXMLVal(getXML(data,'networkInfo')[0],'rx'))
				vmStat['netTX'] 	= str(getXMLVal(getXML(data,'networkInfo')[0],'tx'))
				vmStat['netSumRx'] 	= str(getXMLVal(getXML(data,'networkInfo')[0],'sumRx'))
				vmStat['netSumTx'] 	= str(getXMLVal(getXML(data,'networkInfo')[0],'sumTx'))
			if getIO == '1':
				vmStat['ioRX'] 	= str(getXMLVal(getXML(data,'ioInfo')[0],'rx'))
				vmStat['ioTX'] 	= str(getXMLVal(getXML(data,'ioInfo')[0],'wx'))
				vmStat['ioSumRx'] 	= str(getXMLVal(getXML(data,'ioInfo')[0],'sumRx'))
				vmStat['ioSumTx'] 	= str(getXMLVal(getXML(data,'ioInfo')[0],'sumWx'))
			vmListStat.append(vmStat)
	return vmListStat
def getHostStat(targetHostID=''):
	hostListStat = []
	if targetHostID == '':
		alldata = cloud_rURL('/host/getAllCurrentInfo')
	else:
		alldata = cloud_rURL('/host/getAllCurrentInfo?hostID='+targetHostID)
	for data in getXML(alldata,'host'):
		hostID = str(data.attributes['hostID'].value)
		if  str(data.attributes['polling'].value) == 'success':
			hostStat= {}
			hostStat['hostID'] = hostID
			hostStat['cpuAverage'] 	= str(getXMLVal(getXML(data,'cpuInfo')[0],'average'))
			hostStat['memTotal'] 	= str(getXMLVal(getXML(data,'memoryInfo')[0],'memTotal'))
			hostStat['memFree'] 	= str(getXMLVal(getXML(data,'memoryInfo')[0],'memFree'))
			hostStat['netRX'] 	= str(getXMLVal(getXML(data,'networkInfo')[0],'rx'))
			hostStat['netTX'] 	= str(getXMLVal(getXML(data,'networkInfo')[0],'tx'))
			hostStat['storageCap'] 	= str(getXMLVal(getXML(data,'storageInfo')[0],'capacity'))
			hostStat['storageFree'] 	= str(getXMLVal(getXML(data,'storageInfo')[0],'free'))
			hostStat['storageMaekinUsage'] 	= str(getXMLVal(getXML(data,'storageInfo')[0],'maekinUsage'))
			hostStat['storageImageUsage'] 	= str(getXMLVal(getXML(data,'storageInfo')[0],'imageUsage'))
			hostListStat.append(hostStat)
	return hostListStat
def removeAllocateResouce(vm):
	vi = vm.ownerVI
	vi.usedIP = vi.usedIP-1
	vi.usedVCPU = vi.usedVCPU - vm.vCPU
	vi.usedRAM = vi.usedRAM - vm.memory/256
	vi.save()
def recordNewVMtoDB(vmdata,viid=0):
	templateVM=Template.objects.get(templateID=vmdata['template'])
	if templateVM.OS == 'windows':
		canRemote = True
		canSsh = False
	else:
		canRemote = False
		canSsh = True
	VM.objects.create(imageID=int(vmdata['imageID']),
	name=vmdata['name'],
	IP=vmdata['IP'],
	template=templateVM,
	ssh=canSsh,
	remote=canRemote,
	vCPU=vmdata['vCPU'],
	memory=vmdata['memory'],
	ownerVI=VI.objects.get(id=viid))
	vi = VI.objects.get(id=viid)
	vi.usedIP = vi.usedIP+1
	vi.usedVCPU = vi.usedVCPU + int(vmdata['vCPU'])
	vi.usedRAM = vi.usedRAM + int(vmdata['memory'])/256
	vi.template.add(Template.objects.get(templateID=vmdata['template']))
	vi.save()
def checkUserPermission(user,vi,action_set):
	role = get_or_none(Role,user=user,ownerVI=vi)
	if role ==  None:
		return False
	for action in action_set:
		b = getattr(role,action)
		if getattr(role,action) == False:
			return False
	#a = 1/0
	return True
def permissionFail(vi,action):
	return "Don't have permission to "+action+" VM in "+vi.name
def getTemplate(temID=''):
	if temID == '':
		text = cloud_rURL("/template/getInfo")
		template_list = []
		if text.startswith('error') or text == '':
			return ''
		for a in getXML(text,'template'):
			template = {}
			template['id'] = str(a.attributes['templateID'].value)
			template['OS'] = str(getXMLVal(a,'OS'))
			if 'windows' in str.lower(template['OS']):
				template['ostype'] = 'windows'
			elif 'centos' in str.lower(template['OS']):
				template['ostype'] = 'centos'
			elif 'ubuntu' in str.lower(template['OS']):
				template['ostype'] = 'ubuntu'
			elif 'linux' in str.lower(template['OS']):
				template['ostype'] = 'linux'
			else:
				template['ostype'] = 'OS'
			template['description'] = str(getXMLVal(a,'description'))
			template['minimumMemory'] = str(getXMLVal(a,'minimumMemory'))
			template['maximumMemory'] = str(getXMLVal(a,'maximumMemory'))
			template_list.append(template)
			if len(Template.objects.filter(templateID=template['id']))==0:
				newTem = Template.objects.create(OS=template['OS'],templateID=template['id'],description=template['description'],minMem =template['minimumMemory'],maxMem=template['maximumMemory'],ostype=template['ostype'])
				VI.objects.get(id=0).template.add(newTem)
		return template_list
	else:
		text = cloud_rURL("/template/getInfo?templateID="+temID)
		a = getXML(text,'template')[0]
		template = {}
		template['id'] = str(a.attributes['templateID'].value)
		template['OS'] = str(getXMLVal(a,'OS'))
		if 'windows' in str.lower(template['OS']):
			template['ostype'] = 'windows'
		elif 'centos' in str.lower(template['OS']):
			template['ostype'] = 'centos'
		elif 'ubuntu' in str.lower(template['OS']):
			template['ostype'] = 'ubuntu'
		elif 'linux' in str.lower(template['OS']):
			template['ostype'] = 'linux'
		else:
			template['ostype'] = 'OS'
		template['description'] = str(getXMLVal(a,'description'))
		template['minimumMemory'] = str(getXMLVal(a,'minimumMemory'))
		template['maximumMemory'] = str(getXMLVal(a,'maximumMemory'))
		return template
def extractHostInfo(a):
	hostinfo = {}
	hostinfo['id'] = str(a.attributes['hostID'].value)
	hostinfo['hostName'] = str(a.attributes['hostName'].value)
	hostinfo['status'] = ['shutoff','running','suspended'][int(getXMLVal(a,'status'))]
	hostinfo['activity'] = ['None','preparing to shutdown','booting','preparing to suspend','waking up'][int(getXMLVal(a,'activity'))]
	hostinfo['MAC'] = str(getXMLVal(a,'MAC'))
	hostinfo['IP'] = str(getXMLVal(a,'IP'))
	hostinfo['isHost'] = ['no','yes'][int(getXMLVal(a,'isHost'))]
	hostinfo['isGlobalController'] = ['no','master','slave'][int(getXMLVal(a,'isGlobalController'))]
	hostinfo['isInformationServer'] = ['no','master','slave'][int(getXMLVal(a,'isInformationServer'))]
	hostinfo['isNFSServer'] =['no','master','slave'][int(getXMLVal(a,'isNFSServer'))]
	hostinfo['isCA'] = str(getXMLVal(a,'isCA'))
	hostinfo['mem_size'] = str(getXMLVal(a,'size'))
	hostinfo['mem_type'] = str(getXMLVal(a,'type'))
	hostinfo['mem_speed'] = str(getXMLVal(a,'speed'))
	hostinfo['cpu_model'] = str(getXMLVal(a,'model'))
	hostinfo['cpu_number'] = str(getXMLVal(a,'number'))
	hostinfo['cpu_freq'] = str(getXMLVal(a,'frequency'))
	hostinfo['cpu_cache'] = str(getXMLVal(a,'cache'))
	return hostinfo
def getHostInfo(hostID=""):
	hostInfoList = []
	if hostID == "":
		text = cloud_rURL("/host/getInfo")
		if text.startswith('error') or text == '' :
			return hostInfoList
		for a in getXML(text,'host'):
			hostInfo = extractHostInfo(a)
			hostInfoList.append(hostInfo)
	else:
		text = cloud_rURL("/host/getInfo?hostID="+hostID)
		if text.startswith('error') or text == '' :
			return hostInfoList
		hostInfoList.append(extractHostInfo(getXML(text,'host')[0]))
	return hostInfoList
def isHostTask(data):
	xml = getXML(data,'task')[0]
	opcode = xml.attributes['taskID'].value
	if int(opcode) >= 16:
		return True
	else:
		return False
def createVMLog(vmImageID,name,user,command,xml,viid=None):
	if vmImageID == None:	#for createVM
		log = VMLog.objects.create(vmImageID=None,vmName=name,username=user.username,action=command,viID=viid,taskID=int(getXML(xml,'task')[0].attributes['taskID'].value))
	else:
		log = VMLog.objects.create(vmImageID=int(vmImageID),vmName=name,username=user.username,action=command,viID=viid,taskID=int(getXML(xml,'task')[0].attributes['taskID'].value))
def createHostLog(hostID,user,command,xml):
	if hostID == None:
		log = HostLog.objects.create(hostID=None,username=user.username,action=command,taskID=int(getXML(xml,'task')[0].attributes['taskID'].value))
	else:
		log = HostLog.objects.create(hostID=int(hostID),username=user.username,action=command,taskID=int(getXML(xml,'task')[0].attributes['taskID'].value))
def setHostLogDetail(data):
	xml = getXML(data,'task')[0]
	taskID = int(xml.attributes['taskID'].value)
	log = HostLog.objects.get(taskID=taskID)
	x = int(getXMLVal(xml,'status'))
	log.status = ['queued','working','finish'][x]
	currentfinishStatus = ['None','success','error'][int(getXMLVal(xml,'finishStatus'))]
	if log.action == 'host_add':
		if log.status == 'finish' and currentfinishStatus == 'success':
			log.hostID = int(getXML(data,'host')[0].attributes['hostID'].value)
	log.startTime = str(getXMLVal(xml,'createTimestamp'))
	log.finishTime = str(getXMLVal(xml,'finishTimestamp'))
	log.finishMessage = str(getXMLVal(xml,'finishMessage'))
	if currentfinishStatus == 'error':
		log.error = True
	elif currentfinishStatus == 'success':
		log.error = False
	log.save()
	return log
def setVMLogDetail(data):
	xml = getXML(data,'task')[0]
	taskID = int(xml.attributes['taskID'].value)
	log = VMLog.objects.get(taskID=taskID)
	x = int(getXMLVal(xml,'status'))
	log.status = ['queued','working','finish'][x]
	currentfinishStatus = ['None','success','error'][int(getXMLVal(xml,'finishStatus'))]
	if log.action == 'create':
		if log.status == 'finish' and currentfinishStatus == 'success':
			log.vmImageID = int(getXML(data,'guest')[0].attributes['guestID'].value)
			if get_or_none(VM,imageID=int(getXML(data,'guest')[0].attributes['guestID'].value)) == None:
				recordNewVMtoDB(getVMinfo(log.vmImageID),log.viID)
	log.startTime = str(getXMLVal(xml,'createTimestamp'))
	log.finishTime = str(getXMLVal(xml,'finishTimestamp'))
	log.finishMessage = str(getXMLVal(xml,'finishMessage'))
	if currentfinishStatus == 'error':
		log.error = True
	elif currentfinishStatus == 'success':
		log.error = False
	log.save()
	return log
def lostVM(vmID):
	vm = VM.objects.get(imageID=vmID)
	removeAllocateResouce(vm)
	log = VMLog.objects.create(vmImageID=vm.imageID,vmName=vm.name,user=Admin_mkmt.objects.get(id=1).user,action="Lost",viID=vm.ownerVI.id)
	vm.delete()
def checkQuotaVI(vi,cpu,ram):
	if vi.quotaIP - vi.usedIP > 0:
		if vi == getCurrentGlobalVI():
			return True
		else:
			if vi.quotaVCPU - vi.usedVCPU >=  cpu:
				if vi.quotaRAM - vi.usedRAM >= ram:
					return True
	return False
def logVI(name,ownerUser,adminList,templateList,quotaIP,quotaCPU,quotaRam):
	if get_or_none(VIrequest,name=name) == None:
		req = VIrequest.objects.create(ownerCloud=getCurrentCloud(),name=name,owner=ownerUser,quotaIP=quotaIP,quotaVCPU=quotaCPU,quotaRAM=quotaRam)
		for template in templateList:	
			req.template.add(template)
		for user in adminList:
			req.adminGroup.add(user)
		req.save()
		return "clear"
	else:
		return "Error! : VI request name already found"
def createVI(name,ownerUser,adminList,templateList,quotaIP,quotaCPU=None,quotaRam=None,id=None):
	currentUser = User.objects.filter(is_superuser=False)
	if id != 0:
		globalVI = getCurrentGlobalVI()
		globalVI.quotaIP = globalVI.quotaIP - quotaIP
		globalVI.save()
	newVI = VI.objects.create(id=id,owner=ownerUser,name=name,quotaIP=quotaIP,quotaVCPU=quotaCPU,quotaRAM=quotaRam,ownerCloud=getCurrentCloud())
	newAdminRole = createNewRole(newVI.name+'_Admin',newVI,'11111111')
	#newAdminRole = Role.objects.create(ownerVI=newVI,name=newVI.name+'_Admin')
	#configRole(newAdminRole,'11111111')
	for addAdmin in adminList:
		newAdminRole.user.add(User.objects.get(id=addAdmin))
	if id == 0:
		createNewRole(newVI.name+'_User',newVI,'00010000')
	for addTem in templateList:
		newVI.template.add(Template.objects.get(templateID=addTem))
	##########
	##DEBUG
	#########
	newAdminRole.user.add(User.objects.filter(is_superuser=True)[0])
	return newVI
def createNewRole(name,vi,permission,flag='1'):
	newRole = Role.objects.create(ownerVI=vi,name=name)
	configRole(newRole,permission,flag)
	return newRole
def configRole(role,permission,flag):
	role.roleEdit = permission[0] == flag
	role.userAdd = permission[1]== flag
	role.userRemove = permission[2]== flag
	role.vmControl = permission[3]== flag
	role.vmCreate = permission[4]== flag
	role.vmDelete = permission[5]== flag
	role.templateAdd = permission[6]== flag
	role.templateRemove = permission[7]== flag
	role.save()
def roleGreaterAndEqualDegree(a,b):
	return greaterAndEqualPermission(a,b,'roleEdit')and greaterAndEqualPermission(a,b,'userAdd')and greaterAndEqualPermission(a,b,'userRemove')and greaterAndEqualPermission(a,b,'vmControl')and greaterAndEqualPermission(a,b,'vmCreate')and greaterAndEqualPermission(a,b,'vmDelete')and greaterAndEqualPermission(a,b,'templateAdd')and greaterAndEqualPermission(a,b,'templateRemove')
def roleEqualDegree(a,b):
	return a.roleEdit == b.roleEdit and a.userAdd == b.userAdd and a.userRemove == b.userRemove and a.vmControl == b.vmControl and a.vmCreate == b.vmCreate and a.vmDelete == b.vmDelete and a.templateAdd == b.templateAdd and a.templateRemove == b.templateRemove
def roleGreaterDegree(a,b):
	return roleGreaterAndEqualDegree(a,b) and not roleEqualDegree(a,b)
def greaterAndEqualPermission(a,b,attr):
	return getattr(a,attr) or not (getattr(a,attr) or getattr(b,attr))
def getCloudAdminGroup():
	adminlist = Admin_mkmt.objects.all()
	res = []
	for admin in adminlist:
		res.append(admin.user)
	return res
def isCloudAdmin(user):
	if user.is_superuser:
		return True
	if len(Admin_mkmt.objects.filter(user=user)) > 0:
		return True
	else:
		return False