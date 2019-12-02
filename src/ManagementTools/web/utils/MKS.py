import sys
import urllib
import time
import types
from xml.dom import minidom
import re

hosturl = ''
curr_cloud_name = '' 
curr_cloud_id = 0
MKS_comm = {}
ownerlist = {}
guestlistname = []

def rUrl(urlinp):
	try:
		b =  urllib.urlopen('http://'+urlinp)
		a = re.sub(r'\s\s+','',str(b.read()))
		return a
	except:
		return 'error request URL : '+urlinp
		
# def init():
	# f = open('./comm_list.mks','r')
	# a = f.read()
	# exec(a)
	# f.close()
	# f = open('./config.mks','r')
	# a = f.read()
	# exec(a)

	# print 'use "quit" to quit shell\n'
def list_comm(pre=''):
	print 'aviable command:',pre
	for x in MKS_comm:
		if x.startswith(pre):
			print '- '+x
def getXML(inp,val=''):
	try:
		if type(inp) == str:
			doc = minidom.parseString(inp)
			if val == '':
				return doc
			else:
				return doc.getElementsByTagName(val)
		return inp.getElementsByTagName(val)
	except:
		return []
def traXML(elems,i):
	res = ''
	if elems.hasChildNodes() :
		for a in elems.attributes.keys():
			res += a+':'+elems.attributes[a].value+'\n'
		for c in elems.childNodes:
			if str(c.nodeValue) == 'None':	
				for x in range(i+1):
					res += '\t'
				res += str(c.localName) + '\n'
				res += traXML(c,i+1) + '\n'
			elif str(c.nodeValue) != '\n':
				res += ':'+str(c.nodeValue) +'\n'
	else:
		for a in elems.attributes.keys():
				res += a+':'+elems.attributes[a].value +'\n'
	return res
				
def getXMLVal(elems,tag):
	a =  elems.getElementsByTagName(tag)
	b = a[0]
	c = b.childNodes
	if len(c) > 0:
		return  c[0].nodeValue
	else:
		return ''
def makeurl(com,arg):
	tmp = MKS_comm[com][1]
	i = 0
	while i < len(MKS_comm[com][0]):
		if MKS_comm[com][0][i][0] != '_':
			tmp+= '?'+MKS_comm[com][0][i]+'='+arg[i]
		elif i < len(arg):
			tmp+= '?'+MKS_comm[com][0][i][1:len(MKS_comm[com][0][i])]+'='+arg[i]
		i += 1
	return tmp
def print_req(com,arg):
	print "'"+com+"'",'require :',
	for ar in MKS_comm[com][0]:
		if ar != MKS_comm[com][0][0]:
			print ',',
		if ar[0] != '_':
			print ar,
		else:
			print '[',ar,']',
def check_require(com,arg):
	count = 0
	for ar in MKS_comm[com][0]:
		if ar[0] != '_':
			count += 1
	return count == len(arg)
def run_command(com,arg):
	if check_require(com,arg):
		if type(MKS_comm[com][1]) != types.FunctionType:
			rUrl(hosturl+makeurl(com,arg))
		else:
			MKS_comm[com][1](*arg)
	else:
		print_req(com,arg)
def getCommand():
	print 'maekin>',
	buffer = raw_input()
	while(buffer != 'quit'):
		inp = buffer.split()
		if len(inp) > 0 and MKS_comm.has_key(inp[0]):
			resp = run_command(inp[0],inp[1:len(inp)])
		else:
			print "error '"+inp[0]+"' command not found "
			#if inp[0] != '':
			#	print 'may be:'
			#	list_comm(inp[0])
		print '\nmaekin>',
		buffer = raw_input()
		print ''

# startup = init()
# getCommand()