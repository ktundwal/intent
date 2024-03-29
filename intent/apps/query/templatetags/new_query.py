from django.template.loader import render_to_string
from django.template import Library
from django.template import RequestContext
from django.shortcuts import render_to_response

from intent.apps.query.forms import QueryForm, VerticalTrackerForm

# set up Django's template tag registry
register = Library()

@register.simple_tag()
def new_query():
    return render_to_string('query/templatetags/new_query.html', {'form': QueryForm()})
    #context = {'form': ReminderForm()}
    #return render_to_response("reminders/templatetags/new_reminder.html",
    #    context, context_instance=RequestContext(request))

@register.simple_tag()
def new_verticaltracker():
    return render_to_string('query/templatetags/new_verticaltracker.html', {'form': VerticalTrackerForm()})
    #context = {'form': ReminderForm()}
    #return render_to_response("reminders/templatetags/new_reminder.html",
    #    context, context_instance=RequestContext(request))