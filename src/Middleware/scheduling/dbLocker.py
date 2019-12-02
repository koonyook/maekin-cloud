import MySQLdb
import setting
from util import cacheFile

class Locker():
	def __init__(self,key):
		self.key=key
		self.db=None

	def lock(self):
		infoHost=cacheFile.getDatabaseIP()
		self.db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
		cursor = self.db.cursor()
		cursor.execute("SELECT GET_LOCK('%s','0');"%(self.key))
		result=cursor.fetchone()[0]
		if result==1:
			return True
		elif result==0:
			return False
		else:
			return False

	def unlock(self):
		if self.db==None:
			return False
		cursor = self.db.cursor()
		cursor.execute("SELECT RELEASE_LOCK('%s');"%(self.key))
		result=cursor.fetchone()[0]
		if result==1:
			self.db.close()
			self.db=None
			return True
		elif result==0:
			return False
		else:
			return False

