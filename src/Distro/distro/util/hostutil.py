import cputil, memutil, ifutil

def getSpec():
	rdata = {}
	rdata['IP'] = node[0]
	
	cpuinfo = {}
	cpuinfo['number'] = len(cputil.getInfo())
	cpuinfo['model'] = cputil.getInfo()[0]['model name']
	cpuinfo['cache'] = cputil.getInfo()[0]['cache size']

	meminfo = {}
	memtotal, unit = memutil.getInfo()[0]['MemTotal'][0]
	meminfo['size'] = memtotal + ' ' + unit
	
	spec = {'cpu':cpuinfo, 'memory':meminfo}       
	rdata['spec'] = spec
	
	return rdata

def getCpuInfo():
	data = []
	for core in cputil.getLoad():
		if core['core'] == 'all':
			pass
		data.append(100 - float(core['idle']))
	return data

def getMemInfo():
	data = {}
	
	return {}

def getNetworkInfo():
	return {}

def getStorageInfo():
	return {}

def getInfo():
	return { 'cpu_info': getCpuInfo(), 'memory_info':getMemInfo(), 'network_info': getNetworkInfo(), 'storage_info': getStorageInfo()}

if __name__ == '__main__':
	print getCpuInfo()
