from django.contrib.auth.decorators import login_required
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from django.views.generic import TemplateView
import django.views.defaults
from django.shortcuts import render
import oauth2_provider.views

from zemauth.forms import AuthenticationForm

import k1api.views
import etl.crossvalidation.views
import zemauth.views

import dash.views.daily_stats
import dash.views.bcm
import dash.views.breakdown
import dash.views.export
import dash.views.agency
import dash.views.views
import dash.views.navigation
import dash.views.callbacks
import dash.views.upload
import dash.views.grid
import dash.views.audiences
import dash.views.alerts
import dash.views.bulk_actions
import dash.views.publishers
import dash.features.scheduled_reports.views


admin.site.login = login_required(admin.site.login)


# RedirectView.permanent will be False
# by default from Django 1.9 onwards,
# so set it to True to silence warnings
class AdminRedirectView(RedirectView):
    permanent = True


def oauth2_permission_wrap(view):
    def check(request, *args, **kwargs):
        if not request.user.has_perm('zemauth.can_manage_oauth2_apps'):
            return render(request, 'oauth2_provider/contact_for_access.html')
        return view(request, *args, **kwargs)
    return login_required(check)


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
    url(r'^admin/searchableselect/', include('searchableselect.urls')),
    url(r'^oauth2callback', zemauth.views.google_callback, name='zemauth.views.google_callback'),
    url(r'^supply_dash/', login_required(dash.views.views.supply_dash_redirect), name='supply_dash_redirect'),
]

# Oauth2 provider
oauth2_urlpatterns = [
    url(r'^authorize/$', oauth2_provider.views.AuthorizationView.as_view(), name="authorize"),
    url(r'^token/$', oauth2_provider.views.TokenView.as_view(), name="token"),
    url(r'^revoke_token/$', oauth2_provider.views.RevokeTokenView.as_view(), name="revoke-token"),
]

oauth2_urlpatterns += [
    url(r'^applications/$', oauth2_permission_wrap(oauth2_provider.views.ApplicationList.as_view()), name="list"),
    url(r'^applications/register/$', oauth2_permission_wrap(oauth2_provider.views.ApplicationRegistration.as_view()), name="register"),
    url(r'^applications/(?P<pk>\d+)/$', oauth2_permission_wrap(oauth2_provider.views.ApplicationDetail.as_view()), name="detail"),
    url(r'^applications/(?P<pk>\d+)/delete/$', oauth2_permission_wrap(oauth2_provider.views.ApplicationDelete.as_view()), name="delete"),
    url(r'^applications/(?P<pk>\d+)/update/$', oauth2_permission_wrap(oauth2_provider.views.ApplicationUpdate.as_view()), name="update"),
]

oauth2_urlpatterns += [
    url(r'^authorized_tokens/$', oauth2_permission_wrap(oauth2_provider.views.AuthorizedTokensListView.as_view()), name="authorized-token-list"),
    url(r'^authorized_tokens/(?P<pk>\d+)/delete/$', oauth2_permission_wrap(oauth2_provider.views.AuthorizedTokenDeleteView.as_view()),
        name="authorized-token-delete"),
]
urlpatterns += [
    url(r'^o/', include(oauth2_urlpatterns, namespace='oauth2_provider')),
]

# REST API
urlpatterns += [
    url(r'^rest/', include('restapi.urls')),
]

# Custom integrations API
urlpatterns += [
    url(r'^integrations/businesswire/', include('integrations.bizwire.urls')),
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
        r'^api/grid/content_ads/(?P<content_ad_id>\d+)/edit/',
        login_required(dash.views.grid.ContentAdEdit.as_view()),
        name='grid_content_ad_edit'
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
        r'^api/ad_groups/(?P<ad_group_id>\d+)/sources/(?P<source_id>\d+)/settings/',
        login_required(dash.views.views.AdGroupSourceSettings.as_view()),
        name='ad_group_source_settings'
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
        r'^api/ad_groups/(?P<ad_group_id>\d+)/contentads/upload/csv/',
        login_required(dash.views.upload.UploadCsv.as_view()), name='upload_csv'
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/contentads/upload/batch/',
        login_required(dash.views.upload.UploadBatch.as_view()), name='upload_batch'
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
        '/(?P<batch_id>\d+)/candidate/(?:(?P<candidate_id>\d+)/)?',
        login_required(dash.views.upload.Candidate.as_view()), name='upload_candidate'
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/contentads/upload'
        '/(?P<batch_id>\d+)/candidate_update/(?:(?P<candidate_id>\d+)/)?',
        login_required(dash.views.upload.CandidateUpdate.as_view()), name='upload_candidate_update'
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/contentads/edit/',
        login_required(dash.views.bulk_actions.AdGroupContentAdEdit.as_view()),
        name='ad_group_content_ad_edit'
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/contentads/state/',
        login_required(dash.views.bulk_actions.AdGroupContentAdState.as_view()),
        name='ad_group_content_ad_state'
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/contentads/csv/',
        login_required(dash.views.bulk_actions.AdGroupContentAdCSV.as_view()),
        name='ad_group_content_ad_csv'
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/contentads/archive/$',
        login_required(dash.views.bulk_actions.AdGroupContentAdArchive.as_view()),
        name='ad_group_content_ad_archive'
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/contentads/restore/$',
        login_required(dash.views.bulk_actions.AdGroupContentAdRestore.as_view()),
        name='ad_group_content_ad_restore'
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/sources/state/',
        login_required(dash.views.bulk_actions.AdGroupSourceState.as_view()),
        name='ad_group_source_state'
    ),
    url(
        r'^api/campaigns/(?P<campaign_id>\d+)/ad_groups/archive/$',
        login_required(dash.views.bulk_actions.CampaignAdGroupArchive.as_view()),
        name='campaign_ad_group_archive'
    ),
    url(
        r'^api/campaigns/(?P<campaign_id>\d+)/ad_groups/restore/$',
        login_required(dash.views.bulk_actions.CampaignAdGroupRestore.as_view()),
        name='campaign_ad_group_restore'
    ),
    url(
        r'^api/campaigns/(?P<campaign_id>\d+)/ad_groups/state/$',
        login_required(dash.views.bulk_actions.CampaignAdGroupState.as_view()),
        name='campaign_ad_group_state'
    ),
    url(
        r'^api/accounts/(?P<account_id>\d+)/campaigns/archive/$',
        login_required(dash.views.bulk_actions.AccountCampaignArchive.as_view()),
        name='account_campaign_archive'
    ),
    url(
        r'^api/accounts/(?P<account_id>\d+)/campaigns/restore/$',
        login_required(dash.views.bulk_actions.AccountCampaignRestore.as_view()),
        name='account_campaign_restore'
    ),
    url(
        r'^api/all_accounts/accounts/archive/$',
        login_required(dash.views.bulk_actions.AllAccountsAccountArchive.as_view()),
        name='all_accounts_account_archive'
    ),
    url(
        r'^api/all_accounts/accounts/restore/$',
        login_required(dash.views.bulk_actions.AllAccountsAccountRestore.as_view()),
        name='all_accounts_account_restore'
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/overview/',
        login_required(dash.views.views.AdGroupOverview.as_view()),
        name='ad_group_overview'
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
        r'^api/ad_groups/(?P<ad_group_id>\d+)/contentads/daily_stats/',
        login_required(dash.views.daily_stats.AdGroupContentAdsDailyStats.as_view()),
        name='ad_group_content_ads_daily_stats'
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/sources/daily_stats/',
        login_required(dash.views.daily_stats.AdGroupSourcesDailyStats.as_view()),
        name='ad_group_sources_daily_stats'
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/publishers/daily_stats/',
        login_required(dash.views.daily_stats.AdGroupPublishersDailyStats.as_view()),
        name='ad_group_publishers_daily_stats'
    ),
    url(
        r'^api/campaigns/(?P<campaign_id>\d+)/ad_groups/daily_stats/',
        login_required(dash.views.daily_stats.CampaignAdGroupsDailyStats.as_view()),
        name='campaign_ad_groups_daily_stats'
    ),
    url(
        r'^api/campaigns/(?P<campaign_id>\d+)/sources/daily_stats/',
        login_required(dash.views.daily_stats.CampaignSourcesDailyStats.as_view()),
        name='campaign_sources_daily_stats'
    ),
    url(
        r'^api/accounts/(?P<account_id>\d+)/campaigns/daily_stats/',
        login_required(dash.views.daily_stats.AccountCampaignsDailyStats.as_view()),
        name='account_campaigns_daily_stats'
    ),
    url(
        r'^api/accounts/(?P<account_id>\d+)/sources/daily_stats/',
        login_required(dash.views.daily_stats.AccountSourcesDailyStats.as_view()),
        name='account_sources_daily_stats'
    ),
    url(
        r'^api/all_accounts/accounts/daily_stats/',
        login_required(dash.views.daily_stats.AllAccountsAccountsDailyStats.as_view()),
        name='accounts_accounts_daily_stats'
    ),
    url(
        r'^api/all_accounts/sources/daily_stats/',
        login_required(dash.views.daily_stats.AllAccountsSourcesDailyStats.as_view()),
        name='accounts_sources_daily_stats'
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
        r'^api/accounts/(?P<account_id>\d+)/users/(?P<user_id>\d+)/(?P<action>\w+)',
        login_required(dash.views.agency.AccountUserAction.as_view()),
        name='account_user_action',
    ),
    url(
        r'^api/accounts/(?P<account_id>\d+)/conversion_pixels/',
        login_required(dash.views.agency.ConversionPixel.as_view()),
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
        name='account_users_manage',
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
    url(
        r'^api/accounts/(?P<account_id>\d+)/audiences/(?P<audience_id>\d+)/archive/',
        login_required(dash.views.audiences.AudienceArchive.as_view()),
        name='accounts_audience_archive',
    ),
    url(
        r'^api/accounts/(?P<account_id>\d+)/audiences/(?P<audience_id>\d+)/restore/',
        login_required(dash.views.audiences.AudienceRestore.as_view()),
        name='accounts_audience_restore',
    ),
    url(
        r'^api/accounts/(?P<account_id>\d+)/audiences/(?P<audience_id>\d+)/',
        login_required(dash.views.audiences.AudiencesView.as_view()),
        name='accounts_audience',
    ),
    url(
        r'^api/accounts/(?P<account_id>\d+)/audiences/',
        login_required(dash.views.audiences.AudiencesView.as_view()),
        name='accounts_audiences'
    ),
    url(
        r'^api/ad_groups/(?P<ad_group_id>\d+)/alerts/',
        login_required(dash.views.alerts.AdGroupAlerts.as_view()),
        name='ad_group_alerts',
    ),
    url(
        r'^api/campaigns/(?P<campaign_id>\d+)/alerts/',
        login_required(dash.views.alerts.CampaignAlerts.as_view()),
        name='campaign_alerts',
    ),
    url(
        r'^api/accounts/(?P<account_id>\d+)/alerts/',
        login_required(dash.views.alerts.AccountAlerts.as_view()),
        name='account_alerts',
    ),
    url(
        r'^api/all_accounts/alerts/',
        login_required(dash.views.alerts.AllAccountsAlerts.as_view()),
        name='all_account_alerts',
    ),
    url(
        r'^api/publishers/targeting/',
        login_required(dash.views.publishers.PublisherTargeting.as_view()),
        name='publisher_targeting'
    ),
    url(
        r'^api/accounts/(?P<account_id>\d+)/publisher_groups/(?P<publisher_group_id>\d+)/download/',
        login_required(dash.views.publishers.PublisherGroupsDownload.as_view()),
        name='download_publisher_groups'
    ),
    url(
        r'^api/accounts/(?P<account_id>\d+)/publisher_groups/$',
        login_required(dash.views.publishers.PublisherGroups.as_view()),
        name='accounts_publisher_groups'
    ),
    url(
        r'^api/accounts/(?P<account_id>\d+)/publisher_groups/upload/$',
        login_required(dash.views.publishers.PublisherGroupsUpload.as_view()),
        name='accounts_publisher_groups_upload'
    ),
    url(
        r'^api/publisher_groups/download/example/$',
        login_required(dash.views.publishers.PublisherGroupsExampleDownload.as_view()),
        name='publisher_groups_example'
    ),
    url(
        r'^api/accounts/(?P<account_id>\d+)/publisher_groups/errors/(?P<csv_key>[a-zA-Z0-9]+)$',
        login_required(dash.views.publishers.PublisherGroupsUpload.as_view()),
        name='accounts_publisher_groups_upload'
    ),
    url(
        r'^api/custom_report_download/',
        login_required(dash.views.export.CustomReportDownload.as_view()),
        name='custom_report_download'
    ),
    url(
        r'^api/scheduled_reports/$',
        login_required(dash.features.scheduled_reports.views.ScheduledReports.as_view()),
        name='scheduled_reports'
    ),
    url(
        r'^api/scheduled_reports/(?P<scheduled_report_id>\d+)/$',
        login_required(dash.features.scheduled_reports.views.ScheduledReportsDelete.as_view()),
        name='scheduled_reports_delete'
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

# K1 API
urlpatterns += [
    url(
        r'^k1api/ad_groups$',
        k1api.views.AdGroupsView.as_view(),
        name='k1api.ad_groups',
    ),
    url(
        r'^k1api/ad_groups/stats$',
        k1api.views.AdGroupStatsView.as_view(),
        name='k1api.ad_groups.stats',
    ),
    url(
        r'^k1api/ad_groups/sources$',
        k1api.views.AdGroupSourcesView.as_view(),
        name='k1api.ad_groups.sources',
    ),
    url(
        r'^k1api/ad_groups/sources/blockers$',
        k1api.views.AdGroupSourceBlockersView.as_view(),
        name='k1api.ad_groups.sources.blockers',
    ),
    url(
        r'^k1api/content_ads$',
        k1api.views.ContentAdsView.as_view(),
        name='k1api.content_ads',
    ),
    url(
        r'^k1api/content_ads/sources$',
        k1api.views.ContentAdSourcesView.as_view(),
        name='k1api.content_ads.sources',
    ),
    url(
        r'^k1api/accounts$',
        k1api.views.AccountsView.as_view(),
        name='k1api.accounts',
    ),
    url(
        r'^k1api/sources$',
        k1api.views.SourcesView.as_view(),
        name='k1api.sources',
    ),
    url(
        r'k1api/source_pixels$',
        k1api.views.SourcePixelsView.as_view(),
        name='k1api.source_pixels',
    ),
    url(
        r'^k1api/ga_accounts$',
        k1api.views.GAAccountsView.as_view(),
        name='k1api.ga_accounts',
    ),
    url(
        r'^k1api/r1_mapping$',
        k1api.views.R1MappingView.as_view(),
        name='k1api.r1_mapping',
    ),
    url(
        r'^k1api/outbrain/publishers_blacklist$',
        k1api.views.OutbrainPublishersBlacklistView.as_view(),
        name='k1api.outbrain_publishers_blacklist',
    ),
    url(
        r'^k1api/outbrain/marketer_id$',
        k1api.views.OutbrainMarketerIdView.as_view(),
        name='k1api.outbrain_marketer_id',
    ),
    url(
        r'^k1api/outbrain/sync_marketer$',
        k1api.views.OutbrainMarketerSyncView.as_view(),
        name='k1api.outbrain_marketer_sync',
    ),
    url(
        r'^k1api/facebook/accounts$',
        k1api.views.FacebookAccountsView.as_view(),
        name='k1api.facebook_accounts',
    ),
    url(
        r'^k1api/publisher_groups$',
        k1api.views.PublisherGroupsView.as_view(),
        name='k1api.publisher_groups',
    ),
    url(
        r'^k1api/publisher_groups_entries$',
        k1api.views.PublisherGroupsEntriesView.as_view(),
        name='k1api.publisher_groups_entries',
    ),
    url(
        r'^k1api/geolocations$',
        k1api.views.GeolocationsView.as_view(),
        name='k1api.geolocations',
    ),
]

# Crossvalidation Api
urlpatterns += [
    url(
        r'^api/crossvalidation$',
        etl.crossvalidation.views.crossvalidation,
        name='api.crossvalidation',
    )
]

# Source OAuth
urlpatterns += [
    url(
        r'^source/oauth/authorize/(?P<source_name>yahoo)',
        login_required(dash.views.views.oauth_authorize),
        name='source.oauth.authorize',
    ),
    url(
        r'^source/oauth/(?P<source_name>yahoo)',
        dash.views.views.oauth_redirect,  # mustn't have login_required because it's a redirect URI
        name='source.oauth.redirect'
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
    url(r'^', login_required(dash.views.views.index), name='index')
]
