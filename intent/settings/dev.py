# Load defaults in order to then add/override with dev-only settings
import os
from intent.settings import *
from common import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    'default': {
        #'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        #'NAME': os.path.join(SITE_ROOT, 'db') + '/development.db', # Or path to database file if using sqlite3.
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "intent_clone",
        'USER': 'django_login',                      # Not used with sqlite3.
        'PASSWORD': 'denver',                  # Not used with sqlite3.
        #'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        "HOST": "",
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# == Twitter OAuth Authentication ==
#
# This mode of authentication is the new preferred way
# of authenticating with Twitter.

# The consumer keys can be found on your application's Details
# page located at https://dev.twitter.com/apps (under "OAuth settings")

TWITTER_CONSUMER_KEY="wtwE84FcSSJnvSjhpgymzA"
TWITTER_CONSUMER_SECRET="40NWaHRERFxFrhS0m003wQpklDQ8or9z1hgYhXGE"

# ... etc.