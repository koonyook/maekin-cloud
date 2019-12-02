import setting

import sys,os
import time
import subprocess,shlex
from xml.dom import minidom

import MySQLdb
import json

from dhcp import dhcpController
from util import network
from util import connection
from util import cacheFile
from service import caService,dbService,nfsService,globalService

#find my MAC Address (*must know to get right ip address for set static ip first)
myMAC = network.getMyMACAddr()
myIP = None

inputFile=sys.argv[1]

try:
	templateJSON=open(inputFile,'r').read()
except:
	print inputFile,"not found."
	sys.exit()

try:
	templates=json.loads(templateJSON)
except:
	print "invalid file."
	sys.exit()

#check appearing of file
existTemplates=os.listdir(setting.TARGET_TEMPLATE_PATH)
for element in templates:
	if element['fileName'] not in existTemplates:
		print element,"do not exist in template directory, please copy template to",setting.TEMPLATE_PATH,"at nfs server"
		sys.exit()

dbIP=cacheFile.getDatabaseIP()
db = MySQLdb.connect(dbIP, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
cursor = db.cursor()

for element in templates:
	cursor.execute("SELECT `templateID` FROM `templates` WHERE `fileName`='%s'"%(element['fileName']))
	if cursor.fetchone()==None:
		cursor.execute("""
		INSERT INTO `templates` 
			(`fileName`, `OS`, `size`, `description`, `minimumMemory`, `maximumMemory`)
		VALUES
			('%s', '%s', '%s', '%s', '%s', '%s')
		"""%(element['fileName'],element['OS'],element['size'],element['description'],element['minimumMemory'],element['maximumMemory']))

print "Finish template installing."
