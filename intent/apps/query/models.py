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

from django.db import models
from django.contrib.auth.models import User


class Query(models.Model):
    created_by = models.ForeignKey(User)
    query = models.CharField(max_length=200, blank=False, null=False)
    created_on = models.DateTimeField(auto_now_add=True)

    last_run = models.DateTimeField(blank=True, null=True)
    interval = models.IntegerField(default=1800)

    count = models.IntegerField(default=100)

    throttle = models.FloatField(default=0.5)

    latitude = models.CharField(max_length=40, blank=True, null=True)
    longitude = models.CharField(max_length=40, blank=True, null=True)
    radius = models.CharField(max_length=40, blank=True, null=True)

    def __unicode__(self):
        return self.query

    class Meta:
        ordering = ['-created_on']
        verbose_name = "Querie"

class RunningState(models.Model):
    state = models.CharField(max_length=40, blank=False, null=False)
    query = models.ForeignKey(Query)

    def __unicode__(self):
        return self.state

class Intent(models.Model):
    intent = models.CharField(max_length=40, blank=False, null=False)

    def __unicode__(self):
        return self.intent

class Tweet(models.Model):
    result_of = models.ForeignKey(Query)

    url = models.URLField()
    description = models.CharField(max_length=200, blank=False, null=False)
    date = models.DateTimeField(auto_now_add=True)
    author = models.CharField(max_length=40, blank=False, null=False)
    profile = models.URLField()
    language = models.CharField(max_length=20, blank=False, null=False)
    tweet_id = models.CharField(max_length=40, blank=False, null=False)

    intent = models.ForeignKey(Intent)
    cruxly_api_version = models.CharField(max_length=20)
    cruxly_rule_used = models.CharField(max_length=200)

    def __unicode__(self):
        return '%s-%s' % (self.query, self.tweet_id)

    class Meta:
        ordering = ['-date']