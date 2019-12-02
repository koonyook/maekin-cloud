#!/usr/bin/env python

import sys
sys.path.append('/maekin/lib/distro/')
import shlex, subprocess
import setting

# shell color code
COLOR_RED = '\x1b[0;31m'
COLOR_GREEN = '\x1b[0;32m'
COLOR_YELLOW = '\x1b[0;33m'
COLOR_BLUE = '\x1b[0;34m'
COLOR_PURPLE = '\x1b[0;35m'
TAB = '\x1b[60G'
COLOR_RESET = '\x1b[0;0m'

def	runsh(cmd):
	args = shlex.split(cmd)
	p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	p.wait()
	return p.communicate()

def colored(s, color):
	return color + s + COLOR_RESET
def red(s):
	return colored(s, COLOR_RED)
def blue(s):
	return colored(s, COLOR_RED)
def green(s):
	return colored(s, COLOR_GREEN)
def yellow(s):
	return colored(s, COLOR_YELLOW)
def purple(s):
	return colored(s, COLOR_PURPLE)

if __name__ == '__main__':
	print runsh('service hmm start')
