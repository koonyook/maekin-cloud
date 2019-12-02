"""555 this string will be in __doc__ attribute of this module"""
import inspect

def aaa():
	'''thi\ns is a dog;
and this is rest %s
	'''
	#%(str(1234))
	print 'yes'
	return True

def bbb():
	'''
	this is a bird
	'''
	#print bbb
	#print __doc__   #of this module
	#print inspect.getframeinfo(inspect.currentframe()).function
	print getMyFunctionName()
	
	#print __dict__
	#print im_self
	#print im_func
	#print func_globals
	#print func_dict
	#print __module__
	#print func_name
	#print __self__
	#print dir(
	return False

def getMyFunctionName():
	outerFunctionName=None
	frame = inspect.currentframe()
	try:
		outerFunctionName=inspect.getouterframes(frame)[1][3]
	finally:
		del frame
	return outerFunctionName

#print help.__doc__.split(';')[0]
bbb()