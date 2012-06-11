from django.contrib import admin
from .models import *

admin.site.register(Query)
admin.site.register(RunningState)
admin.site.register(Intent)
admin.site.register(Tweet)