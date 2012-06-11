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


from django.template import RequestContext

from django.template.response import TemplateResponse
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .forms import QueryForm
from .models import *

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
