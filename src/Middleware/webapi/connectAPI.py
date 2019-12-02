from util import connection,general
from util import shortcut
from scheduling import queue

import cherrypy


class GetToken(object):
	def index(self):
		content='''
			<token>hello</token>
		'''
		return shortcut.response('success', content, "this is a token")

	index.exposed = True

class Connect(object):
	getToken = GetToken()
