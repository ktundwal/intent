from django.conf.urls import patterns, url

urlpatterns = patterns('intent.apps.pins.views',
    url(r'^$', 'recent_pins', name='recent-pins'),
    url(r'^new-pin/$', 'new_pin', name='new-pin'),
)
