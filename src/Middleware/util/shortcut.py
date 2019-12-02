import setting
from util import cacheFile
import cherrypy
import MySQLdb
import traceback

def response(responseType,content,message=None):	#responseType = { 'success', 'error', 'waiting' }
	'''
	this is shortcut for API module
	'''
	if message==None:
		messagePart=""
	else:
		messagePart="<message>%s</message>"%(message)

	cherrypy.response.headers['Content-Type']= 'text/xml'
	return '''<response type="%s">
<content>
%s
</content>
%s
</response>'''%(responseType,content,messagePart)

def responseTaskID(taskID,message=None):
	'''
	this is shortcut for API module that is waiting type
	'''
	if taskID==None:
		return response('error','',message)
	else:
		return response('waiting','<task taskID="%s" />'%(str(taskID)),message)

#this is shortcut for worker to update output to the database
def storeFinishMessage(taskID,message):
	'''
	store finishMessage only (used in core)
	'''
	try:
		infoHost=cacheFile.getDatabaseIP()
		db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
		cursor = db.cursor()
		cursor.execute("UPDATE `tasks` SET `finishMessage`='%s' WHERE `taskID`=%s"%(message,str(taskID)))
		db.close()
		return True

	except:
		traceback.print_exc()
		return False
