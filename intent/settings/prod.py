# Load defaults in order to then add/override with production-only settings
import os
from intent.settings import *
from common import *

DEBUG = False

#import dj_database_url
#DATABASES = {'default': dj_database_url.config(default='postgres://localhost')}

if ENVIRONMENT == 'prod':
    from postgresify import postgresify
    DATABASES = postgresify()

# == Twitter OAuth Authentication ==
#
# This mode of authentication is the new preferred way
# of authenticating with Twitter.

# The consumer keys can be found on your application's Details
# page located at https://dev.twitter.com/apps (under "OAuth settings")

TWITTER_CONSUMER_KEY="ILoiNE36ajsgZyb8428Sdw"
TWITTER_CONSUMER_SECRET="BecIXwOQXtwlyFsXScHbp6eoWnf0SghjhZGKclfzbA"
# ... etc.