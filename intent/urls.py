from django.conf.urls import patterns, include, url
from django.conf import settings
from django.views.generic.base import RedirectView
from django.views.generic.simple import direct_to_template

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

message = """
Hello, intent users! This is just a dummy response.
"""

urlpatterns = patterns('',
    #All Auth URLS
    (r'^accounts/', include('allauth.urls')),

    url(r'', include('intent.apps.core.urls', namespace='core')),

    url(r'^accounts/profile/', direct_to_template, { 'template' : 'profile.html' }),

    url(r'^query/', include('intent.apps.query.urls', namespace='query')),

    # url(r'^sentry/', include('sentry.urls')),
    # Examples:
    # url(r'^$', 'intent.views.home', name='home'),
    # url(r'^intent/', include('intent.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    url(r'^static/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.STATIC_ROOT}),

    url(r'^favicon\.ico$', RedirectView.as_view(url='/static/core/img/favicon.ico')),
)
