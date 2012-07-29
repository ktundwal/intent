from pattern import web    # for twitter search
from patternliboverrides import *   # for twitter class override in pattern lib
from urllib2 import Request, urlopen, URLError, HTTPError
import socket

import json
import time # to sleep if twitter raises an exception
from time import gmtime, strftime

from intent.apps.core.utils import *
from intent.apps.query.models import Rule
from .decorators import *

from datetime import datetime

CRUXLY_API = 'http://detectintent.appspot.com/v1/api/detect'

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
    engine = TwitterEx(throttle=delay, language='en')
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


def trunc(f, n):
    '''Truncates/pads a float f to n decimal places without rounding'''
    slen = len('%.*f' % (n, f))
    return str(f)[:slen]

def get_timestamp_from_twitter_date(twitter_date):
    return datetime.strptime(twitter_date, '%a, %d %b  %Y %H:%M:%S +0000')

def pretty_date(time=False):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    """
    now = datetime.now()
    if type(time) is int:
        diff = now - datetime.fromtimestamp(time)
    elif isinstance(time,datetime):
        diff = now - time
    elif not time:
        diff = now - now
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(second_diff) + " seconds ago"
        if second_diff < 120:
            return  "a minute ago"
        if second_diff < 3600:
            return str( second_diff / 60 ) + " minutes ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return str( second_diff / 3600 ) + " hours ago"
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return str(day_diff) + " days ago"
    if day_diff < 31:
        return str(day_diff/7) + " weeks ago"
    if day_diff < 365:
        return str(day_diff/30) + " months ago"
    return str(day_diff/365) + " years ago"

def run_and_analyze_query(query, query_count):
    """
    Input query, query_count
    Output processed tweets, % wants, % questions, % promises
    """
    tweets = search_twitter(query, query_count)
    processed_tweets = []
    for tweet in tweets:
        cleaned_tweet = clean_tweet(tweet.description)
        #cleaned_tweet = Text(parse(clean_tweet(tweet.desciption))).string
        analyzed_tweet_dict = dict(
            content = cleaned_tweet,    # 'content' key is what cruxly api looks for
            author = tweet.author,
            image = tweet.profile,
            url = "".join(['http://twitter.com/', tweet.author, '/status/', tweet.tweet_id]),
            date = pretty_date(get_timestamp_from_twitter_date(tweet.date)),
            tweet_id = tweet.tweet_id,
        )
        processed_tweets.append(analyzed_tweet_dict)

    if len(processed_tweets) > 0:
        processed_tweets = insert_intents(processed_tweets)

    wants = len([tweet for tweet in processed_tweets if 'want' in tweet['intents']]) * 100 / len(processed_tweets) if len(processed_tweets) > 0 else 1
    questions = len([tweet for tweet in processed_tweets if 'question' in tweet['intents']]) * 100 / len(processed_tweets) if len(processed_tweets) > 0 else 1
    promises = len([tweet for tweet in processed_tweets if 'promise' in tweet['intents']]) * 100 / len(processed_tweets) if len(processed_tweets) > 0 else 1

    return processed_tweets, wants, questions, promises

def lookup_rules_in_db_for_intents(intents):

    want_rule = None
    promise_rule = None
    question_rule = None
    dislike_rule = None

    if 'want' in intents:
        grammar_rule = "Unknown"
        grammar_version = "1.7"
        confidence = 1.0
        want_rule, created = Rule.objects.get_or_create(
            grammar=Rule.WANT_GRAMMAR,
            grammar_version=grammar_version,
            rule=grammar_rule,
            confidence=confidence)
    elif 'promise' in intents:
        grammar_rule = "Unknown"
        grammar_version = "0.8"
        confidence = 1.0
        promise_rule, created = Rule.objects.get_or_create(
            grammar=Rule.PROMISE_GRAMMAR,
            grammar_version=grammar_version,
            rule=grammar_rule,
            confidence=confidence)
    elif 'question' in intents:
        grammar_rule = "Unknown"
        grammar_version = "0.8"
        confidence = 1.0
        question_rule, created = Rule.objects.get_or_create(
            grammar=Rule.QUESTION_GRAMMAR,
            grammar_version=grammar_version,
            rule=grammar_rule,
            confidence=confidence)
    elif 'dislike' in intents:
        grammar_rule = "Unknown"
        grammar_version = "0.1"
        confidence = 1.0
        dislike_rule, created = Rule.objects.get_or_create(
            grammar=Rule.DISLIKE_GRAMMAR,
            grammar_version=grammar_version,
            rule=grammar_rule,
            confidence=confidence)

    return {
        'want_rule': want_rule,
        'promise_rule': promise_rule,
        'question_rule': question_rule,
        'dislike_rule': dislike_rule
    }