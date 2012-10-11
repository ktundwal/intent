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
        "NAME": "intent",
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        #'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        "HOST": "localhost",
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# ... etc.