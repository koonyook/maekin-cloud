from mkmt.models import *
from django.contrib import admin
import mkmt
# for x in mkmt.models.__dict__.keys():
	# if not x.startswith('_') :
		# admin.site.register(x)
admin.site.register(VM)
admin.site.register(Spec)
admin.site.register(ResourceLeft)
admin.site.register(Template)
admin.site.register(Storage)
admin.site.register(DnsIP)
admin.site.register(Host)
admin.site.register(GuestIP)
admin.site.register(Cloud)
admin.site.register(VI)
admin.site.register(Role)
admin.site.register(VMLog)
admin.site.register(HostLog)
admin.site.register(Admin_mkmt)
admin.site.register(currentCloud)
admin.site.register(VIrequest)