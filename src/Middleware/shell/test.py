import time,threading
import sys,os

#from shellUtil import getch,getTable

#def childThread():
#	print "start child"
#	time.sleep(10)
#	print "end of child"

#class childThread ( threading.Thread ):
#	def run ( self ):
#		print os.getpid()
#		k=getch()	
#		return


#thread.start_new_thread(childThread,())
#childThread().start()
#print os.getpid()
#print threading.enumerate()
#x=0
#print "dsfadsfadfsadsafasdfsadfsadfasfdsa\r\033[7C"
#print getTable([('abc','def','sasdassa'),('ewrew',675,'2112313'),('','122121',23423),(234,2332233223,665565)])
#print x
#print x
counter=11111
sys.stdout.write('\0337')
while True:
	time.sleep(0.01)
	#sys.stdout.write('\0337')
	sys.stdout.write("hello\nthisis\n%dabook\n"%(counter))
	sys.stdout.write('\0338\033[J')
	counter-=1	

	#if len(threading.enumerate())==1:
	#	break


'''
	for t in threading.enumerate():
		if t is not threading.currentThread():
			print "found"
			t.join()
			print "joined"


print "end"

print "aaa:",
x=getch()
print x
print "bbb-"
'''
