import thread
import threading
import socket
import time
import os
import sys
import signal
import traceback

MAXIMUM_MESSAGE_SIZE=4096		#biggest is around 2300 but this value should be a relatively small power of 2

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

def sendSwitchSign(sock):
	sock.send('{switch}')

def recvSwitchSign(sock):
	sign=sock.recv(MAXIMUM_MESSAGE_SIZE)
	if sign!='{switch}':
		print 'Error: switch sign =',sign

def sendBlock(sock,message):
	'''
	for message < MAXIMUM_MESSAGE_SIZE
	'''
	sock.send(str(len(message)))
	zero=sock.recv(MAXIMUM_MESSAGE_SIZE)
	if len(message)==0:
		return

	sock.send(message)
	while int(sock.recv(MAXIMUM_MESSAGE_SIZE)) < int(len(message)):
		pass

def recvBlock(sock):
	'''
	use with sendBlock
	'''
	message=""
	targetLength=int(sock.recv(MAXIMUM_MESSAGE_SIZE))
	sock.send(str(len(message)))

	if targetLength==0:
		return ""
	while len(message)<targetLength:	
		message+=sock.recv(MAXIMUM_MESSAGE_SIZE)
		sock.send(str(len(message)))
	return message

def sendArgument(sock,argument):
	'''
	unlimit length
	'''
	if len(argument)>MAXIMUM_MESSAGE_SIZE:
		#segment and send each
		sendBlock(sock,'{long_message}')
		i=0
		while i<len(argument):
			sendBlock(sock,argument[i:i+MAXIMUM_MESSAGE_SIZE])
			i+=MAXIMUM_MESSAGE_SIZE
		sendBlock(sock,'{end_of_message}')
	else:
		sendBlock(sock,argument)

def recvArgument(sock):
	'''
	use with send Argument
	'''
	firstToken=recvBlock(sock)
	if firstToken=='{long_message}':
		completeArgument=''
		while True:
			segment=recvBlock(sock)
			if segment=='{end_of_message}':
				break
			else:
				completeArgument+=segment
	else:
		completeArgument=firstToken
	return completeArgument

def socketCall(host,mainPort,command,argv=[]):
	try:
		#cast argv
		for i in range(len(argv)):
			argv[i]=str(argv[i])

		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((str(host), mainPort))
		
		sendBlock(s,command)
		sendBlock(s,str(len(argv)))
		for argument in argv:
			sendArgument(s,argument)

		#wait for output data
		sendSwitchSign(s)
		completeResult=recvArgument(s)

		s.close()
		'''
		print '*Connect to',str(host)
		print 'result =',completeResult[:40],
		if len(completeResult)>40:
			print "..."
		else:
			print ''
		'''
		return completeResult
		
	except:
		'''
		print "%sThis is handled error.%s"%(RED_COLOR,END_COLOR)
		traceback.print_exc()
		print "%s----------------------%s"%(RED_COLOR,END_COLOR)
		'''
		return None

# for server side
"""
def handleSIGCHLD(signum,frame):
	try:
		while (0,0) != os.waitpid(-1, os.WNOHANG):
			pass
	except:
		pass
"""

def runServer(mainPort,commandDict):
	'''
	mainPort = first port to be connected
	commandDict = dictionary map from commandString to function (these function get only one list of string parameter)
	'''
	host = ''					# Symbolic name meaning all available interfaces
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind((host, mainPort))
	#signal event handler for killing zombies
	#signal.signal(signal.SIGCHLD, handleSIGCHLD)
	while True:
		s.listen(1)
		#cancel interrupt for a while
		#signal.signal(signal.SIGCHLD, signal.SIG_IGN)
		try:
			conn, addr = s.accept()
		except:
			s.shutdown(socket.SHUT_RDWR)
			print "It's beautiful ending."
			sys.exit(0)
		#print 'Connected by', addr
		#fork it
		pid = os.fork()
		if pid==0: #this is child process, must still connect		
			print 'Connected in new process by', addr
			command = recvBlock(conn)
			print GREEN_COLOR+command+END_COLOR
			
			argc = int(recvBlock(conn))
			argv = []
			for i in range(argc):
				completeArgument=recvArgument(conn)
				argv.append(completeArgument)
			
			#print argv
			#addition for special case
			closeConnEvent=threading.Event()
			try:
				while True:
					index=argv.index('{socket_connection}')
					argv[index]=[conn,s,closeConnEvent]
			except:
				pass
			
			#do something that is a real process
			if command in commandDict.keys():
				try:
					result=str(commandDict[command](argv))
				except:
					print "%sThis is handled error.%s"%(RED_COLOR,END_COLOR)
					traceback.print_exc()
					print "%s----------------------%s"%(RED_COLOR,END_COLOR)
					result="Error:\n Turn on debug mode to see error in console"
			else:
				result="Error\nCommand: %s not match in commandDict"%command

			if result==None:
				result=''
			
			recvSwitchSign(conn)
			sendArgument(conn,result)
			
			#time.sleep(0.5)	#bring out at 6/3/2012 (hope overall communication will be faster without bug)
			conn.close()
			s.close() #this line was add later to fix a bug

			#tell every thread that conn was closed (via share variable)
			closeConnEvent.set()	#any thread who call closeConnEvent.wait() will be blocked until this line

			#should wait until every thread of this process has finish before _exit
			for aThread in threading.enumerate():
				if aThread is not threading.currentThread():
					aThread.join()
			
			###s.shutdown(socket.SHUT_RDWR)	#shutdown at child process
			s.close()
			print "before exit",addr
			#os.exit(0)
			os._exit(0)
			print "after exit"
		
		else:	#this is parent process, must close connection and go to listen
			###conn.shutdown(socket.SHUT_RDWR)
			conn.close()

			#enable interrupt again
			#signal.signal(signal.SIGCHLD, handleSIGCHLD)
			
			try:
				while (0,0)!=os.waitpid(-1, os.WNOHANG):
					pass
			except:
				pass
			
