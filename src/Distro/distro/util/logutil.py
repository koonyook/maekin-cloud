#!/usr/bin/env python

import sys, time

sys.path.append('/maekin/lib/distro')
import setting

def log(modulename, errlv, description):
	f = open(setting.LOG_PATH + modulename, 'a+')
	f.write(time.strftime("%a, %d %b %Y %H:%M:%S : ", time.localtime()))
	f.write( errlv + ':' + description + '\n' )
	f.close()

if __name__ == '__main__':
	#print len(getInfo())
	log('test', 'ERROR', 'kak')
