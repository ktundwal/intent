#!/usr/bin/env python

"""models.py"""

__author__      = 'ktundwal'
__copyright__   = "Copyright 2012, Indraworks"
__credits__     = ["Kapil Tundwal"]
__license__     = "Indraworks Confidential. All Rights Reserved."
__version__     = "0.5.0"
__maintainer__  = "Kapil Tundwal"
__email__       = "ktundwal@gmail.com"
__status__      = "Development"

import unittest
import logging
from intent.apps.query.utils import *

log = logging.getLogger( "Intent.AnalysisTestCase" )

class AnalysisTestCase(unittest.TestCase):
    def testBasic(self):
        queries = ['omaha steaks', 'audi r8', 'kindle fire', 'imation cd', 'starbucks']
        for query in queries:
            start_time = time.time()
            tweets = search_twitter(query, 200)
            print '%d results returned for %s' % (len(tweets), query)
            for tweet in tweets:
                tweet['content'] = clean_tweet(tweet.description)
            if len(tweets) > 0:
                tweets = insert_intents(tweets, log)
                wants = len([tweet for tweet in tweets if 'want' in tweet['intents']]) * 100 / len(tweets) if len(tweets) > 0 else 1
                print '    wants = %d%% in %d seconds' % (wants, time.time() - start_time)
            else:
                print '    no tweets to analyze'

class TwitterSearchTestCase(unittest.TestCase):
    def testBasic(self):
        query = create_query("starbucks", "mocha, coffee, latte")
        tweets = search_twitter(query, 100)
        for tweet in tweets:
            print clean_tweet(tweet.description)

if __name__ == '__main__':
    logging.basicConfig( stream=sys.stderr )
    logging.getLogger( "SomeTest.testSomething" ).setLevel( logging.DEBUG )
    unittest.main()