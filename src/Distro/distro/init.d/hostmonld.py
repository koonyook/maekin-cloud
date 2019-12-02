#!/usr/bin/env python

import sys

sys.path.append("/maekin/lib/distro")
import setting

sys.path.append(setting.MONITOR_MODULE_PATH)
from locald.mond import hostmonld

if __name__ == "__main__":
	daemon = hostmonld('/var/run/hostmonld.pid')
	if len(sys.argv) == 2:
		if 'start' == sys.argv[1]:
			daemon.start()
		elif 'stop' == sys.argv[1]:
			daemon.stop()
		elif 'restart' == sys.argv[1]:
			daemon.restart()
		else:
			print "Unknown command"
			sys.exit(2)
		sys.exit(0)
	else:
		print "usage: %s start|stop|restart" % sys.argv[0]
		sys.exit(2)
