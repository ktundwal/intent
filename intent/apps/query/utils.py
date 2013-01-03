from pattern import web    # for twitter search
from tweepy.error import TweepError
from intent.settings.common import TWITTER_ACCESS_TOKEN_CRUXLY, TWITTER_ACCESS_TOKEN_SECRET_CRUXLY
from intent.settings.prod import TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET
from patternliboverrides import *   # for twitter class override in pattern lib
import socket
import requests

from django.utils.timezone import  datetime
import shlex

import json
import time # to sleep if twitter raises an exception

from intent.apps.core.utils import *
from .decorators import *

from intent import settings
import tweepy

CRUXLY_API_TIMEOUT = 120
TWEETS_PER_API = 100

if settings.ENVIRONMENT == 'mbp':
    CRUXLY_SERVER = 'localhost:8080/api'
else:
    CRUXLY_SERVER = 'api.cruxly.com'

CRUXLY_API = 'http://' + CRUXLY_SERVER + '/rest/v1/analyze'

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

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

def get_user_twitter_access_token():
    return TWITTER_ACCESS_TOKEN_CRUXLY, TWITTER_ACCESS_TOKEN_SECRET_CRUXLY

def search_twitter_using_tweepy(query, logger=None):
    try:
        auth = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
        token, token_secret = get_user_twitter_access_token()
        auth.set_access_token(token, token_secret)
        api = tweepy.API(auth)
        return api.search(
            q=query,
            rpp=100,
            result_type="recent",
            include_entities=True,
            lang="en")
    except TweepError, te:
        log_exception(logger,
            "TWITTER ERROR! reason = %s, response = %s, keywords = %s, consumer_key = %s, consumer_secret = %s" %
                (te.reason, te.response, query, TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET))
        raise

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
            "author": "14726127",
            "url": "http://twitter.com/14726127/status/262266293187670016",
            "author_user_name": "drbuk",
            "image": "http://a0.twimg.com/profile_images/1291204822/Screen_shot_2011-03-29_at_09.11.20_normal.png",
            "kip": {
                "genericterms": [],
                "competingterms": [],
                "keyterms": [
                    "kindle"
                ]
            },
            "longitude": null,
            "tweet_id": "262266293187670016",
            "text": "Amazon: $199 Kindle Fire HD had 'biggest day since launch' after iPad mini event http://t.co/RKRFCz4M",
            "date": "2012-10-27 18:55:31",
            "latitude": null
        },
    ]

    Output
    [
        {
            u'intents': [
                {
                    u'intent': u'question'
                }
            ],
            u'author': u'261471131',
            u'text': u'My mom calls her Kindle and iPad?! Not exactly mother.',
            u'image': u'http://a0.twimg.com/profile_images/2771975641/f5d7d1e323ab1b3442c1eca357ab645f_normal.jpeg',
            u'kip': {
                u'genericterms': [],
                u'keyterms': [
                    u'kindle'
                ],
                u'key': u'kindle_',
                u'competingterms': []
            },
            u'longitude': None,
            u'source': None,
            u'tweet_id': u'262266595454357504',
            u'author_user_name': u'kjerstianna',
            u'date': u'2012-10-27 18:56:43',
            u'latitude': None,
            u'type': None,
            u'id': None
        },
    ]
    """
    response = tweets
    try:
        #make a request object to hold the POST data and the URL
        #make the request using the request object as an argument, store response in a variable
        #dthandler = lambda obj: obj.isoformat() if isinstance(obj, datetime.datetime) else None
        #tweets_json = json.dumps(tweets, default=dthandler)
        tweets_json = json.dumps(tweets)
        headers = {'content-type': 'application/json'}
        r = requests.post(CRUXLY_API, data=tweets_json, headers=headers, timeout=CRUXLY_API_TIMEOUT)
        if r.status_code == 200:
            #store request response in a string
            response = unicode(r.content, 'utf8')
            response = json.loads(response)
        else:
            raise Exception("Got " + r.status_code + " from Cruxly API")

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

def run_and_analyze_query(kip, query_count, logger):
    """
    Input query, query_count
    Output processed tweets, % wants, % questions, % promises
    """
    start = time.time()

    query_from_kip = create_query(kip)
    logger.info("Going to search twitter for " + query_from_kip);
    #all_tweets = search_twitter(query_from_kip, query_count)
    all_tweets = search_twitter_using_tweepy(query_from_kip, logger=logger)
    after_twitter_search = time.time()

    chunked_tweets = list(chunks(all_tweets, TWEETS_PER_API))
    merged_chunked_tweets = []
    chunks_done = 0
    for tweets in chunked_tweets:
        try:
            tweets_without_intents = []
            for tweet in tweets:
                try:
                    cleaned_tweet = clean_tweet(tweet.text)
                    analyzed_tweet_dict = dict(
                        text = cleaned_tweet,    # 'content' key is what cruxly api looks for
                        author = tweet.from_user_id_str,
                        author_user_name = tweet.from_user,
                        image = tweet.profile_image_url,
                        url = "".join(['http://twitter.com/', tweet.from_user_id_str, '/status/', tweet.id_str]),
                        date = tweet.created_at.strftime(DATETIME_FORMAT),
                        tweet_id = tweet.id_str,
                        kip = kip.dict,
                        latitude = tweet.geo['coordinates'][0] if tweet.geo else None,
                        longitude = tweet.geo['coordinates'][1] if tweet.geo else None,
                    )
                    tweets_without_intents.append(analyzed_tweet_dict)
                except Exception, e:
                    log_exception(message="Cruxly API failed to process tweet [%s]" % cleaned_tweet)

            if len(tweets_without_intents) > 0:
                tweets_with_intents = insert_intents(tweets_without_intents, logger)
                merged_chunked_tweets += tweets_with_intents

            chunks_done += 1
        except Exception, e:
            log_exception(message="Cruxly API failed to process %d chunk containing %d tweets. %d chunks left"
                                  % (chunks_done, len(tweets), len(chunked_tweets) - chunks_done))

    after_cruxly_api = time.time()

    logger.info("TIME TAKEN: Cruxly[%d s], Twitter[%d s]"
                % (int(round(after_cruxly_api - after_twitter_search)),
                    int(round(after_twitter_search - start))))
    return merged_chunked_tweets

def create_query(kip):
    terms = ['\"' + term + '\"' for term in kip.product + kip.industryterms]
    return " OR ".join(terms)

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
    if text:
        return text.split(',')
#        splitter = shlex.shlex(text, posix=True)
#        splitter.whitespace += ','
#        splitter.whitespace_split = True
#        return list(splitter)
    else:
        return []

def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

class Kip():
    def __init__(self, keyterms="", genericterms_comma_separated="", competingterms_comma_separated=""):
        self.product = parse_comma_separated_text(keyterms)
        self.industryterms = parse_comma_separated_text(genericterms_comma_separated)
        self.competitors = parse_comma_separated_text(competingterms_comma_separated)

    @property
    def dict(self):
        return {
            "keyterms": self.product,
            "genericterms": self.industryterms,
            "competingterms": self.competitors
        }
