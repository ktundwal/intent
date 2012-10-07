from __future__ import division

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
from django.utils.timezone import datetime

class VerticalTracker(models.Model):

    created_by = models.ForeignKey(User)
    name = models.CharField(max_length=200, blank=False)
    query = models.CharField(max_length=200, blank=False)
    created_on = models.DateTimeField(auto_now_add=True, default = datetime.now)

    def __unicode__(self):
        return '%s-%s' % (self.name, self.query)

class Rule(models.Model):
    BUY_GRAMMAR             = 1
    RECOMMENDATION_GRAMMAR  = 2
    QUESTION_GRAMMAR        = 3
    COMMITMENT_GRAMMAR      = 4
    LIKE_GRAMMAR            = 5
    DISLIKE_GRAMMAR         = 6
    TRY_GRAMMAR             = 6
    GRAMMAR_CHOICES = (
        (BUY_GRAMMAR,               'buy'),
        (RECOMMENDATION_GRAMMAR,    'recommendation'),
        (QUESTION_GRAMMAR,          'question'),
        (COMMITMENT_GRAMMAR,        'commitment'),
        (LIKE_GRAMMAR,              'like'),
        (DISLIKE_GRAMMAR,           'dislike'),
        (TRY_GRAMMAR,               'try'),
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
    WAITING_TO_RUN_STATUS = 1
    RUNNING_STATUS = 2
    HOLD_STATUS = 3
    STATUS_CHOICES = (
        (WAITING_TO_RUN_STATUS, 'In queue'),
        (RUNNING_STATUS, 'Running'),
        (HOLD_STATUS, 'Paused'),
        (INACTIVE_STATUS, 'Inactive'),
    )

    created_by = models.ForeignKey(User)

    vertical_tracker = models.ForeignKey(VerticalTracker, related_name='trackers', null=True, blank=True, default=None)

    query = models.CharField(max_length=200, blank=False)
    industry_terms_comma_separated = models.CharField(max_length=200, default="", blank=True)
    competitors_comma_separated = models.CharField(max_length=200, default="", blank=True)

    created_on = models.DateTimeField(auto_now_add=True, default = datetime.now)

    status = models.IntegerField(choices=STATUS_CHOICES, default=WAITING_TO_RUN_STATUS)

    last_run = models.DateTimeField(blank=True, null=True)
    interval = models.IntegerField(default=1800)

    throttle = models.FloatField(default=0.5)

    latitude = models.CharField(max_length=40, blank=True)
    longitude = models.CharField(max_length=40, blank=True)
    radius = models.CharField(max_length=40, blank=True)

    num_times_run = models.IntegerField(default = 0)
    query_exception = models.CharField(max_length=200, blank=True)

    count                   = models.IntegerField(default=0)
    document_count          = models.IntegerField(default=0)
    buy_count               = models.IntegerField(default=0)
    recommendation_count    = models.IntegerField(default=0)
    question_count          = models.IntegerField(default=0)
    commitment_count        = models.IntegerField(default=0)
    like_count              = models.IntegerField(default=0)
    dislike_count           = models.IntegerField(default=0)
    try_count               = models.IntegerField(default=0)

    def buy_percentage(self):
        return percentage(self.buy_count, self.count)

    def recommendation_percentage(self):
        return percentage(self.recommendation_count, self.count)

    def question_percentage(self):
        return percentage(self.question_count, self.count)

    def commitment_percentage(self):
        return percentage(self.commitment_count, self.count)

    def like_percentage(self):
        return percentage(self.like_count, self.count)

    def dislike_percentage(self):
        return percentage(self.dislike_count, self.count)

    def try_percentage(self):
        return percentage(self.try_count, self.count)

    def __unicode__(self):
        val = self.query
        if self.industry_terms_comma_separated:
            val += ' +(%s)' % self.industry_terms_comma_separated
        if self.competitors_comma_separated:
            val += ' -(%s)' % self.competitors_comma_separated
        return val

    class Meta:
        ordering = ['-created_on']
        verbose_name_plural = "Queries"

class Author(models.Model):
    twitter_handle = models.CharField(max_length=40, blank=False)
    name = models.CharField(max_length=40, default='', blank=False)
    profile_image_url = models.URLField(default='http://i.stack.imgur.com/TDbOb.png')

    def __unicode__(self):
        return self.twitter_handle

    class Meta:
        verbose_name_plural = "Authors"

def get_anonymous_author():
    return Author.objects.get_or_create(
        twitter_handle='unknown',
        name='unknown'
    )

class Document(models.Model):

    TWITTER_SOURCE = 1
    FACEBOOK_SOURCE = 3
    SOURCE_CHOICES = (
        (TWITTER_SOURCE, 'Twitter'),
        (FACEBOOK_SOURCE, 'Facebook'),
    )

    NOT_ANALYZED = -1
    NO_INTENT = 0

    # This is unoptimized since a Document may have expressed multiple wants for different query
    # we are tracking, but what are the chances that this will have in tweets?
    result_of = models.ForeignKey(Query, related_name='results', blank=True)

    # Twitter? Facebook?
    source = models.IntegerField(choices=SOURCE_CHOICES, default=TWITTER_SOURCE)

    # author, we will use
    author = models.ForeignKey(Author, related_name='documents')

    # Tweet id
    source_id = models.CharField(max_length=40, unique=True, blank=False)
    date = models.DateTimeField(auto_now_add=True)
    text = models.CharField(max_length=200, blank=True, default='')

    # This will be used to query what all needs analysis in background task
    analyzed = models.BooleanField(default=False)

    # we point to an entry in separate table to look for analytics
    buy_rule            = models.ForeignKey(Rule, related_name='buys',              blank=True, null=True)
    recommendation_rule = models.ForeignKey(Rule, related_name='recommendations',   blank=True, null=True)
    question_rule       = models.ForeignKey(Rule, related_name='questions',         blank=True, null=True)
    commitment_rule     = models.ForeignKey(Rule, related_name='commitments',       blank=True, null=True)
    like_rule           = models.ForeignKey(Rule, related_name='likes',             blank=True, null=True)
    dislike_rule        = models.ForeignKey(Rule, related_name='dislikes',          blank=True, null=True)
    try_rule            = models.ForeignKey(Rule, related_name='tries',             blank=True, null=True)

    def __unicode__(self):
        return '%s-%s' % (self.result_of.query, self.source_id)

    class Meta:
        ordering = ['-date']

class DailyStat(models.Model):
    stat_of = models.ForeignKey(Query, related_name='dailystats', blank=True)
    stat_for = models.DateField()

    document_count          = models.IntegerField(default=0)
    buy_count               = models.IntegerField(default=0)
    recommendation_count    = models.IntegerField(default=0)
    question_count          = models.IntegerField(default=0)
    commitment_count        = models.IntegerField(default=0)
    like_count              = models.IntegerField(default=0)
    dislike_count           = models.IntegerField(default=0)
    try_count               = models.IntegerField(default=0)

    def display(self):
        response = 'Daily stat: %s\n' % self.stat_for.strftime('%h %d %Y')
        response += 'Query: %s\n' % self.stat_of.query
        response += 'Created by: %s\n' % self.stat_of.created_by
        response += 'Total tweets processed today: %d\n' % self.document_count
        response += 'Buy: %f%%\n' % self.buy_percentage()
        response += 'Recommendation: %f%%\n' % self.recommendation_percentage()
        response += 'Question: %f%%\n' % self.question_percentage()
        response += 'Commitment: %f%%\n' % self.commitment_percentage()
        response += 'Like: %f%%\n' % self.like_percentage()
        response += 'Try: %f%%\n' % self.dislike_percentage()
        response += 'Dislike: %f%%\n' % self.try_percentage()

        return response

    def buy_percentage(self):
        return percentage(self.buy_count, self.document_count)

    def recommendation_percentage(self):
        return percentage(self.recommendation_count, self.document_count)

    def question_percentage(self):
        return percentage(self.question_count, self.document_count)

    def commitment_percentage(self):
        return percentage(self.commitment_count, self.document_count)

    def like_percentage(self):
        return percentage(self.like_count, self.document_count)

    def dislike_percentage(self):
        return percentage(self.dislike_count, self.document_count)

    def try_percentage(self):
        return percentage(self.try_count, self.document_count)

    def __unicode__(self):
        return '%s-%s' % (self.stat_for.strftime('%h %d %Y'), self.stat_of.query)

    class Meta:
        ordering = ['stat_for']

def percentage(part, whole):
    return (100 * float(part)/float(whole)) if whole else 0