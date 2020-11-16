import urllib.error
import urllib.parse
import urllib.request

import ipware.ip
from django.conf import settings
from django.contrib import auth
from django.contrib.auth import tokens as auth_tokens
from django.contrib.auth import views as auth_views
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.shortcuts import resolve_url
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.http import is_safe_url
from django.utils.http import urlsafe_base64_decode
from ratelimit.decorators import ratelimit
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

import utils.rest_common.authentication
from utils import email_helper
from utils import metrics_compat
from utils import recaptcha_helper
from zemauth import devices
from zemauth import forms
from zemauth.models import User

from . import gauth
from . import serializers


class UserView(APIView):
    authentication_classes = [
        utils.rest_common.authentication.OAuth2Authentication,
        utils.rest_common.authentication.SessionAuthentication,
    ]
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        return Response(serializers.UserSerializer(request.user).data)


@metrics_compat.timer("auth.signin_response_time")
@ratelimit(key=lambda g, r: ipware.ip.get_ip(r), rate="20/m", method="POST")
def login(request, *args, **kwargs):
    """
    Wraps login view and injects certain query string values into
    extra_context and passes it to django.contrib.auth.views.login.
    """

    if "error" in request.GET:
        return _fail_response()

    if "extra_context" not in kwargs:
        kwargs["extra_context"] = {}

    if request.limited:
        form = forms.AuthenticationForm(request, data=request.POST)
        return TemplateResponse(
            request,
            kwargs["template_name"],
            {"form": form, "ratelimited_error": "Too many login attempts. Please try again in a few minutes."},
        )

    kwargs["extra_context"]["gauth_error"] = request.GET.get("gauth_error")

    if settings.GOOGLE_OAUTH_ENABLED:
        kwargs["extra_context"]["gauth_url"] = gauth.get_uri(request)

    kwargs["success_url_allowed_hosts"] = settings.ALLOWED_REDIRECT_HOSTS
    response = auth_views.LoginView.as_view(**kwargs)(request, *args, **kwargs)
    if request.method == "POST":
        devices.handle_user_device(request, response)

    return response


def password_reset(request, template_name=None):
    form = forms.PasswordResetForm()
    success = False

    if request.method == "POST":
        form = forms.PasswordResetForm(request.POST)

        if form.is_valid() and recaptcha_helper.check_recaptcha(request):
            success = True

            try:
                user = User.objects.get(email__iexact=form.cleaned_data["username"])
                next_param = request.GET.get("next", "")
                safe_next_param = next_param if is_safe_url(next_param, settings.ALLOWED_REDIRECT_HOSTS, True) else ""
                email_helper.send_password_reset_email(user, request, safe_next_param)
            except User.DoesNotExist:
                pass

    context = {"form": form, "success": success}
    return TemplateResponse(request, template_name, context)


def set_password(request, uidb64=None, token=None, template_name=None):
    assert uidb64 is not None and token is not None  # checked by URLconf

    try:
        uid = urlsafe_base64_decode(uidb64)
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and auth_tokens.default_token_generator.check_token(user, token):
        valid_link = True
        if request.method == "POST":
            form = forms.SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()

                if not any(user.email.endswith(postfix) for postfix in settings.INTERNAL_EMAIL_POSTFIXES):
                    # login user
                    user = auth.authenticate(username=user.email, password=request.POST["new_password"])
                    auth.login(request, user)

                next_param = request.GET.get("next", "/")
                redirect_to = next_param if is_safe_url(next_param, settings.ALLOWED_REDIRECT_HOSTS, True) else "/"
                return HttpResponseRedirect(resolve_url(redirect_to))
        else:
            form = forms.SetPasswordForm(user)
    else:
        valid_link = False
        form = None

    context = {"form": form, "valid_link": valid_link, "user_email": user.email}

    return TemplateResponse(request, template_name, context)


def set_new_user(request, uidb64=None, token=None, template_name=None):
    assert uidb64 is not None and token is not None  # checked by URLconf

    try:
        uid = urlsafe_base64_decode(uidb64)
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and auth_tokens.default_token_generator.check_token(user, token):
        valid_link = True
        if request.method == "POST":
            form = forms.SetNewUserForm(user, request.POST)
            if form.is_valid():
                form.save()

                if not any(user.email.endswith(postfix) for postfix in settings.INTERNAL_EMAIL_POSTFIXES):
                    # login user
                    user = auth.authenticate(username=user.email, password=request.POST["new_password"])
                    auth.login(request, user)

                next_param = request.GET.get("next", "/")
                redirect_to = next_param if is_safe_url(next_param, settings.ALLOWED_REDIRECT_HOSTS, True) else "/"
                return HttpResponseRedirect(resolve_url(redirect_to))
        else:
            form = forms.SetNewUserForm(user)
    else:
        valid_link = False
        form = None

    context = {"form": form, "valid_link": valid_link, "user_email": user.email}

    return TemplateResponse(request, template_name, context)


def google_callback(request, *args, **kwargs):
    if "error" in request.GET or "code" not in request.GET:
        return _fail_response()

    user_data = gauth.authorize(request)
    if not user_data:
        return _fail_response()

    user = auth.authenticate(oauth_data=user_data)

    if user and user.is_active:
        response = HttpResponseRedirect(request.GET.get("state") or reverse("index"))
        auth.login(request, user)
        devices.handle_user_device(request, response)
        return response
    else:
        return _fail_response("Your Google account is not connected with Zemanta.")


def _fail_response(message="Google authentication failed."):
    url = reverse("signin")
    if message:
        message = urllib.parse.urlencode({"gauth_error": message or ""})
        url += "?" + message
    return redirect(url)
