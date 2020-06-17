import django.views.defaults
import drf_yasg
import drf_yasg.views
import oauth2_provider.views
from django.conf import settings
from django.conf.urls import include
from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.generic import RedirectView
from django.views.generic import TemplateView
from rest_framework import permissions

import dash.features.contentupload.views
import dash.features.daily_stats.views
import dash.features.scheduled_reports.views
import dash.views.agency
import dash.views.audiences
import dash.views.breakdown
import dash.views.bulk_actions
import dash.views.callbacks
import dash.views.custom_report
import dash.views.grid
import dash.views.navigation
import dash.views.publishers
import dash.views.views
import etl.crossvalidation.views
import stats.constants
import zemauth.views
from restapi.common.views_base import CanUseRESTAPIPermission
from restapi.docs.swagger import RestAPISchemaGenerator
from zemauth.forms import AuthenticationForm

admin.site.login = login_required(admin.site.login)


# RedirectView.permanent will be False
# by default from Django 1.9 onwards,
# so set it to True to silence warnings
class AdminRedirectView(RedirectView):
    permanent = True


def oauth2_permission_wrap(view):
    def check(request, *args, **kwargs):
        if not request.user.has_perm("zemauth.can_manage_oauth2_apps"):
            return render(request, "oauth2_provider/contact_for_access.html")
        return view(request, *args, **kwargs)

    return login_required(check)


urlpatterns = []

if settings.ENABLE_DEBUG_TOOLBAR:
    import debug_toolbar

    urlpatterns += [url(r"^__debug__/", include(debug_toolbar.urls))]

if settings.DEBUG and settings.ENABLE_SILK:
    urlpatterns += [url(r"^silk/", include("silk.urls", namespace="silk"))]

urlpatterns += [
    url(
        r"^signin$",
        zemauth.views.login,
        {"authentication_form": AuthenticationForm, "template_name": "zemauth/signin.html"},
        name="signin",
    ),
    url(r"^signout$", auth_views.logout_then_login),
    url(
        r"^password_reset",
        zemauth.views.password_reset,
        {"template_name": "zemauth/password_reset.html"},
        name="password_reset",
    ),
    url(
        r"^set_password/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$",
        zemauth.views.set_password,
        {"template_name": "zemauth/set_password.html"},
        name="set_password",
    ),
    url(r"^admin$", AdminRedirectView.as_view(url="/admin/")),
    url(r"^admin/", admin.site.urls),
    url(r"^oauth2callback", zemauth.views.google_callback, name="zemauth.views.google_callback"),
    url(r"^supply_dash/", login_required(dash.views.views.supply_dash_redirect), name="supply_dash_redirect"),
    url(r"^user/", zemauth.views.UserView.as_view(), name="user_details"),
    url(
        r"^push_metrics/(?P<ad_group_id>\d+)/(?P<switch>(enable|disable))/$",
        login_required(dash.views.views.PushMetrics.as_view()),
        name="push_metrics",
    ),
]

# Oauth2 provider
oauth2_urlpatterns = [
    url(r"^authorize/$", oauth2_provider.views.AuthorizationView.as_view(), name="authorize"),
    url(r"^token/$", oauth2_provider.views.TokenView.as_view(), name="token"),
    url(r"^revoke_token/$", oauth2_provider.views.RevokeTokenView.as_view(), name="revoke-token"),
]

oauth2_urlpatterns += [
    url(r"^applications/$", oauth2_permission_wrap(oauth2_provider.views.ApplicationList.as_view()), name="list"),
    url(
        r"^applications/register/$",
        oauth2_permission_wrap(oauth2_provider.views.ApplicationRegistration.as_view()),
        name="register",
    ),
    url(
        r"^applications/(?P<pk>\d+)/$",
        oauth2_permission_wrap(oauth2_provider.views.ApplicationDetail.as_view()),
        name="detail",
    ),
    url(
        r"^applications/(?P<pk>\d+)/delete/$",
        oauth2_permission_wrap(oauth2_provider.views.ApplicationDelete.as_view()),
        name="delete",
    ),
    url(
        r"^applications/(?P<pk>\d+)/update/$",
        oauth2_permission_wrap(oauth2_provider.views.ApplicationUpdate.as_view()),
        name="update",
    ),
]

oauth2_urlpatterns += [
    url(
        r"^authorized_tokens/$",
        oauth2_permission_wrap(oauth2_provider.views.AuthorizedTokensListView.as_view()),
        name="authorized-token-list",
    ),
    url(
        r"^authorized_tokens/(?P<pk>\d+)/delete/$",
        oauth2_permission_wrap(oauth2_provider.views.AuthorizedTokenDeleteView.as_view()),
        name="authorized-token-delete",
    ),
]
urlpatterns += [url(r"^o/", include((oauth2_urlpatterns, "oauth2_provider"), namespace="oauth2_provider"))]

# K1 API
urlpatterns += [url(r"^k1api/", include("k1api.urls"))]

# REST API
urlpatterns += [url(r"^rest/", include("restapi.urls"))]

# Service APIs
urlpatterns += [url(r"^service/", include("serviceapi.urls"))]

# Custom integrations API
urlpatterns += [url(r"^integrations/businesswire/", include("integrations.bizwire.urls"))]

# Api
urlpatterns += [
    url(
        r"^api/grid/ad_groups/(?P<ad_group_id>\d+)/settings/$",
        login_required(dash.views.grid.AdGroupSettings.as_view()),
        name="grid_ad_group_settings",
    ),
    url(
        r"^api/grid/content_ads/(?P<content_ad_id>\d+)/settings/$",
        login_required(dash.views.grid.ContentAdSettings.as_view()),
        name="grid_content_ad_settings",
    ),
    url(
        r"^api/grid/content_ads/(?P<content_ad_id>\d+)/edit/$",
        login_required(dash.views.grid.ContentAdEdit.as_view()),
        name="grid_content_ad_edit",
    ),
    url(
        r"^api/grid/ad_groups/(?P<ad_group_id>\d+)/sources/(?P<source_id>\d+)/settings/$",
        login_required(dash.views.grid.AdGroupSourceSettings.as_view()),
        name="grid_ad_group_source_settings",
    ),
    url(
        r"^api/ad_groups/(?P<ad_group_id>\d+)/settings/state/$",
        login_required(dash.views.agency.AdGroupSettingsState.as_view()),
        name="ad_group_settings_state",
    ),
    url(
        r"^api/ad_groups/(?P<ad_group_id>\d+)/sources/$",
        login_required(dash.views.views.AdGroupSources.as_view()),
        name="ad_group_sources",
    ),
    url(
        r"^api/ad_groups/(?P<ad_group_id>\d+)/sources/(?P<source_id>\d+)/settings/$",
        login_required(dash.views.views.AdGroupSourceSettings.as_view()),
        name="ad_group_source_settings",
    ),
    url(
        r"^api/contentads/upload/csv/$",
        login_required(dash.features.contentupload.views.UploadCsv.as_view()),
        name="upload_csv",
    ),
    url(
        r"^api/contentads/upload/batch/$",
        login_required(dash.features.contentupload.views.UploadBatch.as_view()),
        name="upload_batch",
    ),
    url(
        r"^api/contentads/upload/(?P<batch_id>\d+)/status/$",
        login_required(dash.features.contentupload.views.UploadStatus.as_view()),
        name="upload_status",
    ),
    url(
        r"^api/contentads/upload/(?P<batch_id>\d+)/download/$",
        login_required(dash.features.contentupload.views.CandidatesDownload.as_view()),
        name="upload_candidates_download",
    ),
    url(
        r"^api/contentads/upload/(?P<batch_id>\d+)/save/$",
        login_required(dash.features.contentupload.views.UploadSave.as_view()),
        name="upload_save",
    ),
    url(
        r"^api/contentads/upload/(?P<batch_id>\d+)/cancel/$",
        login_required(dash.features.contentupload.views.UploadCancel.as_view()),
        name="upload_cancel",
    ),
    url(
        r"^api/contentads/upload" r"/(?P<batch_id>\d+)/candidate/(?:(?P<candidate_id>\d+)/)?$",
        login_required(dash.features.contentupload.views.Candidate.as_view()),
        name="upload_candidate",
    ),
    url(
        r"^api/contentads/upload" r"/(?P<batch_id>\d+)/candidate_update/(?:(?P<candidate_id>\d+)/)?$",
        login_required(dash.features.contentupload.views.CandidateUpdate.as_view()),
        name="upload_candidate_update",
    ),
    url(
        r"^api/ad_groups/(?P<ad_group_id>\d+)/contentads/edit/$",
        login_required(dash.views.bulk_actions.AdGroupContentAdEdit.as_view()),
        name="ad_group_content_ad_edit",
    ),
    url(
        r"^api/ad_groups/(?P<ad_group_id>\d+)/contentads/state/$",
        login_required(dash.views.bulk_actions.AdGroupContentAdState.as_view()),
        name="ad_group_content_ad_state",
    ),
    url(
        r"^api/ad_groups/(?P<ad_group_id>\d+)/contentads/csv/$",
        login_required(dash.views.bulk_actions.AdGroupContentAdCSV.as_view()),
        name="ad_group_content_ad_csv",
    ),
    url(
        r"^api/ad_groups/(?P<ad_group_id>\d+)/contentads/archive/$",
        login_required(dash.views.bulk_actions.AdGroupContentAdArchive.as_view()),
        name="ad_group_content_ad_archive",
    ),
    url(
        r"^api/ad_groups/(?P<ad_group_id>\d+)/contentads/restore/$",
        login_required(dash.views.bulk_actions.AdGroupContentAdRestore.as_view()),
        name="ad_group_content_ad_restore",
    ),
    url(
        r"^api/ad_groups/(?P<ad_group_id>\d+)/sources/state/$",
        login_required(dash.views.bulk_actions.AdGroupSourceState.as_view()),
        name="ad_group_source_state",
    ),
    url(
        r"^api/campaigns/(?P<campaign_id>\d+)/ad_groups/archive/$",
        login_required(dash.views.bulk_actions.CampaignAdGroupArchive.as_view()),
        name="campaign_ad_group_archive",
    ),
    url(
        r"^api/campaigns/(?P<campaign_id>\d+)/ad_groups/restore/$",
        login_required(dash.views.bulk_actions.CampaignAdGroupRestore.as_view()),
        name="campaign_ad_group_restore",
    ),
    url(
        r"^api/campaigns/(?P<campaign_id>\d+)/ad_groups/state/$",
        login_required(dash.views.bulk_actions.CampaignAdGroupState.as_view()),
        name="campaign_ad_group_state",
    ),
    url(
        r"^api/accounts/(?P<account_id>\d+)/campaigns/archive/$",
        login_required(dash.views.bulk_actions.AccountCampaignArchive.as_view()),
        name="account_campaign_archive",
    ),
    url(
        r"^api/accounts/(?P<account_id>\d+)/campaigns/restore/$",
        login_required(dash.views.bulk_actions.AccountCampaignRestore.as_view()),
        name="account_campaign_restore",
    ),
    url(
        r"^api/all_accounts/accounts/archive/$",
        login_required(dash.views.bulk_actions.AllAccountsAccountArchive.as_view()),
        name="all_accounts_account_archive",
    ),
    url(
        r"^api/all_accounts/accounts/restore/$",
        login_required(dash.views.bulk_actions.AllAccountsAccountRestore.as_view()),
        name="all_accounts_account_restore",
    ),
    url(
        r"^api/ad_groups/(?P<ad_group_id>\d+)/overview/$",
        login_required(dash.views.views.AdGroupOverview.as_view()),
        name="ad_group_overview",
    ),
    url(
        r"^api/accounts/overview/$",
        login_required(dash.views.views.AllAccountsOverview.as_view()),
        name="all_accounts_overview",
    ),
    url(r"^api/history/$", login_required(dash.views.agency.History.as_view()), name="history"),
    url(
        r"^api/ad_groups/(?P<ad_group_id>\d+)/contentads/daily_stats/$",
        login_required(dash.features.daily_stats.views.AdGroupContentAdsDailyStats.as_view()),
        name="ad_group_content_ads_daily_stats",
    ),
    url(
        r"^api/ad_groups/(?P<ad_group_id>\d+)/sources/daily_stats/$",
        login_required(dash.features.daily_stats.views.AdGroupSourcesDailyStats.as_view()),
        name="ad_group_sources_daily_stats",
    ),
    url(
        r"^api/ad_groups/(?P<ad_group_id>\d+)/publishers/daily_stats/$",
        login_required(dash.features.daily_stats.views.AdGroupPublishersDailyStats.as_view()),
        name="ad_group_publishers_daily_stats",
    ),
    url(
        r"^api/ad_groups/(?P<ad_group_id>\d+)/placements/daily_stats/$",
        login_required(dash.features.daily_stats.views.AdGroupPlacementsDailyStats.as_view()),
        name="ad_group_placements_daily_stats",
    ),
    url(
        r"^api/ad_groups/(?P<ad_group_id>\d+)/(?P<delivery_dimension>({}))/daily_stats/$".format(
            "|".join(stats.constants.get_top_level_delivery_dimensions())
        ),
        login_required(dash.features.daily_stats.views.AdGroupDeliveryDailyStats.as_view()),
        name="ad_group_delivery_daily_stats",
    ),
    url(
        r"^api/campaigns/(?P<campaign_id>\d+)/ad_groups/daily_stats/$",
        login_required(dash.features.daily_stats.views.CampaignAdGroupsDailyStats.as_view()),
        name="campaign_ad_groups_daily_stats",
    ),
    url(
        r"^api/campaigns/(?P<campaign_id>\d+)/sources/daily_stats/$",
        login_required(dash.features.daily_stats.views.CampaignSourcesDailyStats.as_view()),
        name="campaign_sources_daily_stats",
    ),
    url(
        r"^api/campaigns/(?P<campaign_id>\d+)/publishers/daily_stats/$",
        login_required(dash.features.daily_stats.views.CampaignPublishersDailyStats.as_view()),
        name="campaign_publishers_daily_stats",
    ),
    url(
        r"^api/campaigns/(?P<campaign_id>\d+)/placements/daily_stats/$",
        login_required(dash.features.daily_stats.views.CampaignPlacementsDailyStats.as_view()),
        name="campaign_placements_daily_stats",
    ),
    url(
        r"^api/campaigns/(?P<campaign_id>\d+)/(?P<delivery_dimension>({}))/daily_stats/$".format(
            "|".join(stats.constants.get_top_level_delivery_dimensions())
        ),
        login_required(dash.features.daily_stats.views.CampaignDeliveryDailyStats.as_view()),
        name="campaign_delivery_daily_stats",
    ),
    url(
        r"^api/accounts/(?P<account_id>\d+)/campaigns/daily_stats/$",
        login_required(dash.features.daily_stats.views.AccountCampaignsDailyStats.as_view()),
        name="account_campaigns_daily_stats",
    ),
    url(
        r"^api/accounts/(?P<account_id>\d+)/sources/daily_stats/$",
        login_required(dash.features.daily_stats.views.AccountSourcesDailyStats.as_view()),
        name="account_sources_daily_stats",
    ),
    url(
        r"^api/accounts/(?P<account_id>\d+)/placements/daily_stats/$",
        login_required(dash.features.daily_stats.views.AccountPlacementsDailyStats.as_view()),
        name="account_placements_daily_stats",
    ),
    url(
        r"^api/accounts/(?P<account_id>\d+)/publishers/daily_stats/$",
        login_required(dash.features.daily_stats.views.AccountPublishersDailyStats.as_view()),
        name="account_publishers_daily_stats",
    ),
    url(
        r"^api/accounts/(?P<account_id>\d+)/(?P<delivery_dimension>({}))/daily_stats/$".format(
            "|".join(stats.constants.get_top_level_delivery_dimensions())
        ),
        login_required(dash.features.daily_stats.views.AccountDeliveryDailyStats.as_view()),
        name="account_delivery_daily_stats",
    ),
    url(
        r"^api/all_accounts/accounts/daily_stats/$",
        login_required(dash.features.daily_stats.views.AllAccountsAccountsDailyStats.as_view()),
        name="accounts_accounts_daily_stats",
    ),
    url(
        r"^api/all_accounts/sources/daily_stats/$",
        login_required(dash.features.daily_stats.views.AllAccountsSourcesDailyStats.as_view()),
        name="accounts_sources_daily_stats",
    ),
    url(
        r"^api/all_accounts/publishers/daily_stats/$",
        login_required(dash.features.daily_stats.views.AllAccountsPublishersDailyStats.as_view()),
        name="accounts_publishers_daily_stats",
    ),
    url(
        r"^api/all_accounts/placements/daily_stats/$",
        login_required(dash.features.daily_stats.views.AllAccountsPlacementsDailyStats.as_view()),
        name="accounts_placements_daily_stats",
    ),
    url(
        r"^api/all_accounts/(?P<delivery_dimension>({}))/daily_stats/$".format(
            "|".join(stats.constants.get_top_level_delivery_dimensions())
        ),
        login_required(dash.features.daily_stats.views.AllAccountsDeliveryDailyStats.as_view()),
        name="accounts_delivery_daily_stats",
    ),
    url(
        r"^api/campaigns/(?P<campaign_id>\d+)/content-insights/$",
        login_required(dash.views.agency.CampaignContentInsights.as_view()),
    ),
    url(
        r"^api/accounts/(?P<account_id>\d+)/users/(?P<user_id>\d+)/(?P<action>\w+)$",
        login_required(dash.views.agency.AccountUserAction.as_view()),
        name="account_user_action",
    ),
    url(
        r"^api/accounts/(?P<account_id>\d+)/conversion_pixels/$",
        login_required(dash.views.agency.ConversionPixel.as_view()),
        name="account_conversion_pixels",
    ),
    url(
        r"^api/conversion_pixel/(?P<conversion_pixel_id>\d+)/$",
        login_required(dash.views.agency.ConversionPixel.as_view()),
        name="conversion_pixel",
    ),
    url(
        r"^api/accounts/(?P<account_id>\d+)/users/(?P<user_id>\d+)/$",
        login_required(dash.views.agency.AccountUsers.as_view()),
        name="account_users_manage",
    ),
    url(
        r"^api/accounts/(?P<account_id>\d+)/users/$",
        login_required(dash.views.agency.AccountUsers.as_view()),
        name="account_users",
    ),
    url(r"^api/accounts/(?P<account_id>\d+)/restore/$", login_required(dash.views.views.AccountRestore.as_view())),
    url(r"^api/campaigns/(?P<campaign_id>\d+)/restore/$", login_required(dash.views.views.CampaignRestore.as_view())),
    url(
        r"^api/campaigns/(?P<campaign_id>\d+)/overview/$",
        login_required(dash.views.views.CampaignOverview.as_view()),
        name="campaign_overview",
    ),
    url(r"^api/sources/$", login_required(dash.views.views.AvailableSources.as_view())),
    url(r"^api/agencies/$", login_required(dash.views.agency.Agencies.as_view()), name="agencies"),
    url(
        r"^api/ad_groups/(?P<ad_group_id>\d+)/restore/$",
        login_required(dash.views.views.AdGroupRestore.as_view()),
        name="ad_group_restore",
    ),
    url(
        r"^api/accounts/(?P<account_id>\d+)/overview/$",
        login_required(dash.views.views.AccountOverview.as_view()),
        name="account_overview",
    ),
    url(
        r"^api/(?P<level_>(ad_groups|campaigns|accounts))/(?P<id_>\d+)/nav/$",
        login_required(dash.views.navigation.NavigationDataView.as_view()),
        name="navigation",
    ),
    url(
        r"^api/all_accounts/nav/$",
        login_required(dash.views.navigation.NavigationAllAccountsDataView.as_view()),
        name="navigation_all_accounts",
    ),
    url(r"^api/nav/$", login_required(dash.views.navigation.NavigationTreeView.as_view()), name="navigation_tree"),
    url(
        r"^api/usesbcmv2/$",
        login_required(dash.views.navigation.UsesBCMV2View.as_view()),
        name="navigation_tree_usesbcmv2",
    ),
    url(r"^api/users/(?P<user_id>(\d+|current))/$", login_required(dash.views.views.User.as_view()), name="user"),
    url(
        r"^api/all_accounts/breakdown(?P<breakdown>(/\w+)+/?)$",
        login_required(dash.views.breakdown.AllAccountsBreakdown.as_view()),
        name="breakdown_all_accounts",
    ),
    url(
        r"^api/accounts/(?P<account_id>\d+)/breakdown(?P<breakdown>(/\w+)+/?)$",
        login_required(dash.views.breakdown.AccountBreakdown.as_view()),
        name="breakdown_accounts",
    ),
    url(
        r"^api/campaigns/(?P<campaign_id>\d+)/breakdown(?P<breakdown>(/\w+)+/?)$",
        login_required(dash.views.breakdown.CampaignBreakdown.as_view()),
        name="breakdown_campaigns",
    ),
    url(
        r"^api/ad_groups/(?P<ad_group_id>\d+)/breakdown(?P<breakdown>(/\w+)+/?)$",
        login_required(dash.views.breakdown.AdGroupBreakdown.as_view()),
        name="breakdown_ad_groups",
    ),
    url(r"^api/demov3/$", login_required(dash.views.views.Demo.as_view()), name="demov3"),
    url(
        r"^api/accounts/(?P<account_id>\d+)/audiences/(?P<audience_id>\d+)/archive/$",
        login_required(dash.views.audiences.AudienceArchive.as_view()),
        name="accounts_audience_archive",
    ),
    url(
        r"^api/accounts/(?P<account_id>\d+)/audiences/(?P<audience_id>\d+)/restore/$",
        login_required(dash.views.audiences.AudienceRestore.as_view()),
        name="accounts_audience_restore",
    ),
    url(
        r"^api/accounts/(?P<account_id>\d+)/audiences/(?P<audience_id>\d+)/$",
        login_required(dash.views.audiences.AudiencesView.as_view()),
        name="accounts_audience",
    ),
    url(
        r"^api/accounts/(?P<account_id>\d+)/audiences/$",
        login_required(dash.views.audiences.AudiencesView.as_view()),
        name="accounts_audiences",
    ),
    url(
        r"^api/publishers/targeting/$",
        login_required(dash.views.publishers.PublisherTargeting.as_view()),
        name="publisher_targeting",
    ),
    url(
        r"^api/publisher_groups/(?P<publisher_group_id>\d+)/download/$",
        login_required(dash.views.publishers.PublisherGroupsDownload.as_view()),
        name="download_publisher_groups",
    ),
    url(
        r"^api/publisher_groups/$",
        login_required(dash.views.publishers.PublisherGroups.as_view()),
        name="publisher_groups",
    ),
    url(
        r"^api/publisher_groups/upload/$",
        login_required(dash.views.publishers.PublisherGroupsUpload.as_view()),
        name="publisher_groups_upload",
    ),
    url(
        r"^api/custom_report_download/$",
        login_required(dash.views.custom_report.CustomReportDownload.as_view()),
        name="custom_report_download",
    ),
    url(
        r"^api/publisher_groups/download/example/$",
        login_required(dash.views.publishers.PublisherGroupsExampleDownload.as_view()),
        name="publisher_groups_example",
    ),
    url(
        r"^api/publisher_groups/errors/(?P<csv_key>[a-zA-Z0-9]+)$",
        login_required(dash.views.publishers.PublisherGroupsUpload.as_view()),
        name="publisher_groups_upload",
    ),
    url(
        r"^api/scheduled_reports/$",
        login_required(dash.features.scheduled_reports.views.ScheduledReports.as_view()),
        name="scheduled_reports",
    ),
    url(
        r"^api/scheduled_reports/(?P<scheduled_report_id>\d+)/$",
        login_required(dash.features.scheduled_reports.views.ScheduledReportsDelete.as_view()),
        name="scheduled_reports_delete",
    ),
]

# Lambdas
urlpatterns += [
    url(r"^api/callbacks/content-upload/$", dash.views.callbacks.content_upload, name="callbacks.content_upload")
]

# Crossvalidation Api
urlpatterns += [url(r"^api/crossvalidation$", etl.crossvalidation.views.crossvalidation, name="api.crossvalidation")]

# Source OAuth
urlpatterns += [
    url(
        r"^source/oauth/authorize/(?P<source_name>yahoo)$",
        login_required(dash.views.views.oauth_authorize),
        name="source.oauth.authorize",
    ),
    url(
        r"^source/oauth/(?P<source_name>yahoo)$",
        dash.views.views.oauth_redirect,  # mustn't have login_required because it's a redirect URI
        name="source.oauth.redirect",
    ),
]

# Health Check
urlpatterns += [url(r"^healthcheck$", dash.views.views.healthcheck, name="healthcheck")]

# Swagger API
schema_view = drf_yasg.views.get_schema_view(
    drf_yasg.openapi.Info(
        title="Zemanta One API",
        default_version="v1",
        contact=drf_yasg.openapi.Contact(email="api-support@zemanta.com"),
        description="Find more info here http://dev.zemanta.com/one/api/ \n Note that this is a live production API and calls will affect your account(s)",
    ),
    public=False,
    permission_classes=(permissions.IsAuthenticated, CanUseRESTAPIPermission),
    generator_class=RestAPISchemaGenerator,
)
schema_view_internal = drf_yasg.views.get_schema_view(
    drf_yasg.openapi.Info(title="Internal API", default_version="v1"),
    public=False,
    permission_classes=(permissions.IsAdminUser,),
)
urlpatterns += [
    url(
        r"^swagger_internal/$",
        login_required(schema_view_internal.with_ui("swagger", cache_timeout=0)),
        name="schema-swagger-internal-ui",
    ),
    url(r"^swagger/$", login_required(schema_view.with_ui("swagger", cache_timeout=0)), name="schema-swagger-ui"),
]

# TOS
urlpatterns += [url(r"^tos/$", TemplateView.as_view(template_name="tos.html"))]

urlpatterns += [
    url(r"^api/", django.views.defaults.page_not_found, {"exception": None}),
    url(r"^", login_required(dash.views.views.index), name="index"),
]
