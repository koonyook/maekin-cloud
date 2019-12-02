'''
	this file assign CONSTANT_VALUE only

	usage:
		import setting
		print setting.MAIN_PATH
'''
LOG_PATH="/var/log/"
TEST_LOG_PATH="/maekin/var/testlog/"
ANALYSE_PATH="/maekin/var/analyse/"

MAIN_PATH="/maekin/lib/middleware/"			#end with '/' because this is only way to allow path to be "/"

TARGET_IMAGE_PATH="/var/lib/libvirt/images/"	#path that must be mount in every host
TARGET_TEMPLATE_PATH="/maekin/var/templates/"

STORAGE_PATH=	"/maekin/var/storage/"		#this is a path used by nfs server (system can mkdir this automatically)
IMAGE_PATH=	"/maekin/var/storage/images/"		#this path must be in storage path 
TEMPLATE_PATH=	"/maekin/var/storage/templates/"	#this path must be in storage path

CURRENT_INFO_PATH="/maekin/var/current/" #this directory contains currentInfo files of each domain (*.info)
CA_PATH="/maekin/var/CA/"

API_WHITELIST_FILE="/maekin/var/whitelist"	#list of ip that can access middleware API
#INFO_HOST_FILE="/maekin/var/infohost.ip"	#used to put the ip of info host (act like global variable between many processes)
#SLAVE_INFO_HOST_FILE="/maekin/var/slaveinfohost.ip"
CACHE_FILE="/maekin/var/cache.txt"		#keep the important data (by json encoding) for emergency (keep by json encoding of dictionary)
DHCP_CONFIG_FILE="/maekin/var/dhcp-middleware.conf"		#must be included by "/etc/dhcp/dhcpd.conf"
#DB_NFS_DUMP_FILE="/var/lib/libvirt/images/dumpFile.sql"	#for create slave database (send file via nfs)
DB_DUMP_FILE="/maekin/var/dumpFile.sql"
DB_DUMP_TEMP_FILE="maekin/var/dumpTempFile.sql"

CLOUD_BACKUP_FILENAME="backup.info"

MONITOR_PORT=5556				#Port used to connect with monitoring system(Znut)
API_PORT=8080					#Port used to connect with api (global controller)
LOCAL_PORT=50000				#Port used to connect with local controller (must talk about port policy later)
WORKER_PORT=LOCAL_PORT	#8081	#Port used to tell the worker that queue of tasks has been updated

DB_ROOT_PASSWORD="thisisabook"
DB_NAME="middleware"

DB_USERNAME="robot"
DB_PASSWORD="iamarobot"

MAXIMUM_BOOT_TIME=60*4			# booting time that exceed this threshold will be terminate

GUEST_MONITOR_PERIOD=1.5  #second

#IP_CHECKING_PERIOD=5			#do not use now

PLANNER_COLLECTING_PERIOD=60*1	#
PLANNER_ACTION_PERIOD=60*10		#must be even

LOG_CLEANING_PERIOD=60*15		#load log older that X minutes will be clear 
								#(*must longer than any other period)

WEIGHT_RANDOM_TIME=60*3			#weight random process will use log data X minutes ago
HOST_BALANCE_TIME=60*5			#host balancer will use log data X minutes ago
GUEST_BALANCE_TIME=60*3			#guest balancer will use log data X minutes ago
"""

PLANNER_COLLECTING_PERIOD=10	
PLANNER_ACTION_PERIOD=60*4		

LOG_CLEANING_PERIOD=60*10		

WEIGHT_RANDOM_TIME=60*1		
HOST_BALANCE_TIME=60*2		
GUEST_BALANCE_TIME=60*1			
"""
OPEN_HOST_THRESHOLD=0.70		#[0,1]
CLOSE_HOST_THRESHOLD=0.25		#[0,1]

VOLUNTEER_THRESHOLD= 40.0		#[0,100]  (compare with percentRest)
NEED_HELP_THRESHOLD= 33.0		#[0,100]  (compare with percentRest)
