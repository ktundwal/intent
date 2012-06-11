#!/usr/bin/env python

"""forms.py: store additional information related to users
also see:
    http://birdhouse.org/blog/2009/06/27/django-profiles/
    https://docs.djangoproject.com/en/dev/topics/auth/#storing-additional-information-about-users
"""

__author__      = 'ktundwal'
__copyright__   = "Copyright 2012, Indraworks"
__credits__     = ["Kapil Tundwal"]
__license__     = "Indraworks Confidential. All Rights Reserved."
__version__     = "0.5.0"
__maintainer__  = "Kapil Tundwal"
__email__       = "ktundwal@gmail.com"
__status__      = "Development"

from django import forms
from django.contrib.admin.widgets import AdminDateWidget
import datetime
from .models import *
from django.contrib.localflavor.us.forms import USPhoneNumberField

class ReminderForm(forms.ModelForm):

    patient_cell = USPhoneNumberField()
    reminders = MultiSelectFormField(choices=REMINDER_CHOICES)

    appointment_date = forms.DateField(required=True)
    appointment_date.widget.attrs = {'class':'datePicker', 'readonly':'true',}
    appointment_time = forms.TimeField(required=True, input_formats=['%I:%M %p'])
    appointment_time.widget.attrs = {'class':'timePicker'}

    def clean_my_field(self):
        if len(self.cleaned_data['reminder_choices_field']) == 0:
            raise forms.ValidationError('Select at least one option')
        return self.cleaned_data['reminder_choices_field']

    class Meta:
        model = Reminder
        exclude = ['created_by']
