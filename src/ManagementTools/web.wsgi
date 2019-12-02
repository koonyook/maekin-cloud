import os, sys
sys.path.append('/maekin/lib/managementtool/')
sys.path.append('/maekin/lib/managementtool/web')
sys.path.append('/maekin/lib/managementtool/web/utils')
os.environ['DJANGO_SETTINGS_MODULE'] = 'web.settings'
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()