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
from pattern import web    # for twitter search

@login_required
def recent_queries(request):
    return render_to_response("query/recent_queries.html",
        {'queries': Query.objects.all(),
         'status_choices' : dict(Query.STATUS_CHOICES)},
        RequestContext(request))

@login_required
def query_index(request):
    return render_to_response('query/query_index.html',
            {'query_list': Query.objects.filter(created_by=request.user),
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
    delay = 1 # Disable the timer for testing purposes.
    engine = web.Twitter(throttle=delay, language='en')
    # If twitter is not responding, lay off and try again in 10 minutes.
    # Otherwise, fail for this candidate.
    try: tweets = engine.search(query, start=1, count=query_count) # 100 tweets per query.
    except Exception, e:
        time.sleep(5)
        try: tweets = engine.search(query, start=1, count=query_count)
        except Exception, ex:
            app.logger.error("error" + web.bytestring(query))
            log_exception("Exception during twitter search")
            tweets = []
    return tweets

def clean_tweet(tweet):
    txt1 = web.plaintext(tweet)
    txt1 = txt1.replace("#", "# ").replace("  ", " ") # Clean twitter hashtags
    txt1 = txt1.replace("\n", " ").replace("  ", " ")
    txt1 = txt1.replace("\t", " ").replace("  ", " ")
    return txt1

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
