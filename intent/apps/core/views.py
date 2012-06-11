from django.template.response import TemplateResponse
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from intent.apps.core.forms import UserCreationFormWithEmail
from django.core.mail import send_mail
from intent import settings

def home(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('query:recent-queries'))
    else:
        return TemplateResponse(request, 'core/home.html', {})


def register(request):
    if request.method == 'POST':
        form = UserCreationFormWithEmail(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Thank you for registering, you can now '
                                      'login.')
            send_invite_email(form.data['username'], form.data['email'])
            return HttpResponseRedirect(reverse('core:login'))
    else:
        form = UserCreationFormWithEmail()
    return TemplateResponse(request, 'core/register.html', {'form': form})


@login_required
def logout_user(request):
    logout(request)
    messages.success(request, 'You have successfully logged out.')
    return HttpResponseRedirect(reverse('core:home'))

def send_invite_email(recipient_name, recipient_email):
    '''
    helper that's used to send an e-mail to the manager when a new tweet has been submitted
    for review or if an existing tweet has been updated.
    It uses Django's send_mail() method, which sends e-mail by using the server
    and credentials in the settings files.
    '''
    subject = 'Thanks for signing up at Cruxly'
    body = ('Welcome ' + recipient_name + ', Please login at http://intent.herokuapp.com/login with your username and password. Do let us know if you run into a bug. Thx -Kapil @ Cruxly')
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [recipient_email])