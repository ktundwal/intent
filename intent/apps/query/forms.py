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
from django.forms import Textarea

from django.contrib.admin.widgets import AdminDateWidget
import datetime
from .models import *
from django.utils.safestring import mark_safe

CHOICES=[('Lead generation','Lead generation'),
         ('Product Development','Product development'),
         ('Customer Support','Customer Support'),]

class QueryForm(forms.ModelForm):

    app = forms.ChoiceField(choices=CHOICES, label = 'Engagement App', widget=forms.RadioSelect())
    query = forms.CharField(label="Product/Brand", help_text="Ex: starbucks")
    industry_terms_comma_separated = forms.CharField(label="Industry terms", required=False, help_text="Comma separated values. Ex: coffee, mocha, latte")
    #competitors_comma_separated = forms.CharField(label="Competitors", required=False, help_text="Comma separated values. Ex: McDonalds, Dunkin Donuts")


    class Meta:
        model = Query
        exclude = ['vertical_tracker', 'competitors_comma_separated', 'created_by', 'count', 'interval', 'num_times_run', 'status', 'throttle', 'last_run',
                   'interval', 'latitude', 'longitude', 'radius', 'query_exception',
                   'buy_count', 'recommendation_count', 'question_count', 'commitment_count', 'like_count', 'dislike_count', 'try_count','document_count',  ]
        widgets = {
            'query': Textarea(attrs={'width': 80, 'rows': 20}),
            'industry_terms_comma_separated': Textarea(attrs={'cols': 80, 'rows': 20}),
        }

class VerticalTrackerForm(forms.ModelForm):

    query = forms.CharField(label="Query", help_text="Ex: Tablets")
    query = forms.CharField(label="Query", help_text="Ex: Kindle fire|KindleFire|Kindle Fire HD, iPad|iPad Mini, Google Nexux|Nexus")

    class Meta:
        model = VerticalTracker
        exclude = ['created_by', 'created_on']
