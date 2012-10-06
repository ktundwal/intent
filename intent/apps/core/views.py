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

from intent.apps.query import gviz_api


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
            products = tracker.trackers.all()       # product = Kindle, KindleFire, Kindle Fire HD

            tracker_product_list_of_tuple = [("date", "string")]  # [("date","string"),("kindle","number"),("ipad","number")]
            tracker_buy_list_of_tuple = []          # [("Sept 29",10,20),("Sept 30", 30, 35),("Oct 1", 15, 10)]
            tracker_like_list_of_tuple = []
            tracker_dislike_list_of_tuple = []

            for product in products:
                product_dailystats = product.dailystats.all()

                tracker_product_list_of_tuple.append((product.query, "number"))

                product_daily_buy_stats_list = []
                product_daily_like_stats_list = []
                product_daily_dislike_stats_list = []

                first_dailystat = True
                for product_dailystat in product_dailystats:
                    if first_dailystat:

                        product_daily_buy_stats_list.append(product_dailystat.stat_for.strftime('%h %d %Y'))    # date
                        product_daily_like_stats_list.append(product_dailystat.stat_for.strftime('%h %d %Y'))    # date
                        product_daily_dislike_stats_list.append(product_dailystat.stat_for.strftime('%h %d %Y'))    # date
                        first_dailystat = False


                    product_daily_buy_stats_list.append(product_dailystat.buy_percentage())    # add buy %
                    product_daily_like_stats_list.append(product_dailystat.like_percentage())    # add like %
                    product_daily_dislike_stats_list.append(product_dailystat.dislike_percentage())    # add dislike %

                tracker_buy_list_of_tuple.append(tuple(product_daily_buy_stats_list))
                tracker_like_list_of_tuple.append(tuple(product_daily_like_stats_list))
                tracker_dislike_list_of_tuple.append(tuple(product_daily_dislike_stats_list))


            #create a DataTable object
            buy_table = gviz_api.DataTable(tracker_product_list_of_tuple)
            buy_table.LoadData(tracker_buy_list_of_tuple)
            buy_json_str=buy_table.ToJSon() #convert to JSON

            #create a DataTable object
            like_table = gviz_api.DataTable(tracker_product_list_of_tuple)
            like_table.LoadData(tracker_like_list_of_tuple)
            like_json_str=like_table.ToJSon()   #convert to JSON

            #create a DataTable object
            dislike_table = gviz_api.DataTable(tracker_product_list_of_tuple)
            dislike_table.LoadData(tracker_dislike_list_of_tuple)
            dislike_json_str=dislike_table.ToJSon()   #convert to JSON

            trackers_chartdata_list.append({
                'id' : tracker.id,
                'name' : tracker.name,
                'buy': buy_json_str,
                'like': like_json_str,
                'dislike': dislike_json_str,
            })

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