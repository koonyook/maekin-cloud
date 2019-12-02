fi = open('package.txt', 'r')
fo = open('package.out.txt', 'w')
for line in fi.read().split('\n'):
  fo.write( '     <packagereq type=\'mandatory\'>%(pkgname)s</packagereq>\n'%{'pkgname':line} )
fo.close()