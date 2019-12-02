from xml.dom import minidom
doc = minidom.parseString('<myxml>aabbcc<inner a="333" />xxx</myxml>')
print doc.getElementsByTagName('myxml')[0].childNodes[0].nodeValue
print doc.getElementsByTagName('myxml')[0].getElementsByTagName('inner')[0].toxml()