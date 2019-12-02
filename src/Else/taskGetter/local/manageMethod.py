import os
import socket
import time
import threading
import subprocess,shlex
import json

import setting

def clean_shutdown(argv):
	
	subprocess.Popen(shlex.split("python /taskGetter/shutdown.py"))

	return "OK"

