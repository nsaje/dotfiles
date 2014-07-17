from django.contrib.auth.decorators import login_required
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView

import utils.statsd_helper

from zemauth.forms import AuthenticationForm

import zweiapi.views
import actionlog.views
import dash.views

admin.site.login = login_required(admin.site.login)

# Decorators for auth views for statsd.
auth_views.logout_then_login = utils.statsd_helper.statsd_timer('auth', 'signout_response_time')(
    auth_views.logout_then_login)

urlpatterns = patterns(
    '',
    url(r'^signin$',
        'zemauth.views.login',
        {'authentication_form': AuthenticationForm, 'template_name': 'zemauth/signin.html'}),
    url(r'^signout$', 'django.contrib.auth.views.logout_then_login'),
    url(r'^admin$', RedirectView.as_view(url='/admin/')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^oauth2callback', 'zemauth.views.google_callback'),
)

# Api
urlpatterns += patterns(
    '',
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/settings/',
        login_required(dash.views.AdGroupSettings.as_view()),
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/sources/table/',
        login_required(dash.views.AdGroupSourcesTable.as_view()),
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/ads/export/',
        login_required(dash.views.AdGroupAdsExport.as_view())
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/sources/export/',
        login_required(dash.views.AdGroupSourcesExport.as_view())
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/ads/table/',
        login_required(dash.views.AdGroupAdsTable.as_view()),
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/sync/',
        login_required(dash.views.AdGroupSync.as_view()),
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/daily_stats/',
        login_required(dash.views.AdGroupDailyStats.as_view()),
    ),
    url(r'^api/nav_data$', login_required(dash.views.NavigationDataView.as_view())),
    url(r'^api/users/(?P<user_id>(\d+|current))/$', login_required(dash.views.User.as_view())),
)

# Action Log
urlpatterns += patterns(
    '',
    url(
        r'^action_log/?$',
        login_required(actionlog.views.action_log),
        name='action_log_view',
    ),
    url(
        r'^action_log/api/$',
        login_required(actionlog.views.ActionLogApiView.as_view()),
        name='action_log_api',
    ),
    url(
        r'^action_log/api/(?P<action_log_id>\d+)/$',
        login_required(actionlog.views.ActionLogApiView.as_view()),
        name='action_log_api_put',
    ),
)

# Zwei Api
urlpatterns += patterns(
    '',
    url(
        r'^api/zwei_callback/(?P<action_id>\d+)$',
        zweiapi.views.zwei_callback,
        name='api.zwei_callback',
    )
)

# Health Check
urlpatterns += patterns(
    '',
    url(
        r'^healthcheck$',
        dash.views.healthcheck,
        name='healthcheck',
    )
)

urlpatterns += patterns(
    '',
    url(r'^', dash.views.index, name='index')
)
