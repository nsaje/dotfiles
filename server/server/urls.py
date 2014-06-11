from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required

from dash import views as dash_views
from zemauth.forms import AuthenticationForm

import utils.statsd_helper

admin.site.login = login_required(admin.site.login)

# Decorators for auth views for statsd.
# auth_views.login = utils.statsd_helper.statsd_timer('one.auth')(auth_views.login)
auth_views.logout_then_login = utils.statsd_helper.statsd_timer('one.auth')(auth_views.logout_then_login)

urlpatterns = patterns(
    '',
    url(r'^$', dash_views.index, name='index'),
    url(r'^signin$',
        'zemauth.views.login',
        {'authentication_form': AuthenticationForm, 'template_name': 'zemauth/signin.html'}),
    url(r'^signout$', 'django.contrib.auth.views.logout_then_login'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^oauth2callback', 'zemauth.views.google_callback'),
)
