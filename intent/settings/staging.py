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

    # ... etc.