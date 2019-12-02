from util import connection
import time
import json
#longString='a'*10000
#s=connection.socketCall(host='158.108.34.12',mainPort=50000,command='test_connection_bug',argv=['{socket_connection}','158.108.34.12','mysql-bin.000037','7519',longString,'shortString'])
#print s
#print connection.socketCall('127.0.0.1',50000,'are_you_running_dhcpd')
#print connection.socketCall('127.0.0.1',50000,'have_this_mac',['00:12:f0:d4:8f:35'])
#print connection.socketCall('158.108.34.95',50000,'soft_work')
#print connection.socketCall('158.108.34.85',50000,'test_type')
#print connection.socketCall('158.108.34.85',50000,'set_work',[json.dumps(['soft_work',2.0,0.0,60.0]),json.dumps([]),'{socket_connection}'])
#time.sleep(0.66)
#print connection.socketCall('158.108.34.85',50000,'set_work',[json.dumps(['soft_work',2.0,0.0,60.0]),json.dumps([]),'{socket_connection}'])
#time.sleep(0.66)
print connection.socketCall('158.108.34.111',50000,'log_network',[str(20),'{socket_connection}'])
