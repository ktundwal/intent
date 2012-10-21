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
import tweepy

import gviz_api

CRUXLY_API_TIMEOUT = 120
TWEETS_PER_API = 100

if settings.ENVIRONMENT == 'mbp':
    CRUXLY_SERVER = 'localhost:8080/api'
else:
    CRUXLY_SERVER = 'api.cruxly.com'

CRUXLY_API = 'http://' + CRUXLY_SERVER + '/rest/v1/analyze'

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

# == Twitter OAuth Authentication ==
#
# This mode of authentication is the new preferred way
# of authenticating with Twitter.

# The consumer keys can be found on your application's Details
# page located at https://dev.twitter.com/apps (under "OAuth settings")
consumer_key="0pupnggdsjb0cNPMpMZpVA"
consumer_secret="LIp2Im85LQbs8r2kqQdhiD884IrxQ5N1dfLlB6ULPQ"

# The access tokens can be found on your applications's Details
# page located at https://dev.twitter.com/apps (located
# under "Your access token")
access_token="151766004-h72B7fDOTWNHqlJCnTYaQxBs1bdyE588cBXc1qWV"
access_token_secret="bXMb8uvG9e9ZBtBQnbA3HUKpVk5PI3cXa6K6kT7JQ"

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

def search_twitter_using_tweepy(query):
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    return api.search(
        q=query,
        rpp=100,
        result_type="recent",
        include_entities=True,
        lang="en")

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
    all_tweets = search_twitter_using_tweepy(query_from_kip)
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

def get_verticaltracker_gvizjson(tracker):
    products = tracker.trackers.all()       # product = Kindle, KindleFire, Kindle Fire HD

    tracker_product_list_of_tuple = [("date", "string")]  # [("date","string"),("kindle","number"),("ipad","number")]
    for product in products:
        tracker_product_list_of_tuple.append((product.query, "number"))

    tracker_buy_list_of_tuple = []          # [("Sept 29",10,20),("Sept 30", 30, 35),("Oct 1", 15, 10)]
    tracker_like_list_of_tuple = []
    tracker_dislike_list_of_tuple = []

    product_daily_buy_stats_list = []
    product_daily_like_stats_list = []
    product_daily_dislike_stats_list = []

    first_dailystat = True

    first_product = products[0]
    first_product_dailystats = first_product.dailystats.all()

    for first_product_dailystat in first_product_dailystats:

        daily_buy_list = [first_product_dailystat.stat_for.strftime('%h %d %Y')]
        daily_like_list = [first_product_dailystat.stat_for.strftime('%h %d %Y')]
        daily_dislike_list = [first_product_dailystat.stat_for.strftime('%h %d %Y')]

        daily_buy_list.append(first_product_dailystat.buy_percentage())
        daily_like_list.append(first_product_dailystat.like_percentage())
        daily_dislike_list.append(first_product_dailystat.dislike_percentage())

        other_products_dailystat = DailyStat.objects\
                                        .filter(stat_of__in=products)\
                                        .exclude(stat_of=first_product)\
                                        .filter(stat_for=first_product_dailystat.stat_for)

        for other_product_dailystat in other_products_dailystat:

            daily_buy_list.append(other_product_dailystat.buy_percentage())
            daily_like_list.append(other_product_dailystat.like_percentage())
            daily_dislike_list.append(other_product_dailystat.dislike_percentage())

        tracker_buy_list_of_tuple.append(tuple(daily_buy_list))
        tracker_like_list_of_tuple.append(tuple(daily_like_list))
        tracker_dislike_list_of_tuple.append(tuple(daily_dislike_list))

#    for product in products:
#
#        product_dailystats = product.dailystats.all()
#
#        tracker_product_list_of_tuple.append((product.query, "number"))
#
#        for product_dailystat in product_dailystats:
#            if first_dailystat:
#                product_daily_buy_stats_list.append(product_dailystat.stat_for.strftime('%h %d %Y'))    # date
#                product_daily_like_stats_list.append(product_dailystat.stat_for.strftime('%h %d %Y'))    # date
#                product_daily_dislike_stats_list.append(product_dailystat.stat_for.strftime('%h %d %Y'))    # date
#                first_dailystat = False
#
#            product_daily_buy_stats_list.append(product_dailystat.buy_percentage())    # add buy %
#            product_daily_like_stats_list.append(product_dailystat.like_percentage())    # add like %
#            product_daily_dislike_stats_list.append(product_dailystat.dislike_percentage())    # add dislike %
#
#    tracker_buy_list_of_tuple.append(tuple(product_daily_buy_stats_list))
#    tracker_like_list_of_tuple.append(tuple(product_daily_like_stats_list))
#    tracker_dislike_list_of_tuple.append(tuple(product_daily_dislike_stats_list))


    #create a DataTable object
    buy_table = gviz_api.DataTable(tracker_product_list_of_tuple)
    buy_table.LoadData(tracker_buy_list_of_tuple)
    buy_json_str = buy_table.ToJSon() #convert to JSON
    #create a DataTable object
    like_table = gviz_api.DataTable(tracker_product_list_of_tuple)
    like_table.LoadData(tracker_like_list_of_tuple)
    like_json_str = like_table.ToJSon()   #convert to JSON
    #create a DataTable object
    dislike_table = gviz_api.DataTable(tracker_product_list_of_tuple)
    dislike_table.LoadData(tracker_dislike_list_of_tuple)
    dislike_json_str = dislike_table.ToJSon()   #convert to JSON

    intent_gviz_json = {
        'id': tracker.id,
        'name': tracker.name,
        'buy': buy_json_str,
        'like': like_json_str,
        'dislike': dislike_json_str, }
    return intent_gviz_json