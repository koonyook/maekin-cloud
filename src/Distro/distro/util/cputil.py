#!/usr/bin/env python

import sys, os, time
import shlex, subprocess
import string

def getLoad(core='all', detail=0):
	cmd = 'mpstat -P ALL 1 1'
	args = shlex.split(cmd)
	p = subprocess.Popen(args, stdout=subprocess.PIPE)
	p.wait()

	cpuinfo = []
	#print len(p.stdout.read())
	if detail == 0:
		#for s in p.stdout.read().strip().split('\n')[3:]:
		for s in p.communicate()[0].strip().split('\n')[3:]:
			if len(s) == 0:
				break
			info = s[11:].split()
			if info[0] == 'all':
				continue
			load = str(100-float(info[9]))
			cpuinfo.append(load)
	elif detail == 1:
		#for s in p.stdout.read().strip().split('\n')[3:]:
		for s in p.communicate()[0].strip().split('\n')[3:]:
			returndata = {}
			returndata['time'] = s[:11]
			info = s[11:].split()
			returndata['core'] = info[0]
			returndata['usr'] = info[1]
			returndata['nice'] = info[2]
			returndata['sys'] = info[3]
			returndata['iowait'] = info[4]
			returndata['irq'] = info[5]
			returndata['soft'] = info[6]
			returndata['steal'] = info[7]
			returndata['guest'] = info[8]
			returndata['idle'] = info[9]

			if core == 'all':
				cpuinfo.append(returndata)
			elif str(core) == info[0]:
				cpuinfo.append(returndata)
	return cpuinfo

def	getInfo(core='all'):
	cmd = 'cat /proc/cpuinfo'
	args = shlex.split(cmd)
	p = subprocess.Popen(args, stdout=subprocess.PIPE)
	p.wait()
	cpuinfo = []
	#for s in p.stdout.read().strip().split('\n\n'):
	for s in p.communicate()[0].strip().split('\n\n'):
		data = {}
		for s2 in s.split('\n'):
			f, r = s2.split(':')
			data[f.strip()] = r.strip()
		cpuinfo.append(data)
	return cpuinfo

def getLoadAvg():
	cmd = 'cat /proc/loadavg'
	args = shlex.split(cmd)
	p = subprocess.Popen(args, stdout=subprocess.PIPE)
	p.wait()
	#loadavg = p.stdout.read().strip().split(' ')
	loadavg = p.communicate()[0].strip().split(' ')
	return (loadavg[0],loadavg[1],loadavg[2])

if __name__ == '__main__':
	#print len(getInfo())
	print getInfo()
