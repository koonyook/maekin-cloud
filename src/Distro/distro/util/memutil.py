#!/usr/bin/env python

import sys, os
import shlex, subprocess
import string

def	getInfo():
	cmd = 'cat /proc/meminfo'
	args = shlex.split(cmd)
	p = subprocess.Popen(args, stdout=subprocess.PIPE)
	p.wait()
	info = {}
	#s = p.stdout.read().strip().split('\n')
	s = p.communicate()[0].strip().split('\n')
	info[s[0].split()[0].strip(':')] = s[0].split()[1:]
	info[s[1].split()[0].strip(':')] = s[1].split()[1:]
	return info

if __name__ == '__main__':
	print getInfo()
