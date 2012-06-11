#!/usr/bin/env python

"""models.py"""

__author__      = 'ktundwal'
__copyright__   = "Copyright 2012, Indraworks"
__credits__     = ["Kapil Tundwal"]
__license__     = "Indraworks Confidential. All Rights Reserved."
__version__     = "0.5.0"
__maintainer__  = "Kapil Tundwal"
__email__       = "ktundwal@gmail.com"
__status__      = "Development"

from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404


from django.template import RequestContext

from django.template.response import TemplateResponse
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .forms import ReminderForm
from .models import *

@login_required
def recent_reminders(request):
    #return TemplateResponse(request, 'reminders/recent_reminders.html', {'reminders': Reminder.objects.all()})
    return render_to_response("reminders/recent_reminders.html",
        {'reminders': Reminder.objects.all(),},
        RequestContext(request))

@login_required
def reminders_index(request):
    x = dict(REMINDER_CHOICES)
    return render_to_response('reminders/reminder_index.html',
            {'reminder_list': Reminder.objects.filter(created_by=request.user),
             'reminder_choices' : dict(REMINDER_CHOICES)},
            context_instance=RequestContext(request))

@login_required
def new_reminder(request, reminder_id = None):
    reminder = None
    if reminder_id:
        reminder = get_object_or_404(Reminder, id=reminder_id)

    if request.method == 'POST':
        form = ReminderForm(data=request.POST, instance=reminder)
        if form.is_valid():
            reminder = form.save(commit=False) # returns unsaved instance
            reminder.created_by = request.user
            reminder.save() # real save to DB.
            messages.success(request, 'New reminder successfully added.')
            return HttpResponseRedirect(reverse('reminders:recent-reminders'))
        else:
            messages.error(request, 'Reminder did not pass validation!')
    else:
        form = ReminderForm(instance=reminder)
    context = {'form': form,}
    #return TemplateResponse(request, 'reminders/new_reminder.html', context)
    return render_to_response("reminders/new_reminder.html",
        context, context_instance=RequestContext(request))
