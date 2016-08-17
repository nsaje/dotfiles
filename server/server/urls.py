from django.contrib.auth.decorators import login_required
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from django.views.generic import TemplateView
import django.views.defaults

from zemauth.forms import AuthenticationForm

import zweiapi.views
import k1api_old.views
import k1api.views
import actionlog.views
import reports.views
import zemauth.views

import dash.views.daily_stats
import dash.views.bcm
import dash.views.breakdown
import dash.views.export
import dash.views.sync
import dash.views.table
import dash.views.agency
import dash.views.views
import dash.views.navigation
import dash.views.callbacks
import dash.views.upload
import dash.views.grid


admin.site.login = login_required(admin.site.login)


# RedirectView.permanent will be False
# by default from Django 1.9 onwards,
# so set it to True to silence warnings
class AdminRedirectView(RedirectView):
    permanent = True


urlpatterns = [
    url(r'^signin$',
        zemauth.views.login,
        {'authentication_form': AuthenticationForm, 'template_name': 'zemauth/signin.html'},
        name='signin'),
    url(r'^signout$', auth_views.logout_then_login),
    url(r'^password_reset',
        zemauth.views.password_reset,
        {'template_name': 'zemauth/password_reset.html'},
        name='password_reset'),
    url(r'^set_password/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
        zemauth.views.set_password,
        {'template_name': 'zemauth/set_password.html'},
        name='set_password'),
    url(r'^admin$', AdminRedirectView.as_view(url='/admin/')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^oauth2callback', zemauth.views.google_callback),
    url(r'^supply_dash/', dash.views.views.supply_dash_redirect),

    url(r'^demo_mode$', dash.views.views.demo_mode)
]

# Api
urlpatterns += [
    url(
        r'^api/grid/ad_groups/(?P<ad_group_id>\d+)/settings/',
        login_required(dash.views.grid.AdGroupSettings.as_view()),
        name='grid_ad_group_settings'
    ),
    url(
        r'^api/grid/content_ads/(?P<content_ad_id>\d+)/settings/',
        login_required(dash.views.grid.ContentAdSettings.as_view()),
        name='grid_content_ad_settings'
    ),
    url(
        r'^api/grid/ad_groups/(?P<ad_group_id>\d+)/sources/(?P<source_id>\d+)/settings/',
        login_required(dash.views.grid.AdGroupSourceSettings.as_view()),
        name='grid_ad_group_source_settings'
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/settings/state/',
        login_required(dash.views.agency.AdGroupSettingsState.as_view()),
        name='ad_group_settings_state'
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/settings/',
        login_required(dash.views.agency.AdGroupSettings.as_view()),
        name='ad_group_settings'
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
        r'^api/campaigns/(?P<campaign_id>\d+)/ad_groups/export/allowed/',
        login_required(dash.views.export.CampaignAdGroupsExportAllowed.as_view())
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/contentads/table/updates/',
        login_required(dash.views.table.AdGroupAdsTableUpdates.as_view()),
        name='ad_group_ads_table_updates'
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/contentads/table/',
        login_required(dash.views.table.AdGroupAdsTable.as_view()),
        name='ad_group_ads_table'
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/contentads/upload/csv/',
        login_required(dash.views.upload.UploadCsv.as_view()), name='upload_csv'
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/contentads/upload/(?P<batch_id>\d+)/status/',
        login_required(dash.views.upload.UploadStatus.as_view()), name='upload_status'
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/contentads/upload/(?P<batch_id>\d+)/download/',
        login_required(dash.views.upload.CandidatesDownload.as_view()), name='upload_candidates_download'
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/contentads/upload/(?P<batch_id>\d+)/save/',
        login_required(dash.views.upload.UploadSave.as_view()), name='upload_save'
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/contentads/upload/(?P<batch_id>\d+)/cancel/',
        login_required(dash.views.upload.UploadCancel.as_view()), name='upload_cancel'
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/contentads/upload'
        '/(?P<batch_id>\d+)/candidate/(?P<candidate_id>\d+)/',
        login_required(dash.views.upload.Candidate.as_view()), name='upload_candidate'
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
        r'^api/ad_groups/(?P<ad_group_id>\d+)/overview/',
        login_required(dash.views.views.AdGroupOverview.as_view()),
        name='ad_group_overview'
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
        r'^api/accounts/overview/',
        login_required(dash.views.views.AllAccountsOverview.as_view()),
        name='all_accounts_overview'
    ),
    url(
        r'^api/history/',
        login_required(dash.views.agency.History.as_view()),
        name='history'
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
        r'^api/ad_groups/(?P<ad_group_id>\d+)/contentads/daily_stats/',
        login_required(dash.views.daily_stats.AdGroupAdsDailyStats.as_view()),
        name='ad_group_ads_daily_stats'
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
        r'^api/campaigns/(?P<campaign_id>\d+)/settings/',
        login_required(dash.views.agency.CampaignSettings.as_view()),
    ),
    url(
        r'^api/campaigns/(?P<campaign_id>\d+)/goals/validate/',
        login_required(dash.views.agency.CampaignGoalValidation.as_view()),
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
        name='account_campaigns'
    ),
    url(
        r'^api/campaigns/(?P<campaign_id>\d+)/content-insights/',
        login_required(dash.views.agency.CampaignContentInsights.as_view()),
    ),
    url(
        r'^api/accounts/(?P<account_id>\d+)/settings/',
        login_required(dash.views.agency.AccountSettings.as_view()),
        name='account_settings'
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
        r'^api/accounts/(?P<account_id>\d+)/users/(?P<user_id>\d+)/',
        login_required(dash.views.agency.AccountUsers.as_view()),
    ),
    url(
        r'^api/accounts/(?P<account_id>\d+)/users/',
        login_required(dash.views.agency.AccountUsers.as_view()),
        name='account_users',
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
        r'^api/campaigns/(?P<campaign_id>\d+)/overview/',
        login_required(dash.views.views.CampaignOverview.as_view()),
        name='campaign_overview'
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
        r'^api/agencies/',
        login_required(dash.views.agency.Agencies.as_view()),
        name='agencies',
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/restore/',
        login_required(dash.views.views.AdGroupRestore.as_view()),
        name='ad_group_restore',
    ),
    url(
        r'^api/accounts/$',
        login_required(dash.views.views.Account.as_view()),
        name='accounts_create',
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
        r'^api/accounts/(?P<account_id>\d+)/overview/',
        login_required(dash.views.views.AccountOverview.as_view()),
        name='account_overview'
    ),
    url(
        r'^api/campaigns/(?P<campaign_id>\d+)/budget/(?P<budget_id>\d+)/',
        login_required(dash.views.bcm.CampaignBudgetItemView.as_view()),
        name='campaigns_budget_item'
    ),
    url(
        r'^api/campaigns/(?P<campaign_id>\d+)/budget/',
        login_required(dash.views.bcm.CampaignBudgetView.as_view()),
        name='campaigns_budget'
    ),
    url(
        r'^api/(?P<level_>(ad_groups|campaigns|accounts))/(?P<id_>\d+)/nav/',
        login_required(dash.views.navigation.NavigationDataView.as_view()),
        name='navigation'
    ),
    url(
        r'^api/all_accounts/nav/',
        login_required(dash.views.navigation.NavigationAllAccountsDataView.as_view()),
        name='navigation_all_accounts'
    ),
    url(
        r'^api/nav/',
        login_required(dash.views.navigation.NavigationTreeView.as_view()),
        name='navigation_tree'
    ),
    url(
        r'^api/users/(?P<user_id>(\d+|current))/$',
        login_required(dash.views.views.User.as_view()),
        name='user'
    ),
    url(
        r'^api/(?P<level_>(ad_groups|campaigns|accounts))/(?P<id_>\d+)/export/allowed/',
        login_required(dash.views.export.ExportAllowed.as_view())
    ),
    url(
        r'^api/(?P<level_>(all_accounts))/export/allowed/',
        login_required(dash.views.export.ExportAllowed.as_view())
    ),
    url(
        r'^api/(?P<level_>(ad_groups|campaigns|accounts|all_accounts))/(?P<id_>\d+)/sources/export/allowed/',
        login_required(dash.views.export.SourcesExportAllowed.as_view())
    ),
    url(
        r'^api/(?P<level_>(all_accounts))/sources/export/allowed/',
        login_required(dash.views.export.SourcesExportAllowed.as_view())
    ),
    url(
        r'^api/campaigns/(?P<campaign_id>\d+)/export/',
        login_required(dash.views.export.CampaignAdGroupsExport.as_view())
    ),
    url(
        r'^api/accounts/(?P<account_id>\d+)/export/',
        login_required(dash.views.export.AccountCampaignsExport.as_view())
    ),
    url(
        r'^api/all_accounts/reports/',
        login_required(dash.views.export.ScheduledReports.as_view())
    ),
    url(
        r'^api/accounts/(?P<account_id>\d+)/reports/',
        login_required(dash.views.export.ScheduledReports.as_view())
    ),
    url(
        r'^api/accounts/reports/remove/(?P<scheduled_report_id>\d+)',
        login_required(dash.views.export.ScheduledReports.as_view())
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/export/',
        login_required(dash.views.export.AdGroupAdsExport.as_view())
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/sources/export/',
        login_required(dash.views.export.AdGroupSourcesExport.as_view())
    ),
    url(
        r'^api/campaigns/(?P<campaign_id>\d+)/sources/export/',
        login_required(dash.views.export.CampaignSourcesExport.as_view())
    ),
    url(
        r'^api/accounts/(?P<account_id>\d+)/sources/export/',
        login_required(dash.views.export.AccountSourcesExport.as_view())
    ),
    url(
        r'^api/all_accounts/sources/export/',
        login_required(dash.views.export.AllAccountsSourcesExport.as_view())
    ),
    url(
        r'^api/all_accounts/export/',
        login_required(dash.views.export.AllAccountsExport.as_view())
    ),
    url(
        r'^api/all_accounts/breakdown(?P<breakdown>(/\w+)+/?)',
        login_required(dash.views.breakdown.AllAccountsBreakdown.as_view()),
        name='breakdown_all_accounts'
    ),
    url(
        r'^api/accounts/(?P<account_id>\d+)/breakdown(?P<breakdown>(/\w+)+/?)',
        login_required(dash.views.breakdown.AccountBreakdown.as_view()),
        name='breakdown_accounts'
    ),
    url(
        r'^api/campaigns/(?P<campaign_id>\d+)/breakdown(?P<breakdown>(/\w+)+/?)',
        login_required(dash.views.breakdown.CampaignBreakdown.as_view()),
        name='breakdown_campaigns'
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/breakdown(?P<breakdown>(/\w+)+/?)',
        login_required(dash.views.breakdown.AdGroupBreakdown.as_view()),
        name='breakdown_ad_groups'
    ),
    url(
        r'^api/accounts/(?P<account_id>\d+)/facebook_account_status/',
        login_required(dash.views.agency.FacebookAccountStatus.as_view()),
        name='facebook_account_status'
    ),
    url(
        r'^api/demov3/$',
        login_required(dash.views.views.Demo.as_view()),
        name='demov3'
    ),
    url(
        r'^api/live-stream/allow/$',
        login_required(dash.views.views.LiveStreamAllow.as_view()),
        name='live_stream_allow'
    ),
]

# Lambdas
urlpatterns += [
    url(
        r'^api/callbacks/content-upload/$',
        dash.views.callbacks.content_upload,
        name='callbacks.content_upload',
    ),
]

# Action Log
urlpatterns += [
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
]

# Zwei Api
urlpatterns += [
    url(
        r'^api/zwei_callback/(?P<action_id>\d+)$',
        zweiapi.views.zwei_callback,
        name='api.zwei_callback',
    )
]

# K1 Api
urlpatterns += [
    url(
        r'^k1api/ad_group_source$',
        k1api_old.views.get_ad_group_source.as_view(),
        name='k1api.get_ad_group_source',
    ),
    url(
        r'k1api/get_ad_group_sources_for_source_type$',
        k1api_old.views.get_ad_group_sources_for_source_type.as_view(),
        name='k1api.get_ad_group_sources_for_source_type'
    ),
    url(
        r'^k1api/ad_group_source_ids$',
        k1api_old.views.get_ad_group_source_ids.as_view(),
        name='k1api.get_ad_group_source_ids',
    ),
    url(
        r'^k1api/content_ad_sources_for_ad_group$',
        k1api_old.views.get_content_ad_sources_for_ad_group.as_view(),
        name='k1api.get_content_ad_sources_for_ad_group',
    ),
    url(
        r'^k1api/get_accounts$',
        k1api_old.views.get_accounts.as_view(),
        name='k1api.get_accounts',
    ),
    url(
        r'^k1api/get_default_source_credentials$',
        k1api_old.views.get_default_source_credentials.as_view(),
        name='k1api.get_default_source_credentials',
    ),
    url(
        r'^k1api/get_custom_audiences$',
        k1api_old.views.get_custom_audiences.as_view(),
        name='k1api.get_custom_audiences',
    ),
    url(
        r'k1api/update_source_pixel$',
        k1api_old.views.update_source_pixel.as_view(),
        name='k1api.update_source_pixel',
    ),
    url(
        r'^k1api/get_source_credentials_for_reports_sync$',
        k1api_old.views.get_source_credentials_for_reports_sync.as_view(),
        name='k1api.get_source_credentials_for_reports_sync',
    ),
    url(
        r'^k1api/get_content_ad_source_mapping$',
        k1api_old.views.get_content_ad_source_mapping.as_view(),
        name='k1api.get_content_ad_source_mapping',
    ),
    url(
        r'^k1api/get_ga_accounts$',
        k1api_old.views.get_ga_accounts.as_view(),
        name='k1api.get_ga_accounts',
    ),
    url(
        r'^k1api/get_sources_by_tracking_slug$',
        k1api_old.views.get_sources_by_tracking_slug.as_view(),
        name='k1api.get_sources_by_tracking_slug',
    ),
    url(
        r'^k1api/get_accounts_slugs_ad_groups$',
        k1api_old.views.get_accounts_slugs_ad_groups.as_view(),
        name='k1api.get_accounts_slugs_ad_groups',
    ),
    url(
        r'^k1api/get_publishers_blacklist$',
        k1api_old.views.get_publishers_blacklist.as_view(),
        name='k1api.get_publishers_blacklist',
    ),
    url(
        r'^k1api/get_publishers_blacklist_outbrain$',
        k1api_old.views.get_publishers_blacklist_outbrain.as_view(),
        name='k1api.get_publishers_blacklist_outbrain',
    ),
    url(
        r'^k1api/get_ad_groups$',
        k1api_old.views.get_ad_groups.as_view(),
        name='k1api.get_ad_groups',
    ),
    url(
        r'k1api/get_ad_groups_exchanges$',
        k1api_old.views.get_ad_groups_exchanges.as_view(),
        name='k1api.get_ad_groups_exchanges',
    ),
    url(
        r'k1api/get_content_ads$',
        k1api_old.views.get_content_ads.as_view(),
        name='k1api.get_content_ads',
    ),
    url(
        r'k1api/get_content_ads_exchanges$',
        k1api_old.views.get_content_ads_exchanges.as_view(),
        name='k1api.get_content_ads_exchanges',
    ),
    url(
        r'^k1api/get_content_ad_ad_group$',
        k1api_old.views.get_content_ad_ad_group.as_view(),
        name='k1api.get_content_ad_ad_group',
    ),
    url(
        r'^k1api/update_content_ad_status$',
        k1api_old.views.update_content_ad_status.as_view(),
        name='k1api.update_content_ad_status',
    ),
    url(
        r'^k1api/set_source_campaign_key$',
        k1api_old.views.set_source_campaign_key.as_view(),
        name='k1api.set_source_campaign_key',
    ),
    url(
        r'^k1api/get_outbrain_marketer_id$',
        k1api_old.views.get_outbrain_marketer_id.as_view(),
        name='k1api.get_outbrain_marketer_id',
    ),
    url(
        r'^k1api/get_facebook_accounts$',
        k1api_old.views.get_facebook_accounts.as_view(),
        name='k1api.get_facebook_accounts',
    ),
    url(
        r'^k1api/update_facebook_account$',
        k1api_old.views.update_facebook_account.as_view(),
        name='k1api.update_facebook_account',
    ),
    url(
        r'^k1api/update_ad_group_source_state$',
        k1api_old.views.update_ad_group_source_state.as_view(),
        name='k1api.update_ad_group_source_state',
    ),
]

# K1 API new
urlpatterns += [
    url(
        r'^k1api_new/ad_groups$',
        k1api.views.AdGroupsView.as_view(),
        name='k1api_new.ad_groups',
    ),
    url(
        r'^k1api_new/ad_groups/sources$',
        k1api.views.AdGroupSourcesView.as_view(),
        name='k1api_new.ad_groups.sources',
    ),
    url(
        r'^k1api_new/content_ads$',
        k1api.views.ContentAdsView.as_view(),
        name='k1api_new.content_ads',
    ),
    url(
        r'^k1api_new/content_ads/sources$',
        k1api.views.ContentAdSourcesView.as_view(),
        name='k1api_new.content_ads.sources',
    ),
    url(
        r'^k1api_new/accounts$',
        k1api.views.AccountsView.as_view(),
        name='k1api_new.accounts',
    ),
    url(
        r'^k1api_new/sources$',
        k1api.views.SourcesView.as_view(),
        name='k1api_new.sources',
    ),
    url(
        r'k1api_new/source_pixels$',
        k1api.views.SourcePixelsView.as_view(),
        name='k1api_new.source_pixels',
    ),
    url(
        r'^k1api_new/ga_accounts$',
        k1api.views.GAAccountsView.as_view(),
        name='k1api_new.ga_accounts',
    ),
    url(
        r'^k1api_new/r1_mapping$',
        k1api.views.R1MappingView.as_view(),
        name='k1api_new.r1_mapping',
    ),
    url(
        r'^k1api_new/publishers_blacklist$',
        k1api.views.PublishersBlacklistView.as_view(),
        name='k1api_new.publishers_blacklist',
    ),
    url(
        r'^k1api_new/outbrain/publishers_blacklist$',
        k1api.views.OutbrainPublishersBlacklistView.as_view(),
        name='k1api_new.outbrain_publishers_blacklist',
    ),
    url(
        r'^k1api_new/outbrain/marketer_id$',
        k1api.views.OutbrainMarketerIdView.as_view(),
        name='k1api_new.outbrain_marketer_id',
    ),
    url(
        r'^k1api_new/facebook/accounts$',
        k1api.views.FacebookAccountsView.as_view(),
        name='k1api_new.facebook_accounts',
    ),
]

# Crossvalidation Api
urlpatterns += [
    url(
        r'^api/crossvalidation$',
        reports.views.crossvalidation,
        name='api.crossvalidation',
    )
]

# Source OAuth
urlpatterns += [
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
]

# Sharethrough callback
urlpatterns += [
    url(
        r'^sharethrough_approval/',
        dash.views.views.sharethrough_approval,
        name='sharethrough_approval'
    )
]

# Health Check
urlpatterns += [
    url(
        r'^healthcheck$',
        dash.views.views.healthcheck,
        name='healthcheck',
    )
]

# TOS
urlpatterns += [url(r'^tos/$', TemplateView.as_view(template_name='tos.html'))]

urlpatterns += [
    url(r'^api/', django.views.defaults.page_not_found, {'exception': None}),
    url(r'^', dash.views.views.index, name='index')
]
