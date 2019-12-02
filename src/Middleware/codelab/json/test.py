import json

x={'IP':'158.108.34.12', 'spec':{
'memory' : { 'size' : '2053732 kB' , 'type' : 'DDR3', 'speed' : '1033 MHz' } ,
'cpu' : { 'number' : '8' , 'model' : 'Intel(R) Core(TM) i7 CPU920 @ 2.67GHz', 'cache':'8192 KB'},
}}

y=[x,x,x]

c=json.dumps(y)
print type(c)
m=json.loads(c)
print type(m)
