from django.conf.urls.defaults import patterns, include, url
from django.conf import settings
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'web.views.home', name='home'),
    # url(r'^web/', include('web.foo.urls')),
	
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
	url(r'^admin/', include(admin.site.urls)),
	#Uncomment the next line to enable the admin:
	(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT }),
	(r'^$','mkmt.views.index'),
	(r'^init','mkmt.views.init'),
	(r'^createXML','mkmt.views.xml'),
	(r'^login','mkmt.views.login_view'),
	(r'^logout','mkmt.views.logout_view'),
	(r'^home','mkmt.views.home'),
	(r'^register','mkmt.views.regis'),
	(r'^user','mkmt.views.user'),
	#(r'^vi/(?P<vi_id>\d+)/vmVICon', 'mkmt.views.manvi'),
	#(r'^vi/(?P<vi_id>\d+)/temVICon', 'mkmt.views.vi_tem'),
	#(r'^vi/(?P<vi_id>\d+)/userVICon', 'mkmt.views.vi_user'),
	(r'^vi/(?P<vi_id>\d+)/deleteVI', 'mkmt.views.vi_del'),
	(r'^requestConfirm','mkmt.views.requestVIConfirm'),
	(r'^vi','mkmt.views.manvi'),
	(r'^host','mkmt.views.host_view'),
	(r'^cloud','mkmt.views.cloud'),
	(r'^request','mkmt.views.requestVI'),
	(r'^editCloudInfo','mkmt.views.editCloud'),
	(r'^createVI','mkmt.views.createVI_view'),
	(r'^controlVM','mkmt.views.controlVM'),
	(r'^controlHost','mkmt.views.controlHost'),
	(r'sendComm','mkmt.views.sendComm'),
	(r'createVM','mkmt.views.createVM'),
	(r'moveVM','mkmt.views.moveVM'),
	(r'moveUser','mkmt.views.moveUser'),
	(r'^createRole','mkmt.views.createRole'),
	(r'^editRole','mkmt.views.editRole'),
	(r'^editVIQuota','mkmt.views.editVI'),
	(r'^queryData','mkmt.views.queryData'),
	(r'^addHost','mkmt.views.addHost'),
	(r'^pollTask','mkmt.views.pollTask'),
)   

