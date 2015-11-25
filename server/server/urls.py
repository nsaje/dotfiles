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
import reports.views

import dash.views.daily_stats
import dash.views.bcm
import dash.views.export
import dash.views.export_plus
import dash.views.sync
import dash.views.table
import dash.views.agency
import dash.views.views


admin.site.login = login_required(admin.site.login)

# Decorators for auth views for statsd.
auth_views.logout_then_login = utils.statsd_helper.statsd_timer('auth', 'signout_response_time')(
    auth_views.logout_then_login)


# RedirectView.permanent will be False
# by default from Django 1.9 onwards,
# so set it to True to silence warnings
class AdminRedirectView(RedirectView):
    permanent = True


urlpatterns = patterns(
    '',
    url(r'^signin$',
        'zemauth.views.login',
        {'authentication_form': AuthenticationForm, 'template_name': 'zemauth/signin.html'},
        name='signin'),
    url(r'^signout$', 'django.contrib.auth.views.logout_then_login'),
    url(r'^password_reset',
        'zemauth.views.password_reset',
        {'template_name': 'zemauth/password_reset.html'},
        name='password_reset'),
    url(r'^set_password/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
        'zemauth.views.set_password',
        {'template_name': 'zemauth/set_password.html'},
        name='set_password'),
    url(r'^admin$', AdminRedirectView.as_view(url='/admin/')),
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
        name='ad_group_settings'
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/agency/',
        login_required(dash.views.agency.AdGroupAgency.as_view()),
        name='ad_group_agency'
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/sources/$',
        login_required(dash.views.views.AdGroupSources.as_view()),
        name='ad_group_sources'
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
        name='ad_group_source_settings'
    ),
    url(
        r'^api/(?P<level_>(ad_groups|campaigns|accounts))/(?P<id_>\d+)/sources/table/',
        login_required(dash.views.table.SourcesTable.as_view()),
    ),
    url(
        r'^api/(?P<level_>(ad_groups))/(?P<id_>\d+)/publishers/table/',
        login_required(dash.views.table.PublishersTable.as_view()),
        name='ad_group_publishers_table'
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/publishers/blacklist/',
        login_required(dash.views.views.PublishersBlacklistStatus.as_view()),
        name='ad_group_publishers_blacklist'
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/publishers/check_sync_progress/',
        login_required(dash.views.sync.AdGroupPublisherBlacklistCheckSyncProgress.as_view()),
        name='ad_group_publishers_blacklist_sync_progress'
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/contentads/export/allowed/',
        login_required(dash.views.export.AdGroupAdsExportAllowed.as_view())
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/contentadsplus/export/allowed/',
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
        r'^api/ad_groups/(?P<ad_group_id>\d+)/contentadsplus/export/',
        login_required(dash.views.export.AdGroupAdsPlusExport.as_view())
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
        r'^api/ad_groups/(?P<ad_group_id>\d+)/contentadsplus/table/updates/',
        login_required(dash.views.table.AdGroupAdsPlusTableUpdates.as_view()),
        name='ad_group_ads_plus_table_updates'
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/contentadsplus/table/',
        login_required(dash.views.table.AdGroupAdsPlusTable.as_view()),
        name='ad_group_ads_plus_table'
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/contentads_plus/upload/(?P<batch_id>\d+)/status/',
        login_required(dash.views.views.AdGroupAdsPlusUploadStatus.as_view()),
        name='ad_group_ads_plus_upload_status'
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/contentads_plus/upload/(?P<batch_id>\d+)/report/',
        login_required(dash.views.views.AdGroupAdsPlusUploadReport.as_view()),
        name='ad_group_ads_plus_upload_report'
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/contentads_plus/upload/',
        login_required(dash.views.views.AdGroupAdsPlusUpload.as_view()), name='ad_group_ads_plus_upload'
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/contentads/state/',
        login_required(dash.views.views.AdGroupContentAdState.as_view()),
        name='ad_group_content_ad_state'
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/contentads/csv/',
        login_required(dash.views.views.AdGroupContentAdCSV.as_view()),
        name='ad_group_content_ad_csv'
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/contentads/archive/$',
        login_required(dash.views.views.AdGroupContentAdArchive.as_view()),
        name='ad_group_content_ad_archive'
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/contentads/restore/$',
        login_required(dash.views.views.AdGroupContentAdRestore.as_view()),
        name='ad_group_content_ad_restore'
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
        name='ad_group_daily_stats'
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/contentads_plus/daily_stats/',
        login_required(dash.views.daily_stats.AdGroupAdsPlusDailyStats.as_view()),
        name='ad_group_ads_plus_daily_stats'
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/publishers/daily_stats/',
        login_required(dash.views.daily_stats.AdGroupPublishersDailyStats.as_view()),
        name='ad_group_publishers_daily_stats'
    ),
    url(
        r'^api/campaigns/(?P<campaign_id>\d+)/daily_stats/',
        login_required(dash.views.daily_stats.CampaignDailyStats.as_view()),
        name='campaign_daily_stats'
    ),
    url(
        r'^api/accounts/(?P<account_id>\d+)/daily_stats/',
        login_required(dash.views.daily_stats.AccountDailyStats.as_view()),
        name='account_daily_stats'
    ),
    url(
        r'^api/all_accounts/daily_stats/',
        login_required(dash.views.daily_stats.AccountsDailyStats.as_view()),
        name='accounts_daily_stats'
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
        name='campaign_ad_groups'
    ),
    url(
        r'^api/campaigns/(?P<campaign_id>\d+)/agency/',
        login_required(dash.views.agency.CampaignAgency.as_view()),
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
        name='account_agency'
    ),
    url(
        r'^api/accounts/(?P<account_id>\d+)/users/(?P<user_id>\d+)/activate',
        login_required(dash.views.agency.UserActivation.as_view()),
        name='account_reactivation',
    ),
    url(
        r'^api/accounts/(?P<account_id>\d+)/conversion_pixels/',
        login_required(dash.views.agency.AccountConversionPixels.as_view()),
        name='account_conversion_pixels',
    ),
    url(
        r'^api/conversion_pixel/(?P<conversion_pixel_id>\d+)/',
        login_required(dash.views.agency.ConversionPixel.as_view()),
        name='conversion_pixel',
    ),
    url(
        r'^api/campaigns/(?P<campaign_id>\d+)/conversion_goals/(?P<conversion_goal_id>\d+)/',
        login_required(dash.views.agency.ConversionGoal.as_view()),
        name='conversion_goal',
    ),
    url(
        r'^api/campaigns/(?P<campaign_id>\d+)/conversion_goals/',
        login_required(dash.views.agency.CampaignConversionGoals.as_view()),
        name='campaign_conversion_goals',
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
        name='ad_group_archive',
    ),
    url(
        r'^api/sources/',
        login_required(dash.views.views.AvailableSources.as_view()),
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/restore/',
        login_required(dash.views.views.AdGroupRestore.as_view()),
        name='ad_group_restore',
    ),
    url(
        r'^api/accounts/export/',
        login_required(dash.views.export.AllAccountsExport.as_view())
    ),
    url(
        r'^api/accounts/$',
        login_required(dash.views.views.Account.as_view()),
    ),
    url(
        r'^api/accounts/(?P<account_id>\d+)/credit/(?P<credit_id>\d+)/',
        login_required(dash.views.bcm.AccountCreditItemView.as_view()),
        name='accounts_credit_item',
    ),
    url(
        r'^api/accounts/(?P<account_id>\d+)/credit/',
        login_required(dash.views.bcm.AccountCreditView.as_view()),
        name='accounts_credit'
    ),
    url(
        r'^api/campaigns/(?P<campaign_id>\d+)/budget-plus/(?P<budget_id>\d+)/',
        login_required(dash.views.bcm.CampaignBudgetItemView.as_view()),
        name='campaigns_budget_item'
    ),
    url(
        r'^api/campaigns/(?P<campaign_id>\d+)/budget-plus/',
        login_required(dash.views.bcm.CampaignBudgetView.as_view()),
        name='campaigns_budget'
    ),
    url(r'^api/nav_data$', login_required(dash.views.views.NavigationDataView.as_view())),
    url(
        r'^api/users/(?P<user_id>(\d+|current))/$',
        login_required(dash.views.views.User.as_view()),
        name='user'
    ),
    url(
        r'^api/(?P<level_>(ad_groups|campaigns|accounts))/(?P<id_>\d+)/export_plus/allowed/',
        login_required(dash.views.export_plus.ExportAllowed.as_view())
    ),
    url(
        r'^api/(?P<level_>(all_accounts))/export_plus/allowed/',
        login_required(dash.views.export_plus.ExportAllowed.as_view())
    ),
    url(
        r'^api/(?P<level_>(ad_groups|campaigns|accounts|all_accounts))/(?P<id_>\d+)/sources/export_plus/allowed/',
        login_required(dash.views.export_plus.SourcesExportAllowed.as_view())
    ),
    url(
        r'^api/(?P<level_>(all_accounts))/sources/export_plus/allowed/',
        login_required(dash.views.export_plus.SourcesExportAllowed.as_view())
    ),
    url(
        r'^api/campaigns/(?P<campaign_id>\d+)/export_plus/',
        login_required(dash.views.export_plus.CampaignAdGroupsExport.as_view())
    ),
    url(
        r'^api/accounts/(?P<account_id>\d+)/export_plus/',
        login_required(dash.views.export_plus.AccountCampaignsExport.as_view())
    ),
    url(
        r'^api/accounts/(?P<account_id>\d+)/reports/',
        login_required(dash.views.export_plus.AccountReports.as_view())
    ),
    url(
        r'^api/accounts/reports/remove/(?P<scheduled_report_id>\d+)',
        login_required(dash.views.export_plus.AccountReports.as_view())
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/export_plus/',
        login_required(dash.views.export_plus.AdGroupAdsPlusExport.as_view())
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/sources/export_plus/',
        login_required(dash.views.export_plus.AdGroupSourcesExport.as_view())
    ),
    url(
        r'^api/campaigns/(?P<campaign_id>\d+)/sources/export_plus/',
        login_required(dash.views.export_plus.CampaignSourcesExport.as_view())
    ),
    url(
        r'^api/accounts/(?P<account_id>\d+)/sources/export_plus/',
        login_required(dash.views.export_plus.AccountSourcesExport.as_view())
    ),
    url(
        r'^api/all_accounts/sources/export_plus/',
        login_required(dash.views.export_plus.AllAccountsSourcesExport.as_view())
    ),
    url(
        r'^api/accounts/export_plus/',
        login_required(dash.views.export_plus.AllAccountsExport.as_view())
    )
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

# Crossvalidation Api
urlpatterns += patterns(
    '',
    url(
        r'^api/crossvalidation$',
        reports.views.crossvalidation,
        name='api.crossvalidation',
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

# Sharethrough callback
urlpatterns += patterns(
    '',
    url(
        r'^sharethrough_approval/',
        dash.views.views.sharethrough_approval,
        name='sharethrough_approval'
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
