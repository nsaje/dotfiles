from django.contrib.auth.decorators import login_required
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from django.views.generic import TemplateView
from django.conf.urls import handler404

import utils.statsd_helper

from zemauth.forms import AuthenticationForm

import zweiapi.views
import actionlog.views
import convapi.views

import dash.views.daily_stats
import dash.views.export
import dash.views.sync
import dash.views.table
import dash.views.agency
import dash.views.views


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
    url(r'^set_password/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
        'zemauth.views.set_password',
        {'template_name': 'zemauth/set_password.html'},
        name='set_password'),
    url(r'^admin$', RedirectView.as_view(url='/admin/')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^oauth2callback', 'zemauth.views.google_callback'),
    url(r'^supply_dash/', 'dash.views.views.supply_dash_redirect'),

    url(r'^demo_mode$', 'dash.views.views.demo_mode')
)

# Api
urlpatterns += patterns(
    '',
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/state/',
        login_required(dash.views.views.AdGroupState.as_view()),
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/settings/',
        login_required(dash.views.agency.AdGroupSettings.as_view()),
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/agency/',
        login_required(dash.views.agency.AdGroupAgency.as_view()),
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/sources/$',
        login_required(dash.views.views.AdGroupSources.as_view()),
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id_>\d+)/sources/table/updates/',
        login_required(dash.views.table.AdGroupSourcesTableUpdates.as_view()),
    ),
    url(
        r'^api/(?P<level_>(all_accounts))/sources/table/',
        login_required(dash.views.table.SourcesTable.as_view()),
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/sources/(?P<source_id>\d+)/settings/',
        login_required(dash.views.views.AdGroupSourceSettings.as_view()),
    ),
    url(
        r'^api/(?P<level_>(ad_groups|campaigns|accounts))/(?P<id_>\d+)/sources/table/',
        login_required(dash.views.table.SourcesTable.as_view()),
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/contentads/export/allowed/',
        login_required(dash.views.export.AdGroupAdsExportAllowed.as_view())
    ),
    url(
        r'^api/campaigns/(?P<campaign_id>\d+)/ad_groups/export/allowed/',
        login_required(dash.views.export.CampaignAdGroupsExportAllowed.as_view())
    ),
    url(
        r'^api/campaigns/(?P<campaign_id>\d+)/ad_groups/export/',
        login_required(dash.views.export.CampaignAdGroupsExport.as_view())
    ),
    url(
        r'^api/accounts/(?P<account_id>\d+)/campaigns/export/',
        login_required(dash.views.export.AccountCampaignsExport.as_view())
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/contentads/export/',
        login_required(dash.views.export.AdGroupAdsExport.as_view())
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/sources/export/',
        login_required(dash.views.export.AdGroupSourcesExport.as_view())
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/contentads/table/',
        login_required(dash.views.table.AdGroupAdsTable.as_view()),
    ),
    url(
        r'^api/accounts/table/',
        login_required(dash.views.table.AccountsAccountsTable.as_view()),
    ),
    url(
        r'^api/accounts/sync/',
        login_required(dash.views.sync.AccountSync.as_view()),
    ),
    url(
        r'^api/accounts/check_sync_progress/',
        login_required(dash.views.sync.AccountSyncProgress.as_view()),
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/sync/',
        login_required(dash.views.sync.AdGroupSync.as_view()),
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/check_sync_progress/',
        login_required(dash.views.sync.AdGroupCheckSyncProgress.as_view()),
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/daily_stats/',
        login_required(dash.views.daily_stats.AdGroupDailyStats.as_view()),
    ),
    url(
        r'^api/campaigns/(?P<campaign_id>\d+)/daily_stats/',
        login_required(dash.views.daily_stats.CampaignDailyStats.as_view()),
    ),
    url(
        r'^api/accounts/(?P<account_id>\d+)/daily_stats/',
        login_required(dash.views.daily_stats.AccountDailyStats.as_view()),
    ),
    url(
        r'^api/all_accounts/daily_stats/',
        login_required(dash.views.daily_stats.AccountsDailyStats.as_view()),
    ),
    url(
        r'^api/accounts/(?P<account_id>\d+)/campaigns/table/',
        login_required(dash.views.table.AccountCampaignsTable.as_view()),
    ),
    url(
        r'^api/campaigns/(?P<campaign_id>\d+)/ad_groups/table/',
        login_required(dash.views.table.CampaignAdGroupsTable.as_view()),
    ),
    url(
        r'^api/campaigns/(?P<campaign_id>\d+)/ad_groups/',
        login_required(dash.views.views.CampaignAdGroups.as_view()),
    ),
    url(
        r'^api/campaigns/(?P<campaign_id>\d+)/settings/',
        login_required(dash.views.agency.CampaignSettings.as_view()),
    ),
    url(
        r'^api/campaigns/(?P<campaign_id>\d+)/budget/',
        login_required(dash.views.agency.CampaignBudget.as_view()),
    ),
    url(
        r'^api/campaigns/sync/',
        login_required(dash.views.sync.CampaignSync.as_view()),
    ),
    url(
        r'^api/campaigns/check_sync_progress/',
        login_required(dash.views.sync.CampaignSyncProgress.as_view()),
    ),
    url(
        r'^api/accounts/(?P<account_id>\d+)/campaigns/',
        login_required(dash.views.views.AccountCampaigns.as_view()),
    ),
    url(
        r'^api/accounts/(?P<account_id>\d+)/agency/',
        login_required(dash.views.agency.AccountAgency.as_view()),
    ),
    url(
        r'^api/accounts/(?P<account_id>\d+)/users/(?P<user_id>\d+)/',
        login_required(dash.views.agency.AccountUsers.as_view()),
    ),
    url(
        r'^api/accounts/(?P<account_id>\d+)/users/',
        login_required(dash.views.agency.AccountUsers.as_view()),
    ),
    url(
        r'^api/accounts/(?P<account_id>\d+)/archive/',
        login_required(dash.views.views.AccountArchive.as_view()),
    ),
    url(
        r'^api/accounts/(?P<account_id>\d+)/restore/',
        login_required(dash.views.views.AccountRestore.as_view()),
    ),
    url(
        r'^api/campaigns/(?P<campaign_id>\d+)/archive/',
        login_required(dash.views.views.CampaignArchive.as_view()),
    ),
    url(
        r'^api/campaigns/(?P<campaign_id>\d+)/restore/',
        login_required(dash.views.views.CampaignRestore.as_view()),
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/archive/',
        login_required(dash.views.views.AdGroupArchive.as_view()),
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/restore/',
        login_required(dash.views.views.AdGroupRestore.as_view()),
    ),
    url(
        r'^api/accounts/export/',
        login_required(dash.views.export.AllAccountsExport.as_view())
    ),
    url(
        r'^api/accounts/$',
        login_required(dash.views.views.Account.as_view()),
    ),
    url(r'^api/nav_data$', login_required(dash.views.views.NavigationDataView.as_view())),
    url(r'^api/users/(?P<user_id>(\d+|current))/$', login_required(dash.views.views.User.as_view())),
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


# Conversion Api
urlpatterns += patterns(
    '',
    url(
        r'^convapi/mailgun/gareps$',
        convapi.views.mailgun_gareps,
        name='convapi.mailgun',
    )
)


# Source OAuth
urlpatterns += patterns(
    '',
    url(
        r'^source/oauth/authorize/(?P<source_name>yahoo)',
        dash.views.views.oauth_authorize,
        name='source.oauth.authorize',
    ),
    url(
        r'^source/oauth/(?P<source_name>yahoo)',
        dash.views.views.oauth_redirect,
        name='source.oauth.redirect'
    )
)

# Health Check
urlpatterns += patterns(
    '',
    url(
        r'^healthcheck$',
        dash.views.views.healthcheck,
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
    url(r'^api/', handler404),
    url(r'^', dash.views.views.index, name='index')
)
