from django.contrib import admin
from .models import *

admin.site.register(Query)
admin.site.register(Document)
admin.site.register(Rule)