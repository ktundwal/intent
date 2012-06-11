from django.conf.urls import patterns, include, url
from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

message = """
Hello, intent users! This is just a dummy response.
"""

urlpatterns = patterns('',
    url(r'', include('intent.apps.core.urls', namespace='core')),
    url(r'^queries/', include('intent.apps.query.urls', namespace='query')),
    url(r'^reminders/', include('intent.apps.reminders.urls', namespace='reminders')),
    url(r'^pins/', include('intent.apps.pins.urls', namespace='pins')),
    url(r'^api/', include('intent.apps.api.urls', namespace='api')),

    # url(r'^sentry/', include('sentry.urls')),
    # Examples:
    # url(r'^$', 'intent.views.home', name='home'),
    # url(r'^intent/', include('intent.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    (r'^accounts/', include('registration.backends.default.urls')),

    url(r'^static/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.STATIC_ROOT}),
)
