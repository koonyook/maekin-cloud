#!/usr/bin/env python

import sys, os
import shlex, subprocess
import string

def	getInfo():
	cmd = 'df -P /maekin/var'
	args = shlex.split(cmd)
	p = subprocess.Popen(args, stdout=subprocess.PIPE)
	p.wait()
	#s = p.stdout.read().strip().split('\n')[1]
	s = p.communicate()[0].strip().split('\n')[1]
	info = {}
	info['capacity'] = s.strip().split()[1]
	info['free'] = s.strip().split()[3]

	cmd = 'du /maekin/var/storage'
	args = shlex.split(cmd)
	p = subprocess.Popen(args, stdout=subprocess.PIPE)
	p.wait()
	#s = p.stdout.read().strip()
	s = p.communicate()[0].strip()
	info['image_usage'] = s.strip().split()[0]

	cmd = 'du -c /maekin'
	args = shlex.split(cmd)
	p = subprocess.Popen(args, stdout=subprocess.PIPE)
	p.wait()
	#s = p.stdout.read().strip().split('\n')
	s = p.communicate()[0].strip().split('\n')
	#print s[len(s)-1]
	info['maekin_usage'] = s[len(s)-1].strip().split()[0]
	return info

if __name__ == '__main__':
	print getInfo()
