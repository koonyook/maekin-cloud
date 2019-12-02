import cputil, memutil, ifutil 

hostlist = node

def get_host_spec(argv):
	if argv == []:
		for ip in hostlist[1:]:
			print 'get_host_spec all'
	elif argv == hostlist[0]:
		
