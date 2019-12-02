import setting

from util import network,cacheFile,ping,general
from util import connection
from util import debugger
from info import dbController
from storage import nfsController

import os
import time
import threading
import subprocess,shlex
import libvirt
import MySQLdb
import json
import shutil

###############################################
#################### PKI ######################
###############################################
def you_are_ca_server(argv):
	result = subprocess.Popen(shlex.split("mkdir -p %s"%(setting.CA_PATH)), stdout=subprocess.PIPE)
	result.wait()
	result = subprocess.Popen(shlex.split("certtool --generate-privkey --outfile %scakey.pem"%(setting.CA_PATH)), stdout=subprocess.PIPE)
	result.wait()
	
	infoFileName="ca.info"

	infoFile=open(setting.CA_PATH+infoFileName,'w')
	infoFile.write('''
cn = Maekin Main Certificate Authority
ca
cert_signing_key
''')
	infoFile.close()

	result = subprocess.Popen(shlex.split("certtool --generate-self-signed --load-privkey %(CA_PATH)scakey.pem --template %(CA_PATH)sca.info --outfile %(CA_PATH)scacert.pem"%{'CA_PATH':setting.CA_PATH}), stdout=subprocess.PIPE)
	result.wait()

	return 'OK'

def clone_ca(argv):
	'''
	only real ca can do this method
	(source of ca migration)
	'''
	targetHostIP=argv[0]
	mode=argv[1]

	cakeyString=open(setting.CA_PATH+'cakey.pem','r').read()
	cacertString=open(setting.CA_PATH+'cacert.pem','r').read()
	result=connection.socketCall(targetHostIP,setting.LOCAL_PORT,"you_are_next_ca",[cakeyString,cacertString,mode])
	
	if mode=='migrate':
		infoHost=cacheFile.getDatabaseIP()
		db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
		cursor = db.cursor()	
		cursor.execute("UPDATE `hosts` SET `isCA`=0 WHERE `IPAddress`='%s';"%(str(network.getMyIPAddr())))
		db.close()
	elif mode=='makeSlave':
		pass

	return result

def you_are_next_ca(argv):
	'''
	destination of ca migration
	'''
	cakeyString=argv[0]
	cacertString=argv[1]
	mode=argv[2]
	
	result = subprocess.Popen(shlex.split("mkdir -p %s"%(setting.CA_PATH)), stdout=subprocess.PIPE)
	result.wait()

	cakeyFile=open(setting.CA_PATH+'cakey.pem','w')
	cakeyFile.write(cakeyString)
	cakeyFile.close()

	cacertFile=open(setting.CA_PATH+'cacert.pem','w')
	cacertFile.write(cacertString)
	cacertFile.close()

	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	
	if mode=='migrate':
		cursor.execute("UPDATE `hosts` SET `isCA`=1 WHERE `IPAddress`='%s';"%(str(network.getMyIPAddr())))
	elif mode=='makeSlave':
		cursor.execute("UPDATE `hosts` SET `isCA`=2 WHERE `IPAddress`='%s';"%(str(network.getMyIPAddr())))
	db.close()

	return "OK"

def update_pki(argv):
	'''
	argv[0]=[conn,s,event]	#socket
	argv[1]=cerHostIP (optional)
	'''
	conn = argv[0][0]
	s = argv[0][1]
	
	#add later for testing
	#print "service libvirtd stop"
	#general.runDaemonCommand("service libvirtd stop",conn,s)

	#find cerHostIP
	if len(argv)==1:
		#find CA Server from database
		infoHost=cacheFile.getDatabaseIP()
		db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
		
		cursor = db.cursor()
		cursor.execute('''SELECT 
		`IPAddress`
		FROM `hosts`
		WHERE `isCA`=1;''')
		tmpData=cursor.fetchone()
		if tmpData==None:
			return 'CA Server not found.'
		cerHostIP=tmpData[0]
	else:
		cerHostIP=argv[1]
	
	#create directory
	result = subprocess.Popen(shlex.split("mkdir -p /etc/pki/libvirt/private/"), stdout=subprocess.PIPE)
	result.wait()

	#generate private key
	result = subprocess.Popen(shlex.split("certtool --generate-privkey --outfile /etc/pki/libvirt/private/serverkey.pem"), stdout=subprocess.PIPE)
	result.wait()
	
	#get cacert from CA to install at /etc/pki/CA/cacert.pema
	cacertString=connection.socketCall(cerHostIP, setting.LOCAL_PORT, 'request_cacert')
	cacertFile=open('/etc/pki/CA/cacert.pem','w')
	cacertFile.write(cacertString)
	cacertFile.close()

	''' not secure
	#send private key to sign at CA server
	cerString = connection.socketCall(cerHostIP, setting.LOCAL_PORT, 'request_sign_certificate',[str(network.getMyIPAddr()),open("/etc/pki/libvirt/private/serverkey.pem",'r').read()])
	'''

	#more secure (sending request)
	serverIP=str(network.getMyIPAddr())
	#create template file
	infoString='''
organization = Maekin
cn = "%s"
tls_www_server
tls_www_client
encryption_key
signing_key
	'''%(serverIP)
	infoFile=open('/etc/pki/libvirt/'+serverIP+'.info','w')
	infoFile.write(infoString)
	infoFile.close()
	#generate request from private key
	result = subprocess.Popen(shlex.split("certtool --generate-request --load-privkey /etc/pki/libvirt/private/serverkey.pem --template /etc/pki/libvirt/%s.info --outfile /etc/pki/libvirt/%s.req"%(serverIP,serverIP)), stdout=subprocess.PIPE)
	result.wait()

	requestString=open('/etc/pki/libvirt/'+serverIP+'.req','r').read()
	
	cerString = connection.socketCall(cerHostIP, setting.LOCAL_PORT, 'request_sign_certificate',[serverIP,infoString,requestString])

	#write to file
	cerFile=open('/etc/pki/libvirt/servercert.pem','w')
	cerFile.write(cerString)
	cerFile.close()
	
	#copy (already test : this command doesn't ask when must overwrite)
	shutil.copy2('/etc/pki/libvirt/private/serverkey.pem', '/etc/pki/libvirt/private/clientkey.pem')
	shutil.copy2('/etc/pki/libvirt/servercert.pem', '/etc/pki/libvirt/clientcert.pem')

	#delete temporary file
	os.remove('/etc/pki/libvirt/'+serverIP+'.info')
	os.remove('/etc/pki/libvirt/'+serverIP+'.req')

	#then restart libvirtd (very important)
	#*step should be like this
	#general.runDaemonCommand("service mklocm stop")	#do not stop because mklocm can resist error of libvirtd restart

	#debugger.countdown(10,"before restart libvirtd")
	print "service libvirtd restart"
	general.runDaemonCommand("service libvirtd stop",conn,s)
	general.runDaemonCommandUntilOK("service libvirtd start",conn,s)
	#time.sleep(2)
	#debugger.countdown(10,"after restart libvirtd")
	print "wait conn"
	vconn=libvirt.open(None)
	while vconn==None:
		time.sleep(1)
		vconn = libvirt.open(None)
	
	vconn.close()
	#debugger.countdown(10,"vconn.close()")
	#general.runDaemonCommand("service mklocm start",conn,s)	#do not stop because mklocm can resist error of libvirtd restart
	return 'OK'

def request_cacert(argv):
	return open(setting.CA_PATH+'cacert.pem','r').read()

def request_sign_certificate(argv):
	'''
	cannot be called if i am not CA
	'''
	serverIP=argv[0]
	infoString=argv[1]
	requestString=argv[2]

	serverInfoFile=open(setting.CA_PATH+serverIP+'.info','w')
	serverInfoFile.write(infoString)
	serverInfoFile.close()

	serverKeyFile=open(setting.CA_PATH+serverIP+'.req','w')
	serverKeyFile.write(requestString)
	serverKeyFile.close()

	#create certificate
	result = subprocess.Popen(shlex.split("certtool --generate-certificate --load-request %(request)s --load-ca-certificate %(cacert)s --load-ca-privkey %(cakey)s --template %(serverInfo)s --outfile %(output)s"%{
	'request':setting.CA_PATH+serverIP+'.req',
	'cacert':setting.CA_PATH+'cacert.pem',
	'cakey':setting.CA_PATH+'cakey.pem',
	'serverInfo':setting.CA_PATH+serverIP+'.info',
	'output':setting.CA_PATH+serverIP+'.out'
	}), stdout=subprocess.PIPE)
	result.wait()
	
	resultString=open(setting.CA_PATH+serverIP+'.out','r').read()
	
	#remove all junk file
	os.remove(setting.CA_PATH+serverIP+'.info')
	os.remove(setting.CA_PATH+serverIP+'.req')
	os.remove(setting.CA_PATH+serverIP+'.out')
	#print "reach"
	return resultString

