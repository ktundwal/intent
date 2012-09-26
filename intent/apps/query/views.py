#!/usr/bin/env python

"""models.py"""

__author__ = 'ktundwal'
__copyright__ = "Copyright 2012, Indraworks"
__credits__ = ["Kapil Tundwal"]
__license__ = "Indraworks Confidential. All Rights Reserved."
__version__ = "0.5.0"
__maintainer__ = "Kapil Tundwal"
__email__ = "ktundwal@gmail.com"
__status__ = "Development"

from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404

from datetime import datetime
from django.template import RequestContext

from django.template.response import TemplateResponse
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.db.models import Count

from io import BytesIO
from django.http import HttpResponse
from django.http import Http404

from .forms import QueryForm
from .models import *
from .utils import *
from .tasks import *
from django.utils import simplejson

from intent.apps.core.utils import *

from pattern import web    # for twitter search
from pattern.text.en import wordnet, parse, tag, Text, sentiment, modality, mood    # for sentence breaking

from endless_pagination.decorators import page_template

@login_required
def recent_queries(request):
    return render_to_response("query/recent_queries.html",
            {'queries': Query.objects.all(),
             'status_choices': dict(Query.STATUS_CHOICES)},
        RequestContext(request))


@login_required
def query_index(request):
    queries = []

    if request.user.is_superuser:
        queries = Query.objects.all()
    else:
        queries = Query.objects.filter(created_by=request.user)

    return render_to_response('query/query_index.html',
            {'queries': queries,
             'status_choices': dict(Query.STATUS_CHOICES)},
        context_instance=RequestContext(request))


def filter_tweets_for_intent(docs, intent):
    if intent == 'buy':
        return {
            'tweets': docs.filter(buy_rule__isnull=False),
        }
    elif intent == 'recommendation':
        return {
            'tweets': docs.filter(recommendation_rule__isnull=False),
            }
    elif intent == 'question':
        return {
            'tweets': docs.filter(question_rule__isnull=False),
            }
    elif intent == 'commitment':
        return {
            'tweets': docs.filter(commitment_rule__isnull=False),
            }
    elif intent == 'like':
        return {
            'tweets': docs.filter(like_rule__isnull=False),
            }
    elif intent == 'dislike':
        return {
            'tweets': docs.filter(dislike_rule__isnull=False),
            }
    elif intent == 'try':
        return {
            'tweets': docs.filter(try_rule__isnull=False),
            }

@login_required
@page_template('query/query_results_item.html')
def query_results(request,
                  query_id=None,
                  extra_context=None,
                  template='query/query_results.html',
                  ):
    query = None
    if query_id:
        query = get_object_or_404(Query, id=query_id)
    else:
        django.contrib.messages.error(request, 'Application error. Need a query id! Please try again.')

    context = {}

    if request.method == 'GET' and query:
        try:
            intent = request.GET.get('intent', 'buy')   #default to buy
            tweets = Document.objects.filter(result_of=query)

            context = {
                'query': query,
                'status_choices': dict(Query.STATUS_CHOICES),
                'intent': intent,
                }

            context.update(filter_tweets_for_intent(tweets, intent))

            if extra_context is not None:
                context.update(extra_context)

        except:
            log_exception(message='Error processing query id %d' % query_id)
            django.contrib.messages.error(request, 'Application error. Please try again.')
    else:
        django.contrib.messages.error(request, 'Application error. Only GET requests are supported! Please try again.')

    try:
        response = render_to_response(template, context, context_instance=RequestContext(request))
    except Exception, ex:
        django.contrib.messages.error(request, 'Pagination error. Please try again.')
        response = render_to_response(template, context, context_instance=RequestContext(request))
    return response


@login_required
def new_query(request, query_id=None):
    query = None
    #message = None
    if query_id:
        query = get_object_or_404(Query, id=query_id)

    if request.method == 'POST':
        form = QueryForm(data=request.POST, instance=query)
        if form.is_valid():
            query = form.save(commit=False) # returns unsaved instance
            query.created_by = request.user
            query.save() # real save to DB.
            #django.contrib.messages.success(request, 'New query successfully added.') FIXME
            return HttpResponseRedirect(reverse('query:recent-queries'))
        else:
            django.contrib.messages.error(request, 'Query did not pass validation!')
            #message = UserMessage("Validation error", "Query did not pass validation!")
    else:
        form = QueryForm(instance=query)
    context = {'form': form}
    #return TemplateResponse(request, 'reminders/new_reminder.html', context)
    return render_to_response("query/new_query.html",
        context, context_instance=RequestContext(request))


@login_required
def download(request, query_id=None):
    query = None
    if query_id:
        query = get_object_or_404(Query, id=query_id)

    if request.method == 'GET' and query:
        # Create the HttpResponse object with the appropriate PDF headers.
        response = HttpResponse(mimetype='plain/text')
        filename = "tweets-%s-unanalyzed-%s.%s" % (query.query, datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f"), 'txt')
        response['Content-Disposition'] = 'attachment; filename=' + filename

        delay = 1 # Disable the timer for testing purposes.
        query_count = 100
        engine = web.Twitter(throttle=delay, language='en')
        tweets = engine.search(query.query, start=1, count=query_count) # 100 tweets per query.
        for tweet in tweets:
            response.write('%s\n' % clean_tweet(tweet.description))
        return response
    else:
        raise Http404

SAMPLE_KEYWORD = "starbucks"
DEFAULT_QUERY_COUNT = '50'

def demo(request):
    """Analyze text"""

    context = {}
    error = ''
    query = None
    kip = None

    if request.method == 'GET':
        key_term = request.GET.get('k')
        industry_terms_comma_separated = request.GET.get('i', None)
        query_count = int(request.GET.get('count', DEFAULT_QUERY_COUNT))

    try:
        tweets = run_and_analyze_query(key_term, industry_terms_comma_separated, 100, logger)

#        logger.debug('Going to run twitter search for %s' % " OR ".join(kip))
#        search_results = search_twitter(" OR ".join(kip), query_count)
#
#        tweets = []
#        for tweet in search_results:
#            cleaned_tweet = clean_tweet(tweet.description)
#            #cleaned_tweet = Text(parse(clean_tweet(tweet.desciption))).string
#            analyzed_tweet_dict = dict(
#                content=cleaned_tweet, # 'content' key is what cruxly api looks for
#                author=tweet.author,
#                image=tweet.profile,
#                kip = kip,
#                url="".join(['http://twitter.com/', tweet.author, '/status/', tweet.tweet_id]),
#                date=pretty_date(get_timestamp_from_twitter_date(tweet.date)),
#            )
#            tweets.append(analyzed_tweet_dict)
#
#        if len(tweets) > 0:
#            tweets = insert_intents(tweets, logger)

        tweets_w_dislike           = [tweet for tweet in tweets if {u'intent': u'dislike'}          in tweet['intents']]
        tweets_w_question          = [tweet for tweet in tweets if {u'intent': u'question'}         in tweet['intents']]
        tweets_w_recommendation    = [tweet for tweet in tweets if {u'intent': u'recommendation'}   in tweet['intents']]
        tweets_w_buy               = [tweet for tweet in tweets if {u'intent': u'buy'}              in tweet['intents']]
        tweets_w_commitment        = [tweet for tweet in tweets if {u'intent': u'commitment'}       in tweet['intents']]
        tweets_w_try               = [tweet for tweet in tweets if {u'intent': u'try'}              in tweet['intents']]
        tweets_w_like              = [tweet for tweet in tweets if {u'intent': u'like'}             in tweet['intents']]

        question_percentage        = len(tweets_w_question) * 100 / len(tweets) if len(tweets) > 0 else 1
        recommendation_percentage  = len(tweets_w_recommendation) * 100 / len(tweets) if len(tweets) > 0 else 1
        buy_percentage             = len(tweets_w_buy) * 100 / len(tweets) if len(tweets) > 0 else 1
        commitment_percentage      = len(tweets_w_commitment) * 100 / len(tweets) if len(tweets) > 0 else 1
        try_percentage             = len(tweets_w_try) * 100 / len(tweets) if len(tweets) > 0 else 1
        like_percentage            = len(tweets_w_like) * 100 / len(tweets) if len(tweets) > 0 else 1
        dislike_percentage         = len(tweets_w_dislike) * 100 / len(tweets) if len(tweets) > 0 else 1

        for tweet in tweets:
            intent_list = []
            for intent in tweet['intents']:
                intent_list.append(intent['intent'])
            tweet['comman_separated_intents'] = ", ".join(intent_list)

        logger.info('Demo Request: %s' % query)

        context = {
            'form': QueryForm(),
            'tweets': tweets,
            'query': query,
            'count': query_count,
            'stats': {'question':       question_percentage,
                      'recommendation': recommendation_percentage,
                      'commitment':     commitment_percentage,
                      'buy':            buy_percentage,
                      'like':           like_percentage,
                      'tries':          try_percentage,
                      'dislike':        dislike_percentage,},
            }

    except Exception, e:
        log_exception()
        context['error'] = 'Unexpected error! %s' % e.message

    return render_to_response("query/demo.html", context,
        context_instance=RequestContext(request))


def process(request):
    """run background process task once"""
    start_time = time.time()
    try:
        response = run_and_analyze_queries()
        return HttpResponse(content = simplejson.dumps(
                {'result': 'success' if response is None else 'failure: %s' % response,
                 "time_taken": time.time() - start_time
            }), mimetype='application/json', status=200)
    except Exception, e:
        return HttpResponse(content = simplejson.dumps(
                {'result': 'failure: %s' % e,
                 'reason': e.message,
                 "time_taken": time.time() - start_time
            }), mimetype='application/json', status=200)