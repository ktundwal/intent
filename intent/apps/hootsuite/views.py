#!/usr/bin/env python

"""views.py"""

__author__ = 'ktundwal'
__copyright__ = "Copyright 2012, Indraworks"
__credits__ = ["Kapil Tundwal"]
__license__ = "Indraworks Confidential. All Rights Reserved."
__version__ = "0.5.0"
__maintainer__ = "Kapil Tundwal"
__email__ = "ktundwal@gmail.com"
__status__ = "Development"

import time
import django
from endless_pagination.decorators import page_template
from intent.apps.core.utils import log_exception, logger
from intent.apps.hootsuite.tasks import run_and_analyze_queries
from django.template import RequestContext
from django.utils import simplejson

from django.http import HttpResponseRedirect, Http404, HttpResponse, HttpResponseBadRequest, HttpResponseServerError, HttpResponseNotAllowed
from django.core.urlresolvers import reverse
from django.views.generic.edit import FormView, ProcessFormView
from django.views.generic import TemplateView, UpdateView
from django.shortcuts import redirect, get_object_or_404, render_to_response
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from intent.apps.hootsuite.models import Stream, Document

from intent.apps.hootsuite.forms import StreamForm, StreamUpdateForm

def get_user_stream_config(request):
    try:
        return Stream.objects.filter(created_by = request.user).filter(hootsuite_pid = request.session['hootsuite_pid'])[0]
    except:
        return None


class WelcomeView(TemplateView):
    template_name = 'hs/welcome.html'

    def get(self, request, *args, **kwargs):
        # Do something with GET.
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        # Do something with the POST data.

        if not request.user.is_authenticated():
            return PermissionDenied

        context = self.get_context_data(**kwargs)
        context['stream'] = get_user_stream_config(request)
        return self.render_to_response(context)

class LoginView(TemplateView):
    template_name = 'hs/login.html'

    def get(self, request, *args, **kwargs):
        # Do something with GET.
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        # Do something with the POST data.
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


def build_hs_query_params(request):
    return 'pid=%s&uid=%s&theme=%s&lang=%s&i=%s' % (
        request.session['hootsuite_pid'],
        request.session['hootsuite_uid'],
        request.session['hootsuite_theme'],
        request.session['hootsuite_lang'],
        request.session['hootsuite_uid'],
        )


class StreamFormCreateView(FormView):
    template_name = 'hs/setup.html'
    form_class = StreamForm
    model = Stream

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        stream = form.save(commit=False) # returns unsaved instance
        stream.created_by = self.request.user
        stream.hootsuite_pid = self.request.session['hootsuite_pid']
        stream.status = Stream.WAITING_TO_RUN_STATUS
        stream.save() # real save to DB.

        user = self.request.user

        email = form.cleaned_data['email']
        if email:
            user.email = email

        first_name = form.cleaned_data['name']
        if first_name:
            user.first_name = first_name

        user.save()

        return super(StreamFormCreateView, self).form_valid(form)

    def get_success_url(self):
        return '/hootsuite/results/?%s' % build_hs_query_params(self.request)

class StreamFormUpdateView(UpdateView):
    template_name = 'hs/setup.html'
    form_class = StreamUpdateForm
    model = Stream

    def get_object(self, queryset=None):
        return get_user_stream_config(self.request)

    def get_success_url(self):
        return '/hootsuite/results/?%s' % build_hs_query_params(self.request)

class MainView(FormView):
    template_name = 'hs/stream.html'
    form_class = StreamForm
    #success_url = '/contact_success/'

    def post(self, request, *args, **kwargs):
        context = {}
        redirect_url = reverse("hootsuite:login")
        extra_params = '?overlay=2'
        full_redirect_url = '%s%s' % (redirect_url, extra_params)
        return HttpResponseRedirect( full_redirect_url )

    def form_valid(self, form):
    # This method is called when valid form data has been POSTed.
    # It should return an HttpResponse.
    #        message = "From: %s <%s>\r\nSubject:%s\r\nMessage:\r\n%s\r\n" % (
    #            form.cleaned_data['name'],
    #            form.cleaned_data['email'],
    #            form.cleaned_data['subject'],
    #            form.cleaned_data['message']
    #            )
    #        mail_admins('Contact form', message, fail_silently=False)

        if self.request.is_ajax():
            import time
            time.sleep(5) # delay AJAX response for 5 seconds
            #return render(self.request, self.template_name)
        else:
            #return redirect('index')
            pass

class StreamView(TemplateView):
    template_name = "hs/stream.html"

    def get_context_data(self, **kwargs):
        # This allows this View to be easily subclassed in the future to interchange context data.
        context = kwargs
        return context

    def dispatch(self, request, *args, **kwargs):
        # Do something fancy here.
        if not request.user.is_authenticated():
            #return HttpResponseRedirect(reverse("hootsuite:login"))
            return redirect("hootsuite:login",
                pid=request.POST.get('pid'),
                theme=request.POST.get('theme'),
                uid=request.POST.get('uid'),
                **kwargs)
        return super(StreamView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        # Do something with GET.
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        # Do something with the POST data.
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

class DeleteStreamView(ProcessFormView):
    """
    A mixin that processes a form on POST.
    """
    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed()

    def post(self, request, *args, **kwargs):
        try:
            stream_to_delete = Stream.objects.get(hootsuite_pid = request.POST['pid'])
            stream_to_delete.delete()
            logger.info('Successfully deleted stream with hootsuite pid = %s for user %s' % (request.POST['pid'], request.user))
        except django.core.exceptions.DoesNotExist:
            log_exception(message='Request to delete stream with hootsuite pid = %s. No stream found which matches this pid' % request.POST['pid'])
        except KeyError:
            log_exception(message='Request to delete stream with unknown hootsuite pid')
            return HttpResponseBadRequest()
        except:
            return HttpResponseServerError()
        return HttpResponse('success')

def tokenexchange(request):
    # Django converts Authorization header in HTTP_AUTHORIZATION
    # Warning: it doesn't happen in tests but it's useful, do not remove!
    auth_header = {}
    if 'Authorization' in request.META:
        auth_header = {'Authorization': request.META['Authorization']}
    elif 'HTTP_AUTHORIZATION' in request.META:
        auth_header =  {'HTTP_AUTHORIZATION': request.META['HTTP_AUTHORIZATION']}
        authmeth, auth = request.META['HTTP_AUTHORIZATION'].split(' ', 1)

        import requests

        r = requests.post('https://api.twitter.com/oauth/access_token', headers=auth_header)
        print 'access_token returned: ' + r.content

        r2 = requests.post('https://api.twitter.com/oauth/request_token', headers=auth_header)
        print 'request_token returned: ' + r2.content

        if authmeth.lower() == 'oauth':
            pass

    parameters = dict(request.REQUEST.items())
    return Http404

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

@page_template('hs/query_results_item.html')
def query_results(request,
                  extra_context=None,
                  template='hs/query_results.html',
                  ):
    query = get_user_stream_config(request)
    if not query:
        django.contrib.messages.error(request, 'Application error. Need a query id! Please try again.')

    context = {}

    if request.method == 'GET' and query:
        try:
            tweets = Document.objects.filter(result_of=query)

            context = {
                'query': query,
                'status_choices': dict(Stream.STATUS_CHOICES),
                'tweets': tweets,
                }

            if extra_context is not None:
                context.update(extra_context)

        except:
            log_exception(message='Error processing query id %d' % query.id)
            django.contrib.messages.error(request, 'Application error. Please try again.')
    else:
        django.contrib.messages.error(request, 'Application error. Only GET requests are supported! Please try again.')

    try:
        response = render_to_response(template, context, context_instance=RequestContext(request))
    except Exception, ex:
        django.contrib.messages.error(request, 'Pagination error. Please try again.')
        response = render_to_response(template, context, context_instance=RequestContext(request))
    return response
