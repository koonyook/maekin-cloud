#RED_COLOR='\033[91m'
#GREEN_COLOR='\033[92m'
#BLUE_COLOR='\033[94m'
#END_COLOR='\033[0m'

RED_COLOR = '\x1b[0;31m'
GREEN_COLOR = '\x1b[1;32m'
YELLOW_COLOR = '\x1b[0;33m'
BLUE_COLOR = '\x1b[1;34m'
PURPLE_COLOR = '\x1b[0;35m'
END_COLOR = '\x1b[0;0m'

commandToDetail={
	
	'task_a':{
		'opcode':901,
		'param':[],
		'isMission':False
	},
	'task_b':{
		'opcode':902,
		'param':[],
		'isMission':False
	},
	'simple_mission':{
		'opcode':900,
		'param':['subTask'],
		'isMission':True
	},
	'simple_task':{
		'opcode':999,
		'param':['waitTime'],
		'isMission':False
	},
################################

	'blank_task':{				#dummy task for use when a mission doesn't have subtask (can put as subtask of mission only)
		'opcode':0,
		'param':[],
		'isMission':False
	},
	'guest_create':{
		'opcode':1001,
		'param':['guestName','templateID','memory','vCPU'],
		'optional':['inbound','outbound'],
		'isMission':False
	},
	'guest_destroy':{
		'opcode':1002,
		'param':['guestID'],
		'isMission':False
	},
	'guest_start':{
		'opcode':1003,
		'param':['guestID'],
		'optional':['targetHostID'],
		'isMission':False
	},
	'guest_shutoff':{
		'opcode':1004,
		'param':['guestID'],
		'isMission':False
	},
	'guest_save':{
		'opcode':1005,
		'param':['guestID'],
		'isMission':False
	},
	'guest_restore':{
		'opcode':1006,
		'param':['guestID'],
		'optional':['targetHostID'],	#add later
		'isMission':False
	},
	'guest_suspend':{
		'opcode':1007,
		'param':['guestID'],
		'isMission':False
	},
	'guest_resume':{
		'opcode':1008,
		'param':['guestID'],
		'isMission':False
	},
	'guest_migrate':{
		'opcode':1009,
		'param':['guestID','targetHostID'],
		'isMission':False
	},
	'guest_clone_as_template':{				#skip
		'opcode':1010,
		'param':['guestID','...'],
		'isMission':False
	},
	'guest_scale_cpu':{
		'opcode':1011,
		'param':['guestID','vCPU'],
		'isMission':False
	},
	'guest_scale_memory':{
		'opcode':1012,
		'param':['guestID','memory'],
		'isMission':False
	},
	'guest_duplicate':{
		'opcode':1013,
		'param':['guestName','sourceGuestID'],
		'optional':['memory','vCPU','inbound','outbound'],
		'isMission':False
	},

	'host_add':{							
		'opcode':2001,
		'param':['hostName','MACAddress','IPAddress'],
		'isMission':False
	},
	'host_remove':{
		'opcode':2002,
		'param':['hostID'],
		'isMission':True
	},
	'host_close':{
		'opcode':2003,
		'param':['hostID','mode'],		#mode = {'standby','hibernate','shutdown'}
		'isMission':True
	},
	'host_wakeup':{
		'opcode':2004,
		'param':['hostID'],
		'isMission':False
	},
	'host_evacuate_mission':{
		'opcode':2005,
		'param':['hostID'],		
		'isMission':True
	},

	'global_migrate':{
		'opcode':3101,
		'param':['targetHostID'],
		'isMission':False
	},
	'global_promote':{			#skip
		'opcode':3102,
		'param':[],
		'isMission':False
	},
	'database_migrate':{
		'opcode':3201,
		'param':['targetHostID'],
		'isMission':False
	},
	'database_make_slave':{
		'opcode':3202,
		'param':['targetHostID'],
		'isMission':False
	},
	'database_promote':{		#skip
		'opcode':3203,
		'param':[],
		'isMission':False
	},
	'ca_migrate':{
		'opcode':3301,
		'param':['targetHostID'],
		'isMission':False
	},
	'ca_make_slave':{
		'opcode':3302,
		'param':['targetHostID'],
		'isMission':False
	},
	'ca_promote':{				#skip
		'opcode':3303,
		'param':[],
		'isMission':False
	},
	'nfs_migrate':{
		'opcode':3401,
		'param':['targetHostID'],
		'isMission':False
	},

	
	'guest_balance_mission':{
		'opcode':4001,
		'param':[],
		'isMission':True
	},
	'host_balance_mission':{
		'opcode':4002,
		'param':[],
		'isMission':True
	},
	
	'template_create_from_guest':{
		'opcode':5001,
		'param':['sourceGuestID','description'],
		'isMission':False
	},

	'template_remove':{
		'opcode':5002,
		'param':['templateID'],
		'isMission':False
	}
}
