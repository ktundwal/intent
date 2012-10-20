#!/usr/bin/env python

"""models.py"""

__author__      = 'ktundwal'
__copyright__   = "Copyright 2012, Indraworks"
__credits__     = ["Kapil Tundwal"]
__license__     = "Indraworks Confidential. All Rights Reserved."
__version__     = "0.5.0"
__maintainer__  = "Kapil Tundwal"
__email__       = "ktundwal@gmail.com"
__status__      = "Development"

from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required

urlpatterns = patterns('intent.apps.query.views',
    url(r'^$', 'query_index', name='query_index'),
    url(r'^new-query/$', 'new_query', name='new-query'),
    url(r'^edit/(?P<query_id>\d+)', 'new_query', name='edit-query'),
    url(r'^results/(?P<query_id>\d+)', 'query_results', name='query_results'),
    url(r'^download/(?P<query_id>\d+)', 'download_query_results', name='download_query_results'),
    url(r'^verticaltrackers/$', 'verticaltracker_index', name='verticaltracker_index'),
    url(r'^new-verticaltracker/$', 'new_verticaltracker', name='new-verticaltracker'),
    url(r'^demo/$', 'demo', name='demo'),
    url(r'^process/$', 'process', name='process'),
)
