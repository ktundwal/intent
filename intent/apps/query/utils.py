from pattern import web    # for twitter search
from urllib2 import Request, urlopen, URLError, HTTPError
import socket

import json
import time # to sleep if twitter raises an exception

from intent.apps.core.utils import *

CRUXLY_API = 'http://detectintent.appspot.com/v1/api/detect'

import time

def retry(ExceptionToCheck, tries=4, delay=3, backoff=2, logger=None):
    """Retry calling the decorated function using an exponential backoff.

    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

    :param ExceptionToCheck: the exception to check. may be a tuple of
        excpetions to check
    :type ExceptionToCheck: Exception or tuple
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the delay
        each retry
    :type backoff: int
    :param logger: logger to use. If None, print
    :type logger: logging.Logger instance
    """
    def deco_retry(f):
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            try_one_last_time = True
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                    try_one_last_time = False
                    break
                except ExceptionToCheck, e:
                    msg = "%s, Retrying in %d seconds..." % (str(e), mdelay)
                    if logger:
                        logger.warning(msg)
                    else:
                        print msg
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            if try_one_last_time:
                return f(*args, **kwargs)
            return
        return f_retry  # true decorator
    return deco_retry

@retry(web.SearchEngineLimitError, tries=4, delay=3, backoff=2)
def search_twitter(query, query_count):
    """
    search twitter
    """
    # We'll query for tweets on each candidate.
    # Twitter can handle 150+ queries per hour (actual amount is undisclosed).
    # There are 2078 candidates.
    # Let's do one run in ten hours.
    # That means: 207.8 queries per hour, or 17.3 seconds between each query.
    #delay = 3600.0 / len(candidates) * 10 # 10 means 10 hours

    socket.setdefaulttimeout(60)

    delay = 1 # Disable the timer for testing purposes.
    engine = web.Twitter(throttle=delay, language='en')
    # If twitter is not responding, lay off and try again in 10 minutes.
    # Otherwise, fail for this candidate.
    try: tweets = engine.search(query, start=1, count=query_count) # 100 tweets per query.
    except web.SearchEngineLimitError, limitError:
        log_exception("API limit error during twitter search for query: %s" % web.bytestring(query))
        raise type(limitError)(limitError.message + 'happens for query: %s' % web.bytestring(query))
    except Exception, e:
        log_exception("Exception during twitter search for query: %s" % web.bytestring(query))
        raise type(e)(e.message + 'happens for query: %s' % web.bytestring(query))
    return tweets

def clean_tweet(tweet):
    txt1 = web.plaintext(tweet)
    txt1 = txt1.replace("#", "# ").replace("  ", " ") # Clean twitter hashtags
    txt1 = txt1.replace("\n", " ").replace("  ", " ")
    txt1 = txt1.replace("\t", " ").replace("  ", " ")
    return txt1

@retry(URLError, tries=4, delay=3, backoff=2)
def insert_intents(tweets):
    """
    Input:
    [
        {
            ...
            "content": "me&maa' was suppose to just go to Starbucks but then endedd up going to Dairy Queen&Popeye's.ha.",
            ...
        },
        {
            ...
            "content": "@DethWench they look at me funny in Starbucks... I order coffee, black. They seem....disappointed",
            ...
        },
    ]

    Output
    [
        {
            ...
            "content": "me&maa' was suppose to just go to Starbucks but then endedd up going to Dairy Queen&Popeye's.ha.",
            "intents": [want, promise],
        },
        ...
    ]
    """
    response = tweets
    try:
        #make a request object to hold the POST data and the URL
        #make the request using the request object as an argument, store response in a variable
        result = urlopen(Request(CRUXLY_API, json.dumps(tweets), {'Content-Type': 'application/json'}),
            timeout = 45)

        #store request response in a string
        response = unicode(result.read(), 'utf8')
        response = json.loads(response)

    except URLError, e:
        if isinstance(e.reason, socket.timeout):
            logger.severe("Cruxly API timed out: %r" % e)
        raise type(e)('Cruxly API under heavy load. Please try again later.')

    return response