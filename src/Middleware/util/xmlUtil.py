

def getValue(dom,tag,attribute=None):
	try:
		#print dom.toxml()
		#print dom.attributes
		#print dom.getElementsByTagName(tag)
		#print dom.nodeName
		#print dom.nodeValue
		#print dom.childNodes
		if dom.nodeName==tag:
			targetTag=dom
		else:
			targetTag=dom.getElementsByTagName(tag)[0]
		
		if attribute==None:
			return targetTag.childNodes[0].nodeValue
		else:
			return targetTag.attributes[attribute].value
	except:
		return None
