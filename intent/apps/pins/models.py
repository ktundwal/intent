from django.db import models
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile

import urllib2


class Pin(models.Model):
    url = models.TextField()
    description = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return self.url

    def save(self, *args, **kwargs):
        super(Pin, self).save()

    class Meta:
        ordering = ['-id']
