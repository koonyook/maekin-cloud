import re
#test regular expression only

content = open('example.conf','r').read()
print content
m=re.match(r"^include\s*\"(?P<INCLUDE>.+)\";\s*subnet\s*(?P<SUBNET>(\d+\.){3}\d+)\s+netmask\s+(?P<NETMASK>(\d+\.){3}\d+)\s*{\s*(?P<COMMENT_DEFAULT_ROUTE>#|)\s*option\s+routers\s+(?P<DEFAULT_ROUTE>((\d+\.){3}\d+)|)\s*;\s*(?P<COMMENT_DOMAIN_NAME_SERVERS>#|)\s*option\s+domain-name-servers\s+(?P<DOMAIN_NAME_SERVERS>(((\d+\.){3}\d+\s*,\s*)*(\d+\.){3}\d+)|)\s*;\s*(?P<BINDINGS>(host\s+.+\s*{\s*hardware\s+ethernet\s+([\dABCDEF]{2}:){5}[\dABCDEF]{2}\s*;\s*fixed-address\s+(\d+\.){3}\d+\s*;\s*}\s*)*)}",content)

print m.groupdict()
hostConfig = m.groupdict()['BINDINGS']
m2=re.finditer(r"host\s+(?P<HOST_NAME>.+)\s*{\s*hardware\s+ethernet\s+(?P<MAC_ADDRESS>([\dABCDEF]{2}:){5}[\dABCDEF]{2})\s*;\s*fixed-address\s+(?P<IP_ADDRESS>(\d+\.){3}\d+)\s*;\s*}",hostConfig)
for e in m2:
	print e.groupdict()