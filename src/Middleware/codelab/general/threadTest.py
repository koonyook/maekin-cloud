import time
import thread
import threading

def childThread():
	print "start child"
	time.sleep(10)
	print "end of child"

class childThread ( threading.Thread ):
	def run ( self ):
		print "start child"
		time.sleep(10)
		print "end of child"

#thread.start_new_thread(childThread,())
childThread().start()

print threading.enumerate()

for t in threading.enumerate():
	if t is not threading.currentThread():
		print "found"
		t.join()
		print "joined"

print "end"