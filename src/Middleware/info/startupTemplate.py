import json

ll=[
{
'fileName':'winxp-base.img',
'OS':'WindowsXP SP3',
'size':'8589934592',
'description':'Simple and ready to be used. Please start from remote desktop',
'minimumMemory':'200',
'maximumMemory':'2048'
},
{
'fileName':'ubuntu-base.img',
'OS':'Ubuntu10.04 LTS',
'size':'8589934592',
'description':'Simple and ready to be used. Please start from SSH',
'minimumMemory':'384',
'maximumMemory':'2048'
},
{
'fileName':'centos6-base.img',
'OS':'CentOS 6.2 Minimal',
'size':'8589934592',
'description':'lightweight VM for general usage',
'minimumMemory':'200',
'maximumMemory':'2048'
},
{
'fileName':'centos6-dev-base.img',
'OS':'CentOS 6.2 Dev',
'size':'8589934592',
'description':'template for developer works',
'minimumMemory':'200',
'maximumMemory':'2048'
},
{
'fileName':'centos6-web-base.img',
'OS':'CentOS 6.2 Web',
'size':'8589934592',
'description':'template for create web server',
'minimumMemory':'200',
'maximumMemory':'2048'
}
]

aFile=open('startupTemplate.json','w')
aFile.write(json.dumps(ll))
aFile.close()

for i in range(len(ll)):
	aFile=open(str(i)+'.json','w')
	aFile.write(json.dumps([ll[i]]))
	aFile.close()