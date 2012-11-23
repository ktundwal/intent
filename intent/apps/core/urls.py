from django.conf.urls import patterns, url


urlpatterns = patterns('',
    url(r'^$', 'intent.apps.core.views.home', name='home'),
    url(r'^login/$', 'django.contrib.auth.views.login',
        {'template_name': 'core/login.html'}, name='login'),
    url(r'^register/$', 'intent.apps.core.views.register', name='register'),
    url(r'^logout/$', 'intent.apps.core.views.logout_user', name='logout'),

    url(r'^plans/$', 'intent.apps.core.views.plans', name='plans'),
    url(r'^terms/$', 'intent.apps.core.views.terms', name='terms'),
    url(r'^technology/$', 'intent.apps.core.views.technology', name='technology'),
    url(r'^privacy/$', 'intent.apps.core.views.privacy', name='privacy'),
    url(r'^company/$', 'intent.apps.core.views.company', name='company'),
)
