#!/usr/bin/env python
#
# chkconfig: 345 97 02
# description:  Maekin Local Host Monitoring Daemon.
# processname: mmond
# pidfile: /var/run/mmond.pid

import sys

sys.path.append("/maekin/lib/distro")
import setting

sys.path.append(setting.MONITOR_MODULE_PATH)
from locald.mmond import mmond

if __name__ == "__main__":
	daemon = mmond('/var/run/mmond.pid', 'mmond' ,stderr=setting.LOG_PATH+'maekin.mmond.err', stdout=setting.LOG_PATH+'maekin.mmond.out')
	if len(sys.argv) == 2:
		if 'start' == sys.argv[1]:
			daemon.start()
		elif 'stop' == sys.argv[1]:
			daemon.stop()
		elif 'restart' == sys.argv[1]:
			daemon.restart()
		elif 'status' == sys.argv[1]:
			daemon.status()
		else:
			print "Unknown command"
			sys.exit(2)
		sys.exit(0)
	else:
		print "usage: %s start|stop|restart" % sys.argv[0]
		sys.exit(2)
