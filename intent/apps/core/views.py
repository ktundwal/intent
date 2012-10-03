from django.template.response import TemplateResponse
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from intent.apps.core.forms import UserCreationFormWithEmail
from django.core.mail import send_mail
from intent import settings
from intent.apps.query.models import Document, Query, VerticalTracker
from django.db.models import Sum


def home(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('query:recent-queries'))
    else:
        #        Vertical tracker needs following
        #        var data = google.visualization.arrayToDataTable([
        #            ['Date',           Kindle',    'iPad', 'Nexus'],
        #            ['Sept 2, 2012',   10,         20,     30],
        #            ['Sept 3, 2012',   20,         22,     10],
        #        ]);
        #        list of lists

        trackers_chartdata_list = []
        trackers = VerticalTracker.objects.all()
        for tracker in trackers:
            tracker_chart_data = {}
            products = tracker.trackers.all()   # product = Kindle, KindleFire, Kindle Fire HD

            tracker_chartdata_buy_list = []     # row / date
            tracker_chartdata_like_list = []     # row / date
            tracker_chartdata_dislike_list = []     # row / date

            for product in products:
                product_dailystats = product.dailystats.all()

                first = True

                product_daily_buy_stats = []
                product_daily_like_stats = []
                product_daily_dislike_stats = []

                for product_dailystat in product_dailystats:
                    if first:
                        product_daily_buy_stats.append(product_dailystat.stat_of.query)    # product name
                        product_daily_like_stats.append(product_dailystat.stat_of.query)    # product name
                        product_daily_dislike_stats.append(product_dailystat.stat_of.query)    # product name
                        first = False

                    product_daily_buy_stats.append(product_dailystat.buy_percentage())    # add buy %
                    product_daily_like_stats.append(product_dailystat.like_percentage())    # add like %
                    product_daily_dislike_stats.append(product_dailystat.dislike_percentage())    # add dislike %

                tracker_chartdata_buy_list.append(product_daily_buy_stats)
                tracker_chartdata_like_list.append(product_daily_like_stats)
                tracker_chartdata_dislike_list.append(product_daily_dislike_stats)

            transposed_tracker_chartdata_buy_list = zip(*tracker_chartdata_buy_list)
            transposed_tracker_chartdata_like_list = zip(*tracker_chartdata_like_list)
            transposed_tracker_chartdata_dislike_list = zip(*tracker_chartdata_dislike_list)

            tracker_chart_data['buy'] = transposed_tracker_chartdata_buy_list;
            tracker_chart_data['like'] = transposed_tracker_chartdata_like_list;
            tracker_chart_data['dislike'] = transposed_tracker_chartdata_dislike_list;

            trackers_chartdata_list.append(tracker_chart_data)


        return TemplateResponse(request, 'core/home.html', {
            'vertical_trackers':trackers_chartdata_list,
            'total_documents_processed': Query.objects.all().aggregate(Sum('count'))['count__sum'],
            'buy_count': Query.objects.all().aggregate(Sum('buy_count'))['buy_count__sum']
        })

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
            send_invite_email(form.data['username'], form.data['email'])
            return HttpResponseRedirect(reverse('core:login'))
    else:
        form = UserCreationFormWithEmail()
    return TemplateResponse(request, 'core/register.html', {'form': form})

@login_required
def logout_user(request):
    logout(request)
    messages.success(request, 'You have successfully logged out.')
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