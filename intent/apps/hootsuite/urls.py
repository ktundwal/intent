#!/usr/bin/env python

"""urls.py"""

__author__      = 'ktundwal'
__copyright__   = "Copyright 2012, Indraworks"
__credits__     = ["Kapil Tundwal"]
__license__     = "Indraworks Confidential. All Rights Reserved."
__version__     = "0.5.0"
__maintainer__  = "Kapil Tundwal"
__email__       = "ktundwal@gmail.com"
__status__      = "Development"

from django.conf.urls import patterns, url
from django.views.generic import TemplateView
from .views import LoginView, StreamFormCreateView, StreamView, tokenexchange, WelcomeView, StreamFormUpdateView

urlpatterns = patterns('intent.apps.hootsuite.views',
    url(r'^welcome/$', WelcomeView.as_view(), name='welcome'),
    url(r'^login/$', LoginView.as_view(), name='login'),

    url(r'setup/add/$', StreamFormCreateView.as_view(), name='setup'),
    url(r'setup/edit/$', StreamFormUpdateView.as_view(), name='update'),
    url(r'setup/$', StreamFormUpdateView.as_view(), name='detail'),

    url(r'^stream/$', StreamView.as_view(), name='stream'),
    url(r'^receiver/$', TemplateView.as_view(template_name="hs/receiver.html"), name='receiver'),
    url(r'^tokenexchange/$', tokenexchange, name='tokenexchange'),

    url(r'^process/$', 'process', name='process'),

    url(r'^results/$', 'query_results', name='query_results'),
)
