import urllib

from django.conf import settings
from django.contrib import auth
from django.contrib.auth import views as auth_views, tokens as auth_tokens
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django.utils.http import urlsafe_base64_decode
from django.template.response import TemplateResponse
from django.shortcuts import resolve_url

import gauth
from utils import statsd_helper
from zemauth.models import User
from zemauth.forms import SetPasswordForm


@statsd_helper.statsd_timer('auth', 'signin_response_time')
def login(request, *args, **kwargs):
    """Wraps login view and injects certain query string values into
    extra_context and passes it to django.contrib.auth.views.login.
    """

    if 'error' in request.GET:
        return _fail_response()

    if 'extra_context' not in kwargs:
        kwargs['extra_context'] = {}

    kwargs['extra_context']['gauth_error'] = request.GET.get('gauth_error')

    if settings.GOOGLE_OAUTH_ENABLED:
        kwargs['extra_context']['gauth_url'] = gauth.get_uri(request)

    return auth_views.login(request, *args, **kwargs)


@statsd_helper.statsd_timer('auth', 'set_password')
def set_password(request, uidb64=None, token=None, template_name=None):
    assert uidb64 is not None and token is not None  # checked by URLconf

    try:
        uid = urlsafe_base64_decode(uidb64)
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and auth_tokens.default_token_generator.check_token(user, token):
        validlink = True
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()

                # login user
                user = auth.authenticate(username=user.email, password=request.POST['new_password'])
                auth.login(request, user)

                return HttpResponseRedirect(resolve_url('/'))
        else:
            form = SetPasswordForm(user)
    else:
        validlink = False
        form = None
    context = {
        'form': form,
        'validlink': validlink,
    }

    return TemplateResponse(request, template_name, context)


@statsd_helper.statsd_timer('auth', 'google_callback')
def google_callback(request, *args, **kwargs):
    if 'error' in request.GET or 'code' not in request.GET:
        return _fail_response()

    user_data = gauth.authorize(request)
    if not user_data:
        return _fail_response()

    user = auth.authenticate(oauth_data=user_data)

    if user and user.is_active:
        auth.login(request, user)
        return HttpResponseRedirect(request.GET.get('state') or reverse('dash.views.views.index'))
    else:
        return _fail_response('Your Google account is not connected with Zemanta.')


def _fail_response(message='Google authentication failed.'):
    url = reverse('zemauth.views.login')
    if message:
        message = urllib.urlencode({'gauth_error': message or ""})
        url += "?" + message
    return redirect(url)
