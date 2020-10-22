from django import forms
from django.conf import settings
from django.contrib.auth import forms as auth_forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

import utils.forms
import zemauth.models.user.constants
import zemauth.models.user.exceptions
from utils import dates_helper
from utils.constant_base import ConstantBase


class YearsOfExperience(ConstantBase):
    ONE = 1
    TWO = 2
    THREE_PLUS = 3
    FIVE_PLUS = 5
    TEN_PLUS = 10
    FIFTEEN_PLUS = 15
    TWENTY_PLUS = 20

    _VALUES = {
        ONE: "1",
        TWO: "2",
        THREE_PLUS: "3+",
        FIVE_PLUS: "5+",
        TEN_PLUS: "10+",
        FIFTEEN_PLUS: "15+",
        TWENTY_PLUS: "20+",
    }


class AuthenticationForm(auth_forms.AuthenticationForm):
    username = forms.CharField(
        max_length=75, widget=forms.TextInput(attrs={"placeholder": "Email", "autofocus": "autofocus"})
    )
    password = forms.CharField(widget=forms.PasswordInput(attrs={"placeholder": "Password"}))


class PasswordResetForm(forms.Form):
    username = forms.EmailField(
        max_length=75,
        widget=forms.TextInput(attrs={"placeholder": "Email", "autofocus": "autofocus"}),
        error_messages={"required": "Invalid email address.", "invalid": "Invalid email address."},
    )

    def clean_username(self):
        form_username = self.cleaned_data.get("username")

        if (
            form_username.form_username.endswith("@zemanta.com")
            or form_username.form_username.endswith("@outbrain.com")
        ) and "+" not in form_username.form_username:
            raise ValidationError(
                'For security reasons, you must login using Google authentication. Please return to the sign in page, enter your Zemanta email address, and click "Sign in with Google".',
                code="invalid",
            )

        return form_username


class SetPasswordForm(forms.Form):
    new_password = forms.CharField(
        min_length=settings.PASSWORD_MIN_LENGTH, widget=forms.PasswordInput(attrs={"placeholder": "Password"})
    )
    email = forms.EmailField(widget=forms.HiddenInput())  # needed for FullStory

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(SetPasswordForm, self).__init__(initial={"email": user.email}, *args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        self._clean_new_password(cleaned_data)
        return cleaned_data

    def save(self):
        self.user.set_password(self.cleaned_data["new_password"])
        self.user.save()
        return self.user

    def _clean_new_password(self, cleaned_data):
        value = cleaned_data.get("new_password")
        validate_password(value, user=self.user)


class SetNewUserForm(SetPasswordForm):
    first_name = forms.CharField(
        max_length=30, widget=forms.TextInput(attrs={"placeholder": "First name", "autofocus": "autofocus"})
    )
    last_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={"placeholder": "Last name"}))
    country = utils.forms.EmptyChoiceField(
        choices=zemauth.models.user.constants.Country.get_choices(), empty_label="Select country"
    )
    company_type = utils.forms.IntegerEmptyChoiceField(
        choices=zemauth.models.user.constants.CompanyType.get_choices(), empty_label="Select company type"
    )
    job_title = forms.CharField(max_length=256, widget=forms.TextInput(attrs={"placeholder": "Job title"}))
    years_of_experience = utils.forms.IntegerEmptyChoiceField(
        choices=YearsOfExperience.get_choices(), empty_label="Years of experience"
    )
    programmatic_platforms = utils.forms.IntegerMultipleChoiceField(
        choices=zemauth.models.user.constants.ProgrammaticPlatform.get_choices(),
        widget=forms.CheckboxSelectMultiple(),
        required=False,
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        self._clean_years_of_experience(cleaned_data)
        return cleaned_data

    def save(self):
        self.user.set_password(self.cleaned_data["new_password"])
        self.user.update(**self.cleaned_data, status=zemauth.models.user.constants.Status.ACTIVE)
        return self.user

    @staticmethod
    def _clean_years_of_experience(cleaned_data):
        years_of_experience = cleaned_data.get("years_of_experience")
        cleaned_data["start_year_of_experience"] = dates_helper.local_today().year - years_of_experience
