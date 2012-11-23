from django.template.response import TemplateResponse
from django.http import HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

from intent.apps.core.forms import UserCreationFormWithEmail, PlanForm
from django.core.mail import send_mail
from intent import settings
from intent.apps.query.models import Document, Query, VerticalTracker
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from intent.apps.core.models import *
from django.views.generic.simple import direct_to_template
from django.shortcuts import render_to_response
from django.template import RequestContext

from intent.apps.query.utils import *

from django.contrib import messages


def home(request):
    if request.user.is_authenticated():
        try:
            user = get_object_or_404(UserProfile, user=request.user)
            user = None #FIXME
        except Http404, e:
            user = None
        if user:
            return direct_to_template(request, 'profile.html')
        else:
            return HttpResponseRedirect(reverse('query:query_index'))

    else:
        #        Vertical tracker needs following
        #        var data = google.visualization.arrayToDataTable([
        #            ['Date',           Kindle',    'iPad', 'Nexus'],
        #            ['Sept 2, 2012',   10,         20,     30],
        #            ['Sept 3, 2012',   20,         22,     10],
        #        ]);
        #        list of lists

#        trackers_chartdata_list = []
#
#        try:
#            tracker = VerticalTracker.objects.get(pk=1)
#            intent_gviz_json = get_verticaltracker_gvizjson(tracker)
#            trackers_chartdata_list.append(intent_gviz_json)
#        except Exception, e:
#            log_exception(message='Error collecting vertical data for home page')

        return TemplateResponse(request, 'core/home.html', {
#            'vertical_trackers':trackers_chartdata_list,
            'total_documents_processed': Query.objects.all().aggregate(Sum('count'))['count__sum'],
            'buy_count': Query.objects.all().aggregate(Sum('buy_count'))['buy_count__sum']
        })

def plans(request):
    # https://docs.djangoproject.com/en/dev/ref/forms/api/#prefixes-for-forms
    if request.method == 'POST':
        if 'gold' in request.POST:
            messages.success(request, "you selected Gold plan", fail_silently=True)
        elif 'silver' in request.POST:
            messages.success(request, "you selected Silver plan", fail_silently=True)
        elif 'bronze' in request.POST:
            messages.success(request, "you selected Bronze plan", fail_silently=True)
        elif 'trial' in request.POST:
            messages.success(request, "you selected trial plan", fail_silently=True)
        return direct_to_template(request, 'core/profile.html')
    else:
        return render_to_response('core/plans.html', {
            'gold_plan_form': PlanForm(),
            'silver_plan_form': PlanForm(),
            'bronze_plan_form': PlanForm(),
            'trial_plan_form': PlanForm(),
        }, context_instance=RequestContext(request)
        )

def terms(request):
    return TemplateResponse(request, 'core/terms.html', {})

def privacy(request):
    return TemplateResponse(request, 'core/privacy.html', {})

def technology(request):
    return TemplateResponse(request, 'core/technology.html', {})

def company(request):
    return TemplateResponse(request, 'core/company.html', {})

def register(request):
    if request.method == 'POST':
        form = UserCreationFormWithEmail(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Thank you for registering, you can now '
                                      'login.')
            try:
                send_invite_email(form.data['username'], form.data['email'])
            except:
                pass
            return HttpResponseRedirect(reverse('core:login'))
    else:
        form = UserCreationFormWithEmail()
    return TemplateResponse(request, 'core/register.html', {'form': form})

@login_required
def logout_user(request):
    logout(request)
    #messages.success(request, 'You have successfully logged out.')
    return HttpResponseRedirect(reverse('core:home'))

def send_invite_email(recipient_name, recipient_email):
    '''
    helper that's used to send an e-mail to the manager when a new tweet has been submitted
    for review or if an existing tweet has been updated.
    It uses Django's send_mail() method, which sends e-mail by using the server
    and credentials in the settings files.
    '''
    subject = 'Thanks for signing up at Cruxly'
    body = ('Welcome ' + recipient_name + ', Please login at http://www.cruxly.com/login with your username and password. Do let us know if you run into a bug. Thx -Aloke @ Cruxly')
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [recipient_email])