from django.contrib.auth.decorators import login_required
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from django.views.generic import TemplateView

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
    url(r'^supply_dash/', 'dash.views.supply_dash_redirect'),
)

# Api
urlpatterns += patterns(
    '',
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/state/',
        login_required(dash.views.AdGroupState.as_view()),
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/settings/',
        login_required(dash.views.AdGroupSettings.as_view()),
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/agency/',
        login_required(dash.views.AdGroupAgency.as_view()),
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/sources/table/',
        login_required(dash.views.AdGroupSourcesTable.as_view()),
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/contentads/export/',
        login_required(dash.views.AdGroupAdsExport.as_view())
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/sources/export/',
        login_required(dash.views.AdGroupSourcesExport.as_view())
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/contentads/table/',
        login_required(dash.views.AdGroupAdsTable.as_view()),
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/sync/',
        login_required(dash.views.AdGroupSync.as_view()),
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/check_sync_progress/',
        login_required(dash.views.AdGroupCheckSyncProgress.as_view()),
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/daily_stats/',
        login_required(dash.views.AdGroupDailyStats.as_view()),
    ),
    url(
        r'^api/campaigns/(?P<campaign_id>\d+)/settings/',
        login_required(dash.views.CampaignSettings.as_view()),
    ),
    url(
        r'^api/account/',
        login_required(dash.views.Account.as_view()),
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

# Source OAuth
urlpatterns += patterns(
    '',
    url(
        r'^source/oauth/authorize/(?P<source_name>yahoo)',
        dash.views.oauth_authorize,
        name='source.oauth.authorize',
    ),
    url(
        r'^source/oauth/(?P<source_name>yahoo)',
        dash.views.oauth_redirect,
        name='source.oauth.redirect'
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

# TOS
urlpatterns += patterns(
    '',
    url(r'^tos/$', TemplateView.as_view(template_name='tos.html')),
)

urlpatterns += patterns(
    '',
    url(r'^', dash.views.index, name='index')
)
