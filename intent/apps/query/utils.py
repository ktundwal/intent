from pattern import web    # for twitter search
from patternliboverrides import *   # for twitter class override in pattern lib
import socket
import requests

from django.utils.timezone import utc, datetime, timedelta
import shlex

import json
import time # to sleep if twitter raises an exception
from time import gmtime, strftime

from intent.apps.core.utils import *
from intent.apps.query.models import Rule, Document, DailyStat
from .decorators import *

from intent import settings

CRUXLY_API_TIMEOUT = 120
TWEETS_PER_API = 10

if settings.ENVIRONMENT == 'prod':
    CRUXLY_SERVER = 'detectintent'
    #CRUXLY_SERVER = 'api-dev'
else:
    CRUXLY_SERVER = 'api-dev'

CRUXLY_API = 'http://' + CRUXLY_SERVER + '.appspot.com/v1/api/detect'
#CRUXLY_API = 'http://localhost:8888/v1/api/detect'

logger.info('ENVIRONMENT = %s. Cruxly API = %s' % (settings.ENVIRONMENT, CRUXLY_API))

@retry(web.SearchEngineLimitError, tries=2, delay=3, backoff=2)
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
        raise type(e)(e.message + ' for query: %s' % web.bytestring(query))
    return tweets

def clean_tweet(tweet):
    txt1 = web.plaintext(tweet)
    txt1 = txt1.replace("#", "# ").replace("  ", " ") # Clean twitter hashtags
    txt1 = txt1.replace("\n", " ").replace("  ", " ")
    txt1 = txt1.replace("\t", " ").replace("  ", " ")
    return txt1

#@retry(URLError, tries=1, delay=3, backoff=2)
def insert_intents(tweets, caller_logger):
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
        tweets_json = json.dumps(tweets)
        r = requests.post(CRUXLY_API, data=tweets_json, timeout=CRUXLY_API_TIMEOUT)
        if r.status_code == 202:
            #store request response in a string
            response = unicode(r.content, 'utf8')
            response = json.loads(response)

    except requests.URLRequired, e:
        raise type(e)('invalid url')
    except requests.HTTPError, e:
        raise type(e)('HTTP error')
    except requests.ConnectionError, e:
        raise type(e)('Connection error')
    except requests.RequestException, e:
        raise type(e)('ambiguous exception')
    except Exception, e:
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

def run_and_analyze_query(key_term, industry_terms_comma_separated, query_count, logger):
    """
    Input query, query_count
    Output processed tweets, % wants, % questions, % promises
    """
    start = time.time()

    all_tweets = search_twitter(create_query(key_term, industry_terms_comma_separated), query_count)
    after_twitter_search = time.time()

    chunked_tweets = list(chunks(all_tweets, TWEETS_PER_API))
    merged_chunked_tweets = []
    chunks_done = 0
    for tweets in chunked_tweets:
        try:
            processed_tweets = []
            for tweet in tweets:
                cleaned_tweet = clean_tweet(tweet.description)
                #cleaned_tweet = Text(parse(clean_tweet(tweet.desciption))).string
                analyzed_tweet_dict = dict(
                    content = cleaned_tweet,    # 'content' key is what cruxly api looks for
                    author = tweet.author,
                    author_user_name = tweet.author_user_name,
                    image = tweet.profile,
                    url = "".join(['http://twitter.com/', tweet.author, '/status/', tweet.tweet_id]),
                    date = pretty_date(get_timestamp_from_twitter_date(tweet.date)),
                    tweet_id = tweet.tweet_id,
                    kip = get_kip(key_term, industry_terms_comma_separated)
                )
                processed_tweets.append(analyzed_tweet_dict)

            if len(processed_tweets) > 0:
                processed_tweets = insert_intents(processed_tweets, logger)
                merged_chunked_tweets += processed_tweets

            chunks_done += 1
        except Exception, e:
            log_exception(message="Cruxly API failed to process %d chunk containing %d tweets. %d chunks left"
                                  % (chunks_done, len(tweets), len(chunked_tweets) - chunks_done))

    after_cruxly_api = time.time()

    logger.info("TIME TAKEN: Cruxly[%d s], Twitter[%d s]"
                % (int(round(after_cruxly_api - after_twitter_search)),
                    int(round(after_twitter_search - start))))
    return merged_chunked_tweets

def create_unknown_rule(intents, intent_str, intent_id):
    rule = None

    if intent_str in intents:
        grammar_rule = "Unknown"
        grammar_version = "1.7"
        confidence = 1.0
        rule, created = Rule.objects.get_or_create(
            grammar=intent_id,
            grammar_version=grammar_version,
            rule=grammar_rule,
            confidence=confidence)

    return rule

def get_or_create_todays_daily_stat(query):
    try:
        daily_stat = DailyStat.objects.filter(stat_of=query, stat_for=datetime.utcnow().date())[0]
    except: # daily_stat.DoesNotExist:
        daily_stat = None

    if not daily_stat:
        daily_stat = DailyStat.objects.create(
            stat_of              = query,
            stat_for             = datetime.utcnow().replace(tzinfo=utc))

    return daily_stat

def create_query(key_term, industry_terms_comma_separated):
    if industry_terms_comma_separated and len(industry_terms_comma_separated) > 0:
        splitter = shlex.shlex(industry_terms_comma_separated, posix=True)
        splitter.whitespace += ','
        splitter.whitespace_split = True
        industry_terms = list(splitter)
        if key_term:
            industry_terms.append(key_term)
        return " OR ".join(industry_terms)
    else:
        return key_term

def get_kip(key_term, industry_terms_comma_separated):
    if industry_terms_comma_separated and len(industry_terms_comma_separated) > 0:
        splitter = shlex.shlex(industry_terms_comma_separated, posix=True)
        splitter.whitespace += ','
        splitter.whitespace_split = True
        industry_terms = list(splitter)
        industry_terms.append(key_term)
        return industry_terms
    else:
        return key_term

def parse_comma_separated_text(text):
    splitter = shlex.shlex(text, posix=True)
    splitter.whitespace += ','
    splitter.whitespace_split = True
    return list(splitter)

def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]