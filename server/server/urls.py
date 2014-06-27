from django.contrib.auth.decorators import login_required

from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from dash import views as dash_views
from zweiapi import views as zweiapiviews
from zemauth.forms import AuthenticationForm

import dash.views
import utils.statsd_helper

admin.site.login = login_required(admin.site.login)

# Decorators for auth views for statsd.
auth_views.logout_then_login = utils.statsd_helper.statsd_timer('auth', 'signout_response_time')(
    auth_views.logout_then_login)

urlpatterns = patterns(
    '',
    url(r'^$', dash_views.index, name='index'),
    url(r'^signin$',
        'zemauth.views.login',
        {'authentication_form': AuthenticationForm, 'template_name': 'zemauth/signin.html'}),
    url(r'^signout$', 'django.contrib.auth.views.logout_then_login'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^oauth2callback', 'zemauth.views.google_callback')
)

# Api
urlpatterns += patterns(
    '',
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/settings/',
        login_required(dash.views.AdGroupSettings.as_view())
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/networks/table/',
        login_required(dash.views.AdGroupNetworksTable.as_view())
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/networks/daily_stats/',
        login_required(dash.views.AdGroupNetworksDailyStats.as_view())
    ),
    url(r'^api/nav_data$', login_required(dash_views.NavigationDataView.as_view())),
    url(r'^api/users/(?P<user_id>(\d+|current))/$', login_required(dash.views.User.as_view()))
)

# Action Log
urlpatterns += patterns(
    '',
    url(
        r'^api/zwei_callback/(?P<action_id>\d+)$',
        zweiapiviews.zwei_callback,
        name='api.zwei_callback',
    )
)
