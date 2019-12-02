import time
import thread
import threading

class childThread ( threading.Thread ):

	def run ( self ):
		print "start child"
		closeSocketEvent.wait()
		#time.sleep(10)
		print "end of child"

#thread.start_new_thread(childThread,())
closeSocketEvent=threading.Event()
#closeSocketEvent.clear()
xxx=childThread()

xxx.start()
time.sleep(5)
closeSocketEvent.set()
#print threading.enumerate()

for t in threading.enumerate():
	if t is not threading.currentThread():
		print "found"
		t.join()
		print "joined"

print "end"