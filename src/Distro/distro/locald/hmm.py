import sys, time
import json
import setting

from daemon.daemon import Daemon

sys.path.append(setting.MAEKIN_LIB_PATH)
from middleware.util import connection
from middleware.util import general
from method import hmmMethod

class hmm(Daemon):
	'''
	Daemon for receive request from middleware
	'''
	def run(self):
		connection.runServer( setting.HMM_LISTENING_PORT, general.getCommandDict(hmmMethod) )
