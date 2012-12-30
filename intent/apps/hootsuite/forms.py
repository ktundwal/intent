from django.contrib.auth.models import User
from django.utils.safestring import mark_safe

__author__ = 'self'

from django.forms import Textarea
from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Div, HTML
from intent.apps.hootsuite.models import Stream


CHOICES=[('Lead generation','Lead generation'),
         ('Product Development','Product development'),
         ('Customer Support','Customer Support'),]

class StreamForm(forms.ModelForm):

    keywords = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class':'span7',
            'placeholder' : 'Keywords such as starbucks, coffee, mocha (comma separated)',
            'rows' : 3,
            }),
        #label=mark_safe('<label for="id_keywords" class="hs_title">Product or Brand (required)</label>'),
        label = '',
    )
    twitter_handles = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class':'span7',
            'placeholder' : 'Twitter handles owned by you, such as @starbucks (comma separated)',
            'rows' : 2,
            }),
        #label=mark_safe('<label for="id_exclude_twitter_handles" class="hs_title">Twitter handles to exclude (optional)</label>'),
        label = '',
    )

    name = forms.CharField(
        max_length=30,
        required=True,
        #label=mark_safe('<label for="id_username" class="hs_title">Username (required)</label>'),
        label = '',
        )
    email = forms.EmailField(
        required=True,
        widget=forms.TextInput(attrs={'placeholder': "johndoe@example.com"}),
        #label=mark_safe('<label for="id_email" class="hs_title">Email (required)</label>'),
        label = '',
    )

    # I Agree to the Cruxly <a href="{% url core:terms %}" target="_blank">Terms of Service</a> and <a href="{% url core:privacy %}
    accept_terms = forms.BooleanField(
        required=True,
        #widget=forms.CheckboxInput(attrs={'class':'hs_title'}),
        #label=mark_safe('<span class="hs_title">I agree to Cruxly <a href="/terms">Terms of Service</a> and <a href="/privacy">Privacy Policy</a></span>'),
        label='',
        error_messages={'required': 'You must agree to the terms to use service'},
    )

    class Meta:
        model = Stream
        fields = ('keywords', 'twitter_handles')

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_id = 'id-setupform'
        self.helper.form_class = "form-horizontal"
        self.helper.form_method = 'post'
        #self.helper.add_input(Submit('submit', 'Submit'))

        self.helper.layout = Layout(
            HTML("""<label for="id_keywords" class="hs_title">Product(s) or Brand (required)</label>"""),
            'keywords',
            HTML("""<label for="id_twitter_handles" class="hs_title">Twitter handles owned by you (optional)</label>"""),
            'twitter_handles',
            HTML("""<label for="id_name" class="hs_title">Name (required)</label>"""),
            'name',
            HTML("""<label for="id_email" class="hs_title">Email (required)</label>"""),
            'email',
            HTML("""<label for="id_accept_terms" class="hs_title">I agree to Cruxly <a href="/terms">Terms of Service</a> and <a href="/privacy">Privacy Policy</a></label>"""),
            'accept_terms',
            Div(
                Div(
                    Submit('submit', 'Submit', css_class='btn btn-success pull-right submit'),
                    css_class="navigation form-actions",
                ),
                css_class="step submit",
            ),
        )

        super(StreamForm, self).__init__(*args, **kwargs)

class StreamUpdateForm(forms.ModelForm):

    keywords = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class':'span7',
            'placeholder' : 'Keywords such as starbucks, coffee, mocha (comma separated)',
            'rows' : 3,
            }),
        #label=mark_safe('<label for="id_keywords" class="hs_title">Product or Brand (required)</label>'),
        label = '',
    )
    twitter_handles = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class':'span7',
            'placeholder' : 'Twitter handles owned by you, such as @starbucks (comma separated)',
            'rows' : 2,
            }),
        #label=mark_safe('<label for="id_exclude_twitter_handles" class="hs_title">Twitter handles to exclude (optional)</label>'),
        label = '',
    )

    class Meta:
        model = Stream
        fields = ('keywords', 'twitter_handles')

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_id = 'id-setupform'
        self.helper.form_method = 'post'
        #self.helper.add_input(Submit('submit', 'Submit'))

        self.helper.layout = Layout(
            HTML("""<label for="id_keywords" class="hs_title">Product(s) or Brand (required)</label>"""),
            'keywords',
            HTML("""<label for="id_twitter_handles" class="hs_title">Twitter handles owned by you (optional)</label>"""),
            'twitter_handles',
            Div(
                Div(
                    Submit('submit', 'Update', css_class='btn btn-large btn-success pull-right submit'),
                    css_class="navigation form-actions",
                ),
                css_class="step submit",
            ),
        )

        super(StreamUpdateForm, self).__init__(*args, **kwargs)

class UserInfoForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    class Meta:
        model = User
        fields = ('email',)


