#!/usr/bin/env python

"""forms.py: store additional information related to users
also see:
    http://birdhouse.org/blog/2009/06/27/django-profiles/
    https://docs.djangoproject.com/en/dev/topics/auth/#storing-additional-information-about-users
"""

__author__      = 'ktundwal'
__copyright__   = "Copyright 2012, Indraworks"
__credits__     = ["Kapil Tundwal"]
__license__     = "Indraworks Confidential. All Rights Reserved."
__version__     = "0.5.0"
__maintainer__  = "Kapil Tundwal"
__email__       = "ktundwal@gmail.com"
__status__      = "Development"

from django import forms
from django.contrib.admin.widgets import AdminDateWidget
import datetime
from .models import *
from django.utils.safestring import mark_safe

class QueryForm(forms.ModelForm):

    sample_queries = [
        'starbucks coffee containing both "starbucks" and "coffee"<br>',
        '<b>kindle fire</b> containing the exact phrase "kindle fire"<br>',
        '<b>coffee OR donut</b> containing either "coffee" or "donut" (or both)<br>',
        '<b>coffee -donut</b> containing "coffee" but not "donut"<br>',
        '<b>#coffee</b> containing the hashtag "coffee"<br>',
        '<b>from:starbucks</b> sent from the user @starbucks<br>',
        '<b>@starbucks</b> mentioning @starbucks',
    ]
    query = forms.CharField(help_text=mark_safe(''.join(sample_queries)))

    class Meta:
        model = Query
        exclude = ['created_by', 'count', 'interval', 'num_times_run', 'status', 'throttle']
