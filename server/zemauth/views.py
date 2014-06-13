import urllib

from django.conf import settings
from django.contrib import auth
from django.contrib.auth import views as auth_views
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.http import HttpResponseRedirect

import gauth
from utils import statsd_helper


@statsd_helper.statsd_timer('auth', 'signin_response_time')
def login(request, *args, **kwargs):
    """Wraps login view and injects certain query string values into
    extra_context and passes it to django.contrib.auth.views.login.
    """
    import time
    time.sleep(1)

    if 'error' in request.GET:
        return _fail_response()

    if 'extra_context' not in kwargs:
        kwargs['extra_context'] = {}

    kwargs['extra_context']['gauth_error'] = request.GET.get('gauth_error')

    if settings.GOOGLE_OAUTH_ENABLED:
        kwargs['extra_context']['gauth_url'] = gauth.get_uri(request)

    return auth_views.login(request, *args, **kwargs)


def google_callback(request, *args, **kwargs):
    if 'error' in request.GET or 'code' not in request.GET:
        return _fail_response()

    user_data = gauth.authorize(request)
    if not user_data:
        return _fail_response()

    user = auth.authenticate(oauth_data=user_data)

    if user and user.is_active:
        auth.login(request, user)
        return HttpResponseRedirect(reverse('dash.views.index'))
    else:
        return _fail_response('Your Google account is not connected with Zemanta.')


def _fail_response(message='Google authentication failed.'):
    url = reverse('zemauth.views.login')
    if message:
        message = urllib.urlencode({'gauth_error': message or ""})
        url += "?" + message
    return redirect(url)
