#!/usr/bin/env python

import sys, os
sys.path.append('/maekin/lib/distro/')
import shlex, subprocess
import string, json
import setting
import re

def	getInfo( ifname='all'):
	if ifname == 'all':
		cmd = 'ifconfig'
	else:
		cmd = 'ifconfig ' + ifname

	args = shlex.split(cmd)
	p = subprocess.Popen(args, stdout=subprocess.PIPE)
	p.wait()
	#info = {}
	info = {}
	if ifname == 'all':
		#for s in p.stdout.read().strip().split('\n\n'):
		for s in p.communicate()[0].strip().split('\n\n'):
			print s + ';;;;;;;;;;;;;'
			rx, tx = gettxrx(s)
			info[s.split()[0]] = {'tx':tx,'rx':rx}
			#info.append({'rx':rx, 'tx':tx, 'interface':s.split()[0]})
	else:
		#s = p.stdout.read()
		s = p.communicate()[0]
		rx, tx = gettxrx(s)
		info[s.split()[0]] = {'tx':tx,'rx':rx}
		#info.append({'rx':rx, 'tx':tx, 'interface':s.split()[0]})
			
	return info

def gettxrx(s=''):
	if s == '':
		return (0,0)
	for line in s.split('\n'):
		if line.find('RX bytes:') >= 0 :
			line = line.replace(':', ' ').split()
			return [line[2], line[7]]
	return (0,0)
def gettxrxrate(s=''):
	if s == '':
		return None

	f = open(setting.MAEKIN_VAR_PATH+'iftmp', 'rw')
	if len(f.read()) == 0:
		print f
		f.write( json.dumps(gettxrx(s)) )
		f.close()
		return 
	else:
		last_rx, last_tx = json.loads( f.read() )
		rx, tx = gettxrx(s)
		diffrx = rx - last_rx
		difftx = tx - last_tx
		print diffrx, difftx
	
def getselfip(ifname):
	result = subprocess.Popen(shlex.split('ifconfig '+ifname), stdout=subprocess.PIPE)
	result.wait()
	output=result.communicate()[0]
	searchResult = re.search(r"inet addr\s*:\s*(?P<IP_ADDRESS>(\d+\.){3}\d+)",output)
	if searchResult==None:
		return None
	myIP=searchResult.groupdict()['IP_ADDRESS']
	if myIP==None:
		return None     #do not have ip now
	return myIP

def getMyMAC(ifname):
	result = subprocess.Popen(shlex.split('ifconfig '+ifname), stdout=subprocess.PIPE)
	result.wait()
	output=result.communicate()[0]
	myMAC = re.search(r"HWaddr\s+(?P<MAC_ADDRESS>([\dABCDEF]{2}:){5}[\dABCDEF]{2})",output).groupdict()['MAC_ADDRESS']
	return MACAddr(myMAC)

if __name__ == '__main__':
	print getselfip()
