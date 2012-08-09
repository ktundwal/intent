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

from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404

from datetime import datetime
from django.template import RequestContext

from django.template.response import TemplateResponse
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required

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

@login_required
def recent_queries(request):
    return render_to_response("query/recent_queries.html",
        {'queries': Query.objects.all(),
         'status_choices' : dict(Query.STATUS_CHOICES)},
        RequestContext(request))

@login_required
def query_index(request):
    queries = []
    for query in Query.objects.filter(created_by=request.user):
        docs = Document.objects.filter(result_of=query)
        docs_count = docs.count() if docs.count() > 0 else 1
        queries.append({
            'query': query.query,
            'last_run': query.last_run,
            'status': query.status,
            'created_on': query.created_on,
            'total_tweets': docs.count(),
            'want_percentage': docs.filter(want_rule__isnull=False).count() * 100 / docs_count,
            'promise_percentage': docs.filter(promise_rule__isnull=False).count() * 100 / docs_count,
            'question_percentage': docs.filter(question_rule__isnull=False).count() * 100 / docs_count
        })
    return render_to_response('query/query_index.html',
            {'queries': queries,
             'status_choices' : dict(Query.STATUS_CHOICES)},
            context_instance=RequestContext(request))

@login_required
def new_query(request, query_id = None):
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
    context = {'form': form,}
    #return TemplateResponse(request, 'reminders/new_reminder.html', context)
    return render_to_response("query/new_query.html",
        context, context_instance=RequestContext(request))

@login_required
def download(request, query_id = None):
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
                    content = cleaned_tweet,    # 'content' key is what cruxly api looks for
                    author = tweet.author,
                    image = tweet.profile,
                    url = "".join(['http://twitter.com/', tweet.author, '/status/', tweet.tweet_id]),
                    date = pretty_date(get_timestamp_from_twitter_date(tweet.date)),
                )
                analyzed_tweet_dict_list.append(analyzed_tweet_dict)

            if len(analyzed_tweet_dict_list) > 0:
                analyzed_tweet_dict_list = insert_intents(analyzed_tweet_dict_list)

            wants = len([tweet for tweet in analyzed_tweet_dict_list if 'want' in tweet['intents']]) * 100 / len(analyzed_tweet_dict_list) if len(analyzed_tweet_dict_list) > 0 else 1
            questions = len([tweet for tweet in analyzed_tweet_dict_list if 'question' in tweet['intents']]) * 100 / len(analyzed_tweet_dict_list) if len(analyzed_tweet_dict_list) > 0 else 1
            promises = len([tweet for tweet in analyzed_tweet_dict_list if 'promise' in tweet['intents']]) * 100 / len(analyzed_tweet_dict_list) if len(analyzed_tweet_dict_list) > 0 else 1
            buys = len([tweet for tweet in analyzed_tweet_dict_list if 'buy' in tweet['intents']]) * 100 / len(analyzed_tweet_dict_list) if len(analyzed_tweet_dict_list) > 0 else 1
            likes = len([tweet for tweet in analyzed_tweet_dict_list if 'like' in tweet['intents']]) * 100 / len(analyzed_tweet_dict_list) if len(analyzed_tweet_dict_list) > 0 else 1
            tries = len([tweet for tweet in analyzed_tweet_dict_list if 'try' in tweet['intents']]) * 100 / len(analyzed_tweet_dict_list) if len(analyzed_tweet_dict_list) > 0 else 1
            logger.info('Demo Request: %s' % query)

            context = {
                    'form': QueryForm(),
                    'tweets': analyzed_tweet_dict_list,
                    'query': query,
                    'count': query_count,
                    'stats': {'wants' : wants, 'promises' : promises, 'questions' : questions, 'buys' : buys, 'likes' : likes, 'tries' : tries},
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
        run_and_analyze_queries()
        return HttpResponse(simplejson.dumps(
                {'result': 'success',
                 "time_taken": time.time() - start_time
                }), mimetype='application/json')
    except Exception, e:
        return HttpResponse(simplejson.dumps(
                {'result': 'error',
                 'reason': e.message,
                 "time_taken": time.time() - start_time
                }), mimetype='application/json')