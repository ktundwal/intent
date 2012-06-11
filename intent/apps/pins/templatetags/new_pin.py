from django.template.loader import render_to_string
from django.template import Library

from intent.apps.pins.forms import PinForm


register = Library()


@register.simple_tag
def new_pin():
    return render_to_string('pins/templatetags/new_pin.html',
        {'form': PinForm()})
