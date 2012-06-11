#!/usr/bin/env python

"""models.py: store additional information related to users
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

from django.db import models

from django.contrib.auth.models import User

from django.db.models import signals
from intent.apps.core.signals import create_profile

class UserProfile(models.Model):
    # This field is required.
    user = models.OneToOneField(User)

    # Other fields here
    provider = models.CharField(max_length=40)

    def __unicode__(self):
        return " %s" % self.user

    def get_absolute_url(self):
        return ('profiles_profile_detail', (), { 'username': self.user.username })

    get_absolute_url = models.permalink(get_absolute_url)