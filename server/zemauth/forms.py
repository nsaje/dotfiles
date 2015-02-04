from django import forms
from django.contrib.auth import forms as auth_forms
from django.core.exceptions import ValidationError

from zemauth import models


class AuthenticationForm(auth_forms.AuthenticationForm):
    username = forms.CharField(
        max_length=75,
        widget=forms.TextInput(attrs={'placeholder': 'Email', 'autofocus': 'autofocus'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))


class PasswordResetForm(forms.Form):
    username = forms.EmailField(
        max_length=75,
        widget=forms.TextInput(attrs={'placeholder': 'Email', 'autofocus': 'autofocus'}),
        error_messages={
            'required': 'Invalid email address.',
            'invalid': 'Invalid email address.'
        })

    def clean_username(self):
        form_username = self.cleaned_data.get('username')

        if form_username.endswith('@zemanta.com'):
            raise ValidationError(
                'For security reasons, you must login using Google authentication. Please return to the sign in page, enter your Zemanta email address, and click "Login with Google".',
                code='invalid'
            )

        if not models.User.objects.filter(email__iexact=form_username).exists():
            raise ValidationError('We can\'t find an account registered with that address.', code='invalid')

        return form_username


class SetPasswordForm(forms.Form):
    new_password = forms.CharField(min_length=6, widget=forms.PasswordInput)
    email = forms.EmailField(widget=forms.HiddenInput())  # needed for FullStory

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(SetPasswordForm, self).__init__(initial={'email': user.email}, *args, **kwargs)

    def save(self, commit=True):
        self.user.set_password(self.cleaned_data['new_password'])
        if commit:
            self.user.save()
        return self.user
