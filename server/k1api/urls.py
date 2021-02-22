from django.conf.urls import url

from .views import accounts
from .views import ad_groups
from .views import ad_groups_sources
from .views import ad_groups_stats
from .views import bid_modifiers
from .views import content_ads
from .views import currency_exchange_rates
from .views import direct_deals
from .views import ga_accounts
from .views import geolocations
from .views import outbrain
from .views import r1_mapping
from .views import sources

urlpatterns = [
    url(r"^ad_groups$", ad_groups.AdGroupsView.as_view(), name="k1api.ad_groups"),
    url(r"^ad_groups/stats$", ad_groups_stats.AdGroupStatsView.as_view(), name="k1api.ad_groups.stats"),
    url(
        r"^ad_groups/conversion_stats$",
        ad_groups_stats.AdGroupConversionStatsView.as_view(),
        name="k1api.ad_groups.conversion_stats",
    ),
    url(
        r"^ad_groups/content_ad_publisher_stats$",
        ad_groups_stats.AdGroupContentAdPublisherStatsView.as_view(),
        name="k1api.ad_groups.content_ad_publisher_stats",
    ),
    url(r"^ad_groups/sources$", ad_groups_sources.AdGroupSourcesView.as_view(), name="k1api.ad_groups.sources"),
    url(
        r"^ad_groups/sources/blockers$",
        ad_groups_sources.AdGroupSourceBlockersView.as_view(),
        name="k1api.ad_groups.sources.blockers",
    ),
    url(r"^content_ads$", content_ads.ContentAdsView.as_view(), name="k1api.content_ads"),
    url(
        r"^content_ads/(?P<content_ad_id>\d+)$", content_ads.ContentAdsView.as_view(), name="k1api.content_ads_details"
    ),
    url(r"^content_ads/sources$", content_ads.ContentAdSourcesView.as_view(), name="k1api.content_ads.sources"),
    url(r"^accounts$", accounts.AccountsView.as_view(), name="k1api.accounts"),
    url(
        r"^accounts/bulk_marketer_parameters$",
        accounts.AccountsBulkMarketerParametersView.as_view(),
        name="k1api.accounts_bulk_marketer_parameters",
    ),
    url(
        r"^accounts/(?P<account_id>\d+)/marketer$",
        accounts.AccountMarketerView.as_view(),
        name="k1api.account_marketer",
    ),
    url(
        r"^accounts/(?P<account_id>\d+)/marketer_parameters$",
        accounts.AccountMarketerParametersView.as_view(),
        name="k1api.account_marketer_parameters",
    ),
    url(
        r"^accounts/(?P<account_id>\d+)/r1_pixel_mapping$",
        r1_mapping.R1PixelMappingView.as_view(),
        name="k1api.r1_pixel_mapping",
    ),
    url(
        r"^accounts/(?P<account_id>\d+)/r1_ad_group_mapping$",
        r1_mapping.R1AdGroupMappingView.as_view(),
        name="k1api.r1_ad_group_mapping",
    ),
    url(r"^sources$", sources.SourcesView.as_view(), name="k1api.sources"),
    url(r"^ga_accounts$", ga_accounts.GAAccountsView.as_view(), name="k1api.ga_accounts"),
    url(
        r"^outbrain/publishers_blacklist$",
        outbrain.OutbrainPublishersBlacklistView.as_view(),
        name="k1api.outbrain_publishers_blacklist",
    ),
    url(r"^outbrain/marketer_id$", outbrain.OutbrainMarketerIdView.as_view(), name="k1api.outbrain_marketer_id"),
    url(r"^outbrain/sync_marketer$", outbrain.OutbrainMarketerSyncView.as_view(), name="k1api.outbrain_marketer_sync"),
    url(r"^bidmodifiers$", bid_modifiers.BidModifiersView.as_view(), name="k1api.bidmodifiers"),
    url(r"^geolocations$", geolocations.GeolocationsView.as_view(), name="k1api.geolocations"),
    url(r"^direct_deals$", direct_deals.DirectDealsView.as_view(), name="k1api.directdeals"),
    url(
        "^currency_exchange_rates$",
        currency_exchange_rates.CurrencyExchangeRateView.as_view(),
        name="k1api.currency_exchange_rates",
    ),
]
