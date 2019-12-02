autoMode={
'0':'Full Manual',
'1':'Guest Migration',
'2':'Guest&Host Controll',
}

hostStatus={
'0':'shutoff',
'1':'running',
'2':'suspended',
'3':'hibernated'
}

hostActivity={
'0':'None',
'1':'evacuating',
'2':'booting',
}

hostFunction={
'0':'None',
'1':'master',
'2':'slave'
}

hostIsHost={
'0':'No',
'1':'Yes'
}

guestStatus={
'0':'shutoff',
'1':'turned on',
'2':'saved'
}

guestRunningState={
'0':'None',
'1':'running',
'2':'blocked',
'3':'paused',
'4':'shut down',
'5':'shut off',
'6':'crashed'
}

guestActivity={
'-1':'error',
'0':'None',
'1':'cloning',
'2':'booting',
'3':'saving',
'4':'restoring',
'5':'migrating',
'6':'duplicating'
}

templateActivity={
'-1':'error',
'0':'None',
'1':'cloning'
}

def getSimpleGuestStatus(status,runningState):
	if status=='1':
		return guestRunningState[runningState]
	else:
		return guestStatus[status]
