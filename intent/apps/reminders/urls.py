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

urlpatterns = patterns('intent.apps.reminders.views',
    url(r'^$', 'reminders_index', name='recent-reminders'),
    url(r'^new-reminder/$', 'new_reminder', name='new-reminder'),
    url(r'^edit/(?P<reminder_id>\d+)', 'new_reminder', name='edit-reminder'),
)
