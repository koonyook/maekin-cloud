#update svn
#clear timelog.txt
#clear /etc/udev/rules.d/70-persistent-net.rules
#shutdown

import setting
import subprocess,shlex

open(setting.TIME_LOG_FILE,'w').close()
open('/etc/udev/rules.d/70-persistent-net.rules','w').close()

result=subprocess.Popen(shlex.split("svn update %s"%(setting.MAIN_PATH)))
result.wait()

subprocess.Popen(shlex.split("shutdown -h now"))
