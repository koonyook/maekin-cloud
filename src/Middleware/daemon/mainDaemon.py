#!/usr/bin/env python

import sys, os, time, atexit
from signal import SIGTERM 

#RED_COLOR='\033[91m'
#GREEN_COLOR='\033[92m'
#BLUE_COLOR='\033[94m'
#END_COLOR='\033[0m'

RED_COLOR = '\x1b[0;31m'
GREEN_COLOR = '\x1b[0;32m'
YELLOW_COLOR = '\x1b[0;33m'
BLUE_COLOR = '\x1b[1;34m'
PURPLE_COLOR = '\x1b[0;35m'
END_COLOR = '\x1b[0;0m'

TAB='\x1b[60G'

class Daemon:
	"""
	A generic daemon class.
	
	Usage: subclass the Daemon class and override the run() method
	"""
	def __init__(self, pidfile, servicename, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null', isDebugMode=False):
		self.stdin = stdin
		self.stdout = stdout
		self.stderr = stderr
		self.pidfile = pidfile
		self.servicename = servicename
		#Hacked by prayook(15/8/54)
		self.isDebugMode = isDebugMode
		#print "::"+self.pidfile

	def daemonize(self):
		"""
		do the UNIX double-fork magic, see Stevens' "Advanced 
		Programming in the UNIX Environment" for details (ISBN 0201563177)
		http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
		"""
		try: 
			pid = os.fork() 
			if pid > 0:
				# exit first parent
				sys.exit(0) 
		except OSError, e: 
			sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
			sys.exit(1)
	
		# decouple from parent environment
		os.chdir("/") 
		os.setsid() 
		os.umask(0) 
		#print "Before second fork"
		# do second fork
		try: 
			pid = os.fork() 
			if pid > 0:
				# exit from second parent
				sys.exit(0) 
		except OSError, e: 
			sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
			sys.exit(1) 
		
		print "Starting %s: %s[%s  OK  %s]"%(self.servicename, TAB, GREEN_COLOR, END_COLOR)
		
		# redirect standard file descriptors
		sys.stdout.flush()
		sys.stderr.flush()
		si = file(self.stdin, 'r')
		so = file(self.stdout, 'a+')
		se = file(self.stderr, 'a+', 0)
		
		if not self.isDebugMode:	#hacked by prayook(15/8/54)
			os.dup2(si.fileno(), sys.stdin.fileno())
			os.dup2(so.fileno(), sys.stdout.fileno())
			os.dup2(se.fileno(), sys.stderr.fileno())
		else:
			print "%sYou see this text because you are in debugging mode%s"%(BLUE_COLOR,END_COLOR)

		# write pidfile
		atexit.register(self.delpid)
		pid = str(os.getpid())
		file(self.pidfile,'w+').write("%s\n" % pid)
	
	def delpid(self):
		#print "%sI will delete pid file%s"%(RED_COLOR,END_COLOR)
		os.remove(self.pidfile)

	def start(self):
		"""
		Start the daemon
		"""
		# Check for a pidfile to see if the daemon already runs
		try:
			pf = file(self.pidfile,'r')
			pid = int(pf.read().strip())
			pf.close()
		except IOError:
			pid = None
	
		if pid:
			print "Starting %s: %s[%sFAILED%s]"%(self.servicename, TAB, RED_COLOR, END_COLOR)
			message = "pidfile %s already exist. Daemon already running?\n"
			sys.stderr.write(message % self.pidfile)
			sys.exit(1)
		
		# Start the daemon
		
		self.daemonize()
		
		self.run()

	def stop(self):
		"""
		Stop the daemon
		"""
		# Get the pid from the pidfile
		try:
			pf = file(self.pidfile,'r')
			pid = int(pf.read().strip())
			pf.close()
		except IOError:
			pid = None
	
		if not pid:
			print "Stopping %s: %s[%sFAILED%s]"%(self.servicename, TAB, RED_COLOR, END_COLOR)
			message = "pidfile %s does not exist. Daemon not running?\n"
			sys.stderr.write(message % self.pidfile)
			return # not an error in a restart

		# Try killing the daemon process	
		try:
			while 1:
				os.kill(pid, SIGTERM)
				time.sleep(0.1)
		except OSError, err:
			err = str(err)
			if err.find("No such process") > 0:
				if os.path.exists(self.pidfile):
					os.remove(self.pidfile)
				print "Stopping %s: %s[%s  OK  %s]"%(self.servicename, TAB, GREEN_COLOR,END_COLOR)
			else:
				print str(err)
				sys.exit(1)

	def restart(self):
		"""
		Restart the daemon
		"""
		self.stop()
		self.start()

	#koon add this method.
	def status(self):
		"""
		Print status of this service
		"""
		try:
			pf = file(self.pidfile, 'r')
			pid = int(pf.read().strip())
			pf.close()
		except IOError:
			pid=None

		if pid:
			print "service %s started at pid %d"%(self.servicename,pid)
		else:
			print "service %s stopped."%(self.servicename)

	def run(self):
		"""
		You should override this method when you subclass Daemon. It will be called after the process has been
		daemonized by start() or restart().
		"""
