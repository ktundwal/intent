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

def create_profile(sender, instance, signal, created, **kwargs):
    """When user is created also create a matching profile."""

    from intent.apps.core.models import UserProfile

    if created:
        UserProfile(user = instance).save()
        # Do additional stuff here if needed, e.g.
        # create other required related records