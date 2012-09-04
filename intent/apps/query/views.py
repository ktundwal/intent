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
from django.contrib import messages
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
    for query in Query.objects.filter(created_by=request.user):

        daily_stats = DailyStat.objects.filter(stat_of=query)

        buy_all_count = 0
        recommendation_all_count = 0
        question_all_count = 0
        commitment_all_count = 0
        like_all_count = 0
        dislike_all_count = 0
        try_all_count = 0

        for daily_stat in daily_stats:
            buy_all_count += daily_stat.buy_count
            recommendation_all_count += daily_stat.recommendation_count
            question_all_count += daily_stat.question_count
            commitment_all_count += daily_stat.commitment_count
            like_all_count += daily_stat.like_count
            dislike_all_count += daily_stat.dislike_count
            try_all_count += daily_stat.try_count

        queries.append({
            'query': query.query,
            'id': query.id,
            'last_run': query.last_run,
            'status': query.status,
            'created_on': query.created_on,
            'count': query.count,
            'daily_stats': daily_stats,
            'buy_percentage': buy_all_count * 100 / query.count,
            'recommendation_percentage': recommendation_all_count * 100 / query.count,
            'question_percentage': question_all_count * 100 / query.count,
            'commitment_percentage': commitment_all_count * 100 / query.count,
            'like_percentage': like_all_count * 100 / query.count,
            'dislike_percentage': dislike_all_count * 100 / query.count,
            'try_percentage': try_all_count * 100 / query.count,
        })
    return render_to_response('query/query_index.html',
            {'queries': queries,
             'status_choices': dict(Query.STATUS_CHOICES)},
        context_instance=RequestContext(request))


def build_context_from_intent(docs, docs_count, intent):
    if intent == 'buy':
        return {
            'tweets': docs.filter(buy_rule__isnull=False),
            'buy_percentage': docs.filter(buy_rule__isnull=False).count() * 100 / docs_count,
        }
    elif intent == 'recommendation':
        return {
            'tweets': docs.filter(recommendation_rule__isnull=False),
            'recommendation_percentage': docs.filter(recommendation_rule__isnull=False).count() * 100 / docs_count,
            }
    elif intent == 'question':
        return {
            'tweets': docs.filter(question_rule__isnull=False),
            'question_percentage': docs.filter(question_rule__isnull=False).count() * 100 / docs_count,
            }
    elif intent == 'commitment':
        return {
            'tweets': docs.filter(commitment_rule__isnull=False),
            'commitment_percentage': docs.filter(commitment_rule__isnull=False).count() * 100 / docs_count,
            }
    elif intent == 'like':
        return {
            'tweets': docs.filter(like_rule__isnull=False),
            'like_percentage': docs.filter(like_rule__isnull=False).count() * 100 / docs_count,
            }
    elif intent == 'dislike':
        return {
            'tweets': docs.filter(dislike_rule__isnull=False),
            'dislike_percentage': docs.filter(dislike_rule__isnull=False).count() * 100 / docs_count,
            }
    elif intent == 'try':
        return {
            'tweets': docs.filter(try_rule__isnull=False),
            'try_percentage': docs.filter(try_rule__isnull=False).count() * 100 / docs_count,
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
        messages.error(request, 'Application error. Need a query id! Please try again.')

    context = {}

    if request.method == 'GET' and query:
        try:
            intent = request.GET.get('intent', 'buy')   #default to buy
            docs = Document.objects.filter(result_of=query)
            docs_count = docs.count() if docs.count() > 0 else 1

            context = {
                'query': query,
                'last_run': query.last_run,
                'status': query.status,
                'created_on': query.created_on,
                'total_tweets': docs.count(),
                'status_choices': dict(Query.STATUS_CHOICES),
                'intent': intent,
                }

            context.update(build_context_from_intent(docs, docs_count, intent))

            if extra_context is not None:
                context.update(extra_context)

        except:
            log_exception(message='Error processing query id %d' % query_id)
            messages.error(request, 'Application error. Please try again.')
    else:
        messages.error(request, 'Application error. Only GET requests are supported! Please try again.')

    try:
        response = render_to_response(template, context, context_instance=RequestContext(request))
    except Exception, ex:
        messages.error(request, 'Pagination error. Please try again.')
        response = render_to_response(template, context, context_instance=RequestContext(request))
    return response


@login_required
def new_query(request, query_id=None):
    query = None
    if query_id:
        query = get_object_or_404(Query, id=query_id)

    if request.method == 'POST':
        form = QueryForm(data=request.POST, instance=query)
        if form.is_valid():
            query = form.save(commit=False) # returns unsaved instance
            query.created_by = request.user
            query.save() # real save to DB.
            messages.success(request, 'New query successfully added.')
            return HttpResponseRedirect(reverse('query:recent-queries'))
        else:
            messages.error(request, 'Query did not pass validation!')
    else:
        form = QueryForm(instance=query)
    context = {'form': form, }
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
DEFAULT_QUERY_COUNT = '200'

def demo(request):
    """Analyze text"""

    context = {}
    error = ''

    if request.method == 'GET':
        try: query = request.GET.get('q')
        except Exception: error = 'Invalid query'
        try: query_count = int(request.GET.get('count'))
        except Exception: query_count = int(DEFAULT_QUERY_COUNT)
    else:
        form = QueryForm(data=request.POST)
        if form.is_valid():
            query = form.save(commit=False) # returns unsaved instance
            query_count = int(DEFAULT_QUERY_COUNT)
        else:
            error = 'Invalid query'

    if not error:
        try:
            tweets = search_twitter(query, query_count)

            analyzed_tweet_dict_list = []
            for tweet in tweets:
                cleaned_tweet = clean_tweet(tweet.description)
                #cleaned_tweet = Text(parse(clean_tweet(tweet.desciption))).string
                analyzed_tweet_dict = dict(
                    content=cleaned_tweet, # 'content' key is what cruxly api looks for
                    author=tweet.author,
                    image=tweet.profile,
                    url="".join(['http://twitter.com/', tweet.author, '/status/', tweet.tweet_id]),
                    date=pretty_date(get_timestamp_from_twitter_date(tweet.date)),
                )
                analyzed_tweet_dict_list.append(analyzed_tweet_dict)

            if len(analyzed_tweet_dict_list) > 0:
                analyzed_tweet_dict_list = insert_intents(analyzed_tweet_dict_list)

            question = len([tweet for tweet in analyzed_tweet_dict_list if 'question' in tweet['intents']]) * 100 / len(
                analyzed_tweet_dict_list) if len(analyzed_tweet_dict_list) > 0 else 1
            recommendation = len(
                [tweet for tweet in analyzed_tweet_dict_list if 'recommendation' in tweet['intents']]) * 100 / len(
                analyzed_tweet_dict_list) if len(analyzed_tweet_dict_list) > 0 else 1
            commitment = len(
                [tweet for tweet in analyzed_tweet_dict_list if 'commitment' in tweet['intents']]) * 100 / len(
                analyzed_tweet_dict_list) if len(analyzed_tweet_dict_list) > 0 else 1
            buy = len([tweet for tweet in analyzed_tweet_dict_list if 'buy' in tweet['intents']]) * 100 / len(
                analyzed_tweet_dict_list) if len(analyzed_tweet_dict_list) > 0 else 1
            like = len([tweet for tweet in analyzed_tweet_dict_list if 'like' in tweet['intents']]) * 100 / len(
                analyzed_tweet_dict_list) if len(analyzed_tweet_dict_list) > 0 else 1
            tries = len([tweet for tweet in analyzed_tweet_dict_list if 'try' in tweet['intents']]) * 100 / len(
                analyzed_tweet_dict_list) if len(analyzed_tweet_dict_list) > 0 else 1
            logger.info('Demo Request: %s' % query)

            context = {
                'form': QueryForm(),
                'tweets': analyzed_tweet_dict_list,
                'query': query,
                'count': query_count,
                'stats': {'question': question,
                          'recommendation': recommendation,
                          'commitment': commitment,
                          'buy': buy,
                          'like': like,
                          'tries': tries},
                }

        except Exception, e:
            log_exception()
            context['error'] = 'Unexpected error! %s' % e.message
    else:
        context['error'] = error

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
            }), mimetype='application/json', status=500)