#import setting (don't import setting)
import time

def countdown(sec=5,message=None):
	print message
	for i in range(sec):
		time.sleep(1)
		print i
	
