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
from decimal import *

class Rule(models.Model):
    WANT_GRAMMAR = 1
    QUESTION_GRAMMAR = 2
    PROMISE_GRAMMAR = 3
    GRAMMAR_CHOICES = (
        (WANT_GRAMMAR, 'want'),
        (QUESTION_GRAMMAR, 'question'),
        (PROMISE_GRAMMAR, 'promise'),
        )

    grammar = models.IntegerField(choices=GRAMMAR_CHOICES)
    grammar_version = models.DecimalField(max_digits=2, decimal_places=1)
    rule = models.CharField(max_length=100, blank=True)
    confidence = models.DecimalField(max_digits=2, decimal_places=1, default=1.0)

    def __unicode__(self):
        return '%d-%s' % (self.grammar, self.rule)

    class Meta:
        verbose_name_plural = "Rules"


class Query(models.Model):
    INACTIVE_STATUS = 0
    RUNNING_STATUS = 1
    WAITING_TO_RUN_STATUS = 1
    HOLD_STATUS = 2
    STATUS_CHOICES = (
        (WAITING_TO_RUN_STATUS, 'In queue'),
        (RUNNING_STATUS, 'Running'),
        (HOLD_STATUS, 'Paused'),
        (INACTIVE_STATUS, 'Inactive'),
    )

    created_by = models.ForeignKey(User)
    query = models.CharField(max_length=200, blank=False, null=False)
    created_on = models.DateTimeField(auto_now_add=True)

    status = models.IntegerField(choices=STATUS_CHOICES, default=WAITING_TO_RUN_STATUS)

    last_run = models.DateTimeField(blank=True, null=True)
    interval = models.IntegerField(default=1800)

    count = models.IntegerField(default=100)

    throttle = models.FloatField(default=0.5)

    latitude = models.CharField(max_length=40, blank=True, null=True)
    longitude = models.CharField(max_length=40, blank=True, null=True)
    radius = models.CharField(max_length=40, blank=True, null=True)

    num_times_run = models.IntegerField(default = 0)
    query_exception = models.CharField(max_length=200, blank=True, null=True)

    def __unicode__(self):
        return self.query

    class Meta:
        ordering = ['-created_on']
        verbose_name_plural = "Queries"

class Document(models.Model):

    TWITTER_SOURCE = 1
    FACEBOOK_SOURCE = 3
    SOURCE_CHOICES = (
        (TWITTER_SOURCE, 'Twitter'),
        (FACEBOOK_SOURCE, 'Facebook'),
    )

    NOT_ANALYZED = -1
    NO_INTENT = 0

    result_of = models.ForeignKey(Query, related_name='results', blank=True)

    source = models.IntegerField(choices=SOURCE_CHOICES, default=TWITTER_SOURCE)

    url = models.URLField()
    description = models.CharField(max_length=200, blank=False, null=False)
    date = models.DateTimeField(auto_now_add=True)
    author = models.CharField(max_length=40, blank=False, null=False)
    profile = models.URLField()
    language = models.CharField(max_length=20, blank=False, null=False)
    source_id = models.CharField(max_length=40, blank=False, null=False)

    analyzed = models.BooleanField(default=False)

    want_rule = models.ForeignKey(Rule, related_name='wants', blank=True)
    question_rule = models.ForeignKey(Rule, related_name='questions', blank=True)
    promise_rule = models.ForeignKey(Rule, related_name='promises', blank=True)
    dislike_rule = models.ForeignKey(Rule, related_name='dislikes', blank=True)

    # http://www.clips.ua.ac.be/pages/pattern-en

    INDICATIVE_MOOD = 1
    IMPERATIVE_MOOD = 2
    CONDITIONAL_MOOD = 3
    SUBJUNCTIVE_MOOD = 4

    MOOD_CHOICES = (
        (NOT_ANALYZED, 'Not analyzed'),
        (INDICATIVE_MOOD, 'Indicative'),
        (IMPERATIVE_MOOD, 'Imperative'),
        (CONDITIONAL_MOOD, 'Conditional'),
        (SUBJUNCTIVE_MOOD, 'Subjunctive'),
    )

    polarity = models.DecimalField(max_digits=2, decimal_places=1,default=Decimal("0"))
    subjectivity = models.DecimalField(max_digits=2, decimal_places=1,default=Decimal("0"))
    intent = models.IntegerField(choices=MOOD_CHOICES, default=NOT_ANALYZED)
    modality = models.DecimalField(max_digits=2, decimal_places=1,default=Decimal("0"))

    def __unicode__(self):
        return '%s-%s' % (self.query, self.source_id)

    class Meta:
        ordering = ['-date']