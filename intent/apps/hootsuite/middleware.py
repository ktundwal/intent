from intent.apps.core.utils import logger

__author__ = 'self'

from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ImproperlyConfigured

import hashlib
from intent.settings.common import *

# ref: http://stackoverflow.com/questions/5023762/token-based-authentication-in-django

class TokenMiddleware( object ):
    """Authentication Middleware for Hootsuite using a token.
    Backend will get user.
    """
    def process_request(self, request):
        if not hasattr(request, 'user'):
            raise ImproperlyConfigured(
                "The Django remote user auth middleware requires the"
                " authentication middleware to be installed.  Edit your"
                " MIDDLEWARE_CLASSES setting to insert"
                " 'django.contrib.auth.middleware.AuthenticationMiddleware'"
                " before the RemoteUserMiddleware class.")

        # If the user is already authenticated and that user is the user we are
        # getting passed in the headers, then the correct user is already
        # persisted in the session and we don't need to continue.
        if request.user.is_authenticated():
            if request.REQUEST.get('uid', ''):
                if request.user.username == 'hs_%s' % request.REQUEST.get('uid'):
                    return
                else:
                    logout(request)
            else:
                return

        pid = request.REQUEST.get('pid', '')
        if pid:
            request.session['hootsuite_pid'] = pid

        lang = request.REQUEST.get('lang', '')
        if pid:
            request.session['hootsuite_lang'] = lang

        uid = request.REQUEST.get('uid', '')
        if uid:
            request.session['hootsuite_uid'] = uid

        theme = request.REQUEST.get('theme', '')
        if theme:
            request.session['hootsuite_theme'] = theme

        # request contains <QueryDict: {u'lang': [u'en'], u'uid': [u'5048335'], u'i': [u'5048335'], u'pid': [u'695620'],
        # u'ts': [u'1356556883'], u'theme': [u'classic'], u'token': [u'7d59cb8ef43c5c8aa6c95cfc26d87758b4c9bdb8'],
        # u'timezone': [u'-25200'], u'isSsl': [u'0']}>

        try:
            token = request.REQUEST.get('token', '')
            timestamp = request.REQUEST.get('ts', '')
            timezone = request.REQUEST.get('timezone', '')
        except KeyError:
            # If specified header doesn't exist then return (leaving
            # request.user set to AnonymousUser by the
            # AuthenticationMiddleware).
            return

        logger.info('Got called with hootsuite_user_id = %s and pid = %s' % (uid, pid))

        # see http://hootsuite.com/developers/app-directory/docs/authentication
        if hashlib.sha1(uid + timestamp + HOOTSUITE_SSO_SHARED_SECRET).hexdigest() != token:
            logger.error('Request token dont match. Quitting')
            return

        user = authenticate(timestamp=timestamp, pid=pid, hootsuite_uid=uid, token=token)
        if user:
            # User is valid.  Set request.user and persist user in the session
            # by logging the user in.
            request.user = user
            login(request, user)
            logger.info('Logged user: %s' % user.username)
