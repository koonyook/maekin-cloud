HOST_INFO = '/maekin/var/info'

import json, sys, shutil

if '/maekin/lib/distro/' not in sys.path:
	sys.path.append('/maekin/lib/distro/')

from util import cputil, memutil

def get_my_spec(argv):
	info = {}
	
	info['memory'] = {}
	memtotal, unit = memutil.getInfo()['MemTotal']
	info['memory']['size'] = memtotal + ' ' + unit
	info['memory']['type'] = 'HOD'
	info['memory']['speed'] = 'HOD'

	info['cpu'] = {}
	info['cpu']['number'] = len(cputil.getInfo())
	info['cpu']['model'] = cputil.getInfo()[0]['model name']
	info['cpu']['cache'] = cputil.getInfo()[0]['cache size']
	info['cpu']['speed'] = cputil.getInfo()[0]['cpu MHz']
	
	return json.dumps(info)

def get_host_spec(argv):
	try:
		info = json.loads(open( HOST_INFO , 'r' ).read())
	except IOError:
		return json.dumps([])
	except ValueError:
		#err = open( '/var/log/maekin.mmond.ValueError', 'w' )
		shutil.copy(HOST_INFO, '/var/log/maekin.mmond.ve.info')
		return json.dumps([])

	returndata = []
	if len(argv) == 0:
		for ip in info:
			returndata.append( {'IP':ip, 'spec':info[ip]['spec'],'last_seen':str(info[ip]['last_seen'])} )
		return json.dumps(returndata)

	for ip in argv:
		if ip not in info:
			continue
		else:
			returndata.append({'IP':ip, 'spec':info[ip]['spec'], 'last_seen':info[ip]['last_seen']})
	return json.dumps(returndata)

def get_current_cpu_info(argv):
	try:
		info = json.loads(open( HOST_INFO , 'r' ).read())
	except IOError:
		return json.dumps([])
	except ValueError:
		shutil.copy(HOST_INFO, '/var/log/maekin.mmond.ve.info')
		return json.dumps([])
	
	returndata = []
	if len(argv) == 0:
		for ip in info:
			returndata.append({'IP':ip, 'cpu_info':info[ip]['cpu_info'], 'last_seen':info[ip]['last_seen']})
		return json.dumps(returndata)

	for ip in argv:
		if ip not in info:
			continue
		else:
			returndata.append({'IP':ip, 'cpu_info':info[ip]['cpu_info'], 'last_seen':info[ip]['last_seen']})
	return json.dumps(returndata)

def get_current_memory_info(argv):
	try:
		info = json.loads(open( HOST_INFO , 'r' ).read())
	except IOError:
		return json.dumps([])
	except ValueError:
		shutil.copy(HOST_INFO, '/var/log/maekin.mmond.ve.info')
		return json.dumps([])

	returndata = []
	if len(argv) == 0:
		for ip in info:
			returndata.append({'IP':ip, 'memory_info':info[ip]['memory_info'], 'last_seen':info[ip]['last_seen']})
		return json.dumps(returndata)

	for ip in argv:
		if ip not in info:
			continue
		else:
			returndata.append({'IP':ip, 'memory_info':info[ip]['memory_info'], 'last_seen':info[ip]['last_seen']})
	return json.dumps(returndata)

def get_current_network_info(argv):
	try:
		info = json.loads(open( HOST_INFO , 'r' ).read())
	except IOError:
		return json.dumps([])
	except ValueError:
		shutil.copy(HOST_INFO, '/var/log/maekin.mmond.ve.info')
		return json.dumps([])
	
	returndata = []
	if len(argv) == 0:
		for ip in info:
			returndata.append({'IP':ip, 'network_info':info[ip]['network_info'], 'last_seen':info[ip]['last_seen']})
		return json.dumps(returndata)

	for ip in argv:
		if ip not in info:
			continue
		else:
			returndata.append({'IP':ip, 'network_info':info[ip]['network_info'], 'last_seen':info[ip]['last_seen']})
	return json.dumps(returndata)

def get_current_storage_info(argv):
	try:
		info = json.loads(open( HOST_INFO , 'r' ).read())
	except IOError:
		return json.dumps([])
	except ValueError:
		shutil.copy(HOST_INFO, '/var/log/maekin.mmond.ve.info')
		return json.dumps([])
	
	returndata = []
	if len(argv) == 0:
		for ip in info:
			returndata.append({'IP':ip, 'storage_info':info[ip]['storage_info'], 'last_seen':info[ip]['last_seen']})
		return json.dumps(returndata)

	for ip in argv:
		if ip not in info:
			continue
		else:
			returndata.append({'IP':ip, 'storage_info':info[ip]['storage_info'], 'last_seen':info[ip]['last_seen']})
	return json.dumps(returndata)

def get_current_info(argv):
	try:
		info = json.loads(open( HOST_INFO , 'r' ).read())
	except IOError:
		return json.dumps([])
	except ValueError:
		shutil.copy(HOST_INFO, '/var/log/maekin.mmond.ve.info')
		return json.dumps([])
	
	returndata = []
	if len(argv) == 0:
		for ip in info:
			returndata.append({	'IP':ip, 
				'storage_info':info[ip]['storage_info'], 
				'last_seen':info[ip]['last_seen'],
				'cpu_info':info[ip]['cpu_info'], 
				'network_info':info[ip]['network_info'], 
				'memory_info':info[ip]['memory_info'], 
			})
		return json.dumps(returndata)

	for ip in argv:
		if ip not in info:
			continue
		else:
			returndata.append({
				'IP':ip, 
				'storage_info':info[ip]['storage_info'], 
				'last_seen':info[ip]['last_seen'],
				'cpu_info':info[ip]['cpu_info'], 
				'network_info':info[ip]['network_info'], 
				'memory_info':info[ip]['memory_info'], 
			})
	return json.dumps(returndata)

if __name__ == '__main__':
	print get_host_spec([])
