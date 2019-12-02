import sys
import traceback
def makeError():
	int('eeeeefffggg')

try:
	makeError()
except: # Exception as inst:
	#print type(inst)
	#print inst.args
	#print inst
	#print sys.exc_info()
	#print sys.exc_info()[2].tb_lineno
	#print sys.exc_traceback.tb_lineno 
	#print sys.exc_info()[2]
	#print sys.exc_traceback
	traceback.print_exc()
	print "hello"