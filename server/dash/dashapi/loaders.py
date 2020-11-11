import calendar
import collections

from django.db.models.query import QuerySet
from django.urls import reverse
from django.utils.functional import cached_property

import automation.campaignstop
import core.features.ad_review
import core.features.bcm.calculations
import core.features.bid_modifiers.constants
import core.features.entity_status
import core.features.multicurrency
import stats.constants
import stats.helpers
from core.features import bid_modifiers
from dash import constants
from dash import models
from dash import publisher_helpers
from dash.dashapi import data_helper
from dash.views import helpers as view_helpers
from utils import outbrain_internal_helper
from utils import zlogging
from zemauth.models import User as ZemUser

logger = zlogging.getLogger(__name__)

"""
Objects that load necessary related objects. All try to execute queries as seldom as possible.

The state of loaders should be immutable, if you want to have a different set of base objects
you need to create a new instance of a loader.

Notes on implementation:
  - always compare a queryset with None, otherwise it executes a query on a database.
  - remember to select_related for objects that you will need
  - settings_map properties should return a default dict that returns default field values
  - same for status_map - should return default value
"""

OUTBRAIN_SOURCE_ID = 3

# In case the target_dimension is publisher_id or
# placement_id or is a delivery dimension we can't
# fetch the objects count from RDS. For this dimensions
# objects count is fetched from Redshift.
DEFAULT_OBJS_COUNT = 0


def get_loader_for_dimension(target_dimension, level):
    if target_dimension == "account_id":
        return AccountsLoader
    elif target_dimension == "campaign_id":
        return CampaignsLoader
    elif target_dimension == "ad_group_id":
        return AdGroupsLoader
    elif target_dimension == "content_ad_id":
        if level == constants.Level.AD_GROUPS:
            return ContentAdsOnAdGroupLevelLoader
        return ContentAdsLoader
    elif target_dimension == "source_id":
        if level == constants.Level.AD_GROUPS:
            return AdGroupSourcesLoader
        return SourcesLoader
    elif target_dimension == "publisher_id":
        if level == constants.Level.AD_GROUPS:
            return PublisherBidModifierLoader
        return PublisherBlacklistLoader
    elif target_dimension == "placement_id":
        if level == constants.Level.AD_GROUPS:
            return PlacementBidModifierLoader
        return PlacementLoader
    elif stats.constants.is_top_level_delivery_dimension(target_dimension):
        return DeliveryLoader
    return None


class Loader(object):
    def __init__(self, objs_qs, start_date=None, end_date=None, include_entity_tags=None):
        self.objs_qs = objs_qs

        self._start_date = start_date
        self._end_date = end_date
        self._include_entity_tags = include_entity_tags if include_entity_tags is not None else False

    @classmethod
    def _get_obj_id(cls, obj):
        return obj.pk

    @cached_property
    def objs_map(self):
        return {self._get_obj_id(x): x for x in self.objs_qs}

    @cached_property
    def objs_ids(self):
        return list(self.objs_map.keys())

    @cached_property
    def objs_count(self):
        return self.objs_qs.count()

    @property
    def start_date(self):
        if self._start_date is None:
            raise Exception("Start date not set")
        return self._start_date

    @property
    def end_date(self):
        if self._end_date is None:
            raise Exception("End date not set")
        return self._end_date

    @property
    def include_entity_tags(self):
        return self._include_entity_tags


class AccountsLoader(Loader):
    def __init__(self, accounts_qs, filtered_sources_qs, user, **kwargs):
        accounts_qs = accounts_qs.select_related("agency")

        super(AccountsLoader, self).__init__(accounts_qs, **kwargs)
        self.filtered_sources_qs = filtered_sources_qs
        self.user = user

    @classmethod
    def from_constraints(cls, user, constraints, **kwargs):
        return cls(
            constraints["allowed_accounts"],
            constraints["filtered_sources"],
            user,
            start_date=constraints.get("date__gte"),
            end_date=constraints.get("date__lte"),
            include_entity_tags=constraints.get("include_entity_tags"),
        )

    @cached_property
    def settings_map(self):
        settings_qs = models.AccountSettings.objects.filter(account_id__in=self.objs_ids).group_current_settings()

        # workaround because select_related is currently malfunctioned on models that inherit histroymixin
        # - it doesn't do what its supposed to do
        user_ids = set(x.default_account_manager_id for x in settings_qs)
        user_ids |= set(x.default_sales_representative_id for x in settings_qs)
        user_ids |= set(x.default_cs_representative_id for x in settings_qs)
        user_ids |= set(x.ob_sales_representative_id for x in settings_qs)
        user_ids |= set(x.ob_account_manager_id for x in settings_qs)
        user_map = {x.id: x for x in ZemUser.objects.filter(pk__in=user_ids)}

        settings_obj_map = {x.account_id: x for x in settings_qs}
        status_map = self._get_status_map()

        settings_map = {}
        for account_id in self.objs_ids:
            settings = settings_obj_map.get(account_id)

            settings_dict = {
                "status": status_map[account_id],
                "archived": False,
                "default_account_manager": None,
                "default_sales_representative": None,
                "default_cs_representative": None,
                "ob_sales_representative": None,
                "ob_account_manager": None,
                "account_type": constants.AccountType.get_text(constants.AccountType.UNKNOWN),
                "settings_id": None,  # for debugging purposes, isn't used in production code
                "salesforce_url": "",
            }
            if settings is not None:
                settings_dict.update(
                    {
                        "archived": settings.archived,
                        "account_type": constants.AccountType.get_text(settings.account_type),
                        "settings_id": settings.id,
                        "default_account_manager": view_helpers.get_user_full_name_or_email(
                            user_map.get(settings.default_account_manager_id), default_value=None
                        ),
                        "default_sales_representative": view_helpers.get_user_full_name_or_email(
                            user_map.get(settings.default_sales_representative_id), default_value=None
                        ),
                        "default_cs_representative": view_helpers.get_user_full_name_or_email(
                            user_map.get(settings.default_cs_representative_id), default_value=None
                        ),
                        "ob_sales_representative": view_helpers.get_user_full_name_or_email(
                            user_map.get(settings.ob_sales_representative_id), default_value=None
                        ),
                        "ob_account_manager": view_helpers.get_user_full_name_or_email(
                            user_map.get(settings.ob_account_manager_id), default_value=None
                        ),
                        "salesforce_url": settings.salesforce_url or "",
                    }
                )
            settings_map[account_id] = settings_dict

        return settings_map

    def _get_status_map(self):
        return core.features.entity_status.get_accounts_statuses_cached(self.objs_ids)

    @cached_property
    def refunds_map(self):
        refunds_map = {}
        for refund in self._refunds:
            row = refunds_map.get(refund.account_id)
            if not row:
                row = collections.defaultdict(int)
            refund_amounts = self._calculate_refund_splits(refund)
            stats.helpers.update_with_refunds(row, refund_amounts)
            refunds_map[refund.account_id] = dict(row)
        return refunds_map

    @cached_property
    def refunds_totals(self):
        if not self._refunds:
            return {}

        totals = collections.defaultdict(int)
        for refund in self._refunds:
            refund_amounts = self._calculate_refund_splits(refund)
            stats.helpers.update_with_refunds(totals, refund_amounts)
        return dict(totals)

    @cached_property
    def _refunds(self):
        return models.RefundLineItem.objects.filter(
            account_id__in=self.objs_ids,
            start_date__gte=self.start_date.replace(day=1),
            end_date__lte=self.end_date.replace(day=calendar.monthrange(self.end_date.year, self.end_date.month)[1]),
        ).select_related("credit")

    def _calculate_refund_splits(self, refund):
        currency_exchange_rate = self._refund_exchange_rate(refund)
        return refund.calculate_cost_splits(currency_exchange_rate)

    def _refund_exchange_rate(self, refund):
        view_currency = stats.helpers.get_report_currency(self.user, [account for account in self.objs_map.values()])
        view_currency_exchange_rate = core.features.multicurrency.get_exchange_rate(refund.start_date, view_currency)
        account_currency_exchange_rate = core.features.multicurrency.get_exchange_rate(
            refund.start_date, refund.account.currency
        )
        return view_currency_exchange_rate / account_currency_exchange_rate


class CampaignsLoader(Loader):
    def __init__(self, campaigns_qs, filtered_sources_qs, user, **kwargs):
        super(CampaignsLoader, self).__init__(campaigns_qs.select_related("account"), **kwargs)

        self.filtered_sources_qs = filtered_sources_qs
        self.user = user

    @classmethod
    def from_constraints(cls, user, constraints, **kwargs):
        return cls(
            constraints["allowed_campaigns"],
            constraints["filtered_sources"],
            user,
            start_date=constraints.get("date__gte"),
            end_date=constraints.get("date__lte"),
            include_entity_tags=constraints.get("include_entity_tags"),
        )

    @cached_property
    def settings_map(self):
        settings_qs = (
            models.CampaignSettings.objects.filter(campaign_id__in=self.objs_ids)
            .group_current_settings()
            .select_related("campaign_manager")
        )
        settings_obj_map = {x.campaign_id: x for x in settings_qs}
        status_map = self._get_status_map()
        settings_map = {}

        for campaign_id in self.objs_ids:
            settings = settings_obj_map.get(campaign_id)

            settings_dict = {
                "status": status_map[campaign_id],
                "archived": False,
                "campaign_manager": None,
                "settings_id": None,  # for debugging purposes, get removed
            }
            if settings is not None:
                settings_dict.update(
                    {
                        "archived": settings.archived,
                        "campaign_manager": view_helpers.get_user_full_name_or_email(
                            settings.campaign_manager, default_value=None
                        ),
                        "settings_id": settings.id,
                    }
                )
            settings_map[campaign_id] = settings_dict

        return settings_map

    def _get_status_map(self):
        campaign_ids_state = (
            models.AdGroup.objects.filter(campaign__in=self.objs_ids)
            .values_list("campaign_id", "settings__state")
            .order_by()
        )  # removes default ordering to speed up the query
        campaignstop_states = automation.campaignstop.get_campaignstop_states(
            models.Campaign.objects.filter(id__in=self.objs_ids)
        )

        status_map = collections.defaultdict(lambda: constants.AdGroupRunningStatus.INACTIVE)
        for campaign_id, state in campaign_ids_state:
            if state == constants.AdGroupRunningStatus.ACTIVE and campaignstop_states.get(campaign_id, {}).get(
                "allowed_to_run", False
            ):
                status_map[campaign_id] = state

        return status_map

    @cached_property
    def refunds_totals(self):
        if not self._refunds:
            return {}

        totals = collections.defaultdict(int)
        for refund in self._refunds:
            refund_amounts = self._calculate_refund_splits(refund)
            stats.helpers.update_with_refunds(totals, refund_amounts)

        return dict(totals)

    @cached_property
    def _refunds(self):
        return models.RefundLineItem.objects.filter(
            account__in=models.Campaign.objects.filter(id__in=self.objs_ids).values_list("account_id", flat=True),
            start_date__gte=self.start_date.replace(day=1),
            end_date__lte=self.end_date.replace(day=calendar.monthrange(self.end_date.year, self.end_date.month)[1]),
        ).select_related("credit")

    def _calculate_refund_splits(self, refund):
        currency_exchange_rate = 1  # campaign view always displays local currency
        return refund.calculate_cost_splits(currency_exchange_rate)


class AdGroupsLoader(Loader):
    def __init__(self, ad_groups_qs, filtered_sources_qs, user, **kwargs):
        super(AdGroupsLoader, self).__init__(ad_groups_qs.select_related("campaign__account", "settings"), **kwargs)
        self.filtered_sources_qs = filtered_sources_qs
        self.user = user

    @classmethod
    def from_constraints(cls, user, constraints, **kwargs):
        return cls(
            constraints["allowed_ad_groups"],
            constraints["filtered_sources"],
            user,
            start_date=constraints.get("date__gte"),
            end_date=constraints.get("date__lte"),
            include_entity_tags=constraints.get("include_entity_tags"),
        )

    @cached_property
    def settings_map(self):
        settings_map = {}
        status_map = self._get_status_map()
        for ad_group_id, ad_group in self.objs_map.items():
            settings_map[ad_group_id] = {
                "archived": ad_group.settings.archived,
                "status": status_map[ad_group_id],
                "state": ad_group.settings.state,
                "settings_id": ad_group.settings.id,
            }

        return settings_map

    def _get_status_map(self):
        campaignstop_states = automation.campaignstop.get_campaignstop_states(list(self._campaign_ad_groups_map.keys()))
        status_map = collections.defaultdict(lambda: constants.AdGroupRunningStatus.INACTIVE)
        for ad_group_id, ad_group in self.objs_map.items():
            if ad_group.settings.state == constants.AdGroupRunningStatus.ACTIVE and campaignstop_states.get(
                ad_group.campaign_id, {}
            ).get("allowed_to_run", False):
                status_map[ad_group_id] = ad_group.settings.state

        return status_map

    @cached_property
    def base_level_settings_map(self):
        campaign_ad_groups = self._campaign_ad_groups_map

        settings_map = {}
        for campaign, ad_groups in list(campaign_ad_groups.items()):
            campaign_has_available_budget = data_helper.campaign_has_available_budget(campaign)

            for ad_group in ad_groups:
                settings_map[ad_group.id] = {"campaign_has_available_budget": campaign_has_available_budget}

        return settings_map

    @cached_property
    def _campaign_ad_groups_map(self):
        campaign_ad_groups = collections.defaultdict(list)
        for _, ad_group in self.objs_map.items():
            campaign_ad_groups[ad_group.campaign].append(ad_group)

        return campaign_ad_groups


class ContentAdsLoader(Loader):
    def __init__(self, content_ads_qs, filtered_sources_qs, user, **kwargs):
        super(ContentAdsLoader, self).__init__(
            content_ads_qs.select_related("batch", "ad_group__campaign__account"), **kwargs
        )
        self.filtered_sources_qs = filtered_sources_qs
        self.user = user

    @classmethod
    def from_constraints(cls, user, constraints, **kwargs):
        return cls(
            constraints["allowed_content_ads"],
            constraints["filtered_sources"],
            user,
            start_date=constraints.get("date__gte"),
            end_date=constraints.get("date__lte"),
        )

    @cached_property
    def batch_map(self):
        return {x.pk: x.batch for x in self.objs_qs}

    @cached_property
    def ad_group_loader(self):
        ad_groups_qs = models.AdGroup.objects.filter(pk__in=set(x.ad_group_id for x in self.objs_qs))

        return AdGroupsLoader(ad_groups_qs, self.filtered_sources_qs, self.user)

    @cached_property
    def ad_group_map(self):
        ad_group_map = {}
        for content_ad_id, content_ad in self.objs_map.items():
            ad_group_map[content_ad_id] = self.ad_group_loader.objs_map[content_ad.ad_group_id]
        return ad_group_map

    @cached_property
    def status_map(self):
        status_map = {}
        for content_ad_id, content_ad in self.objs_map.items():
            content_ad_sources = self.content_ads_sources_map[content_ad_id]
            if (
                any([x.state == constants.ContentAdSourceState.ACTIVE for x in content_ad_sources])
                and self.ad_group_loader.settings_map[content_ad.ad_group_id]["status"]
                == constants.AdGroupRunningStatus.ACTIVE
            ):
                status_map[content_ad_id] = constants.ContentAdSourceState.ACTIVE
            else:
                status_map[content_ad_id] = constants.ContentAdSourceState.INACTIVE
        return status_map

    @cached_property
    def per_source_status_map(self):
        per_source_map = collections.defaultdict(dict)
        sources = {x.id: x.name for x in self.filtered_sources_qs}
        source_map = self._get_per_ad_group_source_map()
        submission_status_map = core.features.ad_review.get_per_source_submission_status_map(self.objs_qs)

        for content_ad_id, content_ad in self.objs_map.items():
            for content_ad_source in self.content_ads_sources_map[content_ad_id]:
                source_id = content_ad_source.source_id
                content_ad_source_submission_status = submission_status_map.get(content_ad_id, {}).get(source_id, {})

                source_status = source_map[content_ad.ad_group_id][source_id]["state"]
                if source_status is None:
                    source_status = constants.AdGroupSourceSettingsState.INACTIVE

                source_link = self._get_source_link(
                    content_ad, source_map[content_ad.ad_group_id][source_id]["content_ad_submission_policy"]
                )
                content_ad_source_dict = {
                    "source_id": source_id,
                    "source_name": sources.get(source_id),
                    "source_status": source_status,
                    "submission_status": content_ad_source_submission_status.get("submission_status"),
                    "submission_errors": content_ad_source_submission_status.get("submission_errors"),
                }
                if source_link:
                    content_ad_source_dict["source_link"] = source_link
                per_source_map[content_ad_id][content_ad_source.source_id] = content_ad_source_dict

        return per_source_map

    def _get_per_ad_group_source_map(self):
        ad_group_sources_settings = (
            models.AdGroupSourceSettings.objects.filter(
                ad_group_source__ad_group_id__in=set(x.ad_group_id for x in self.objs_qs)
            )
            .group_current_settings()
            .values_list(
                "ad_group_source__ad_group_id",
                "ad_group_source__source_id",
                "state",
                "ad_group_source__source__content_ad_submission_policy",
            )
        )

        settings_map = collections.defaultdict(dict)
        for ad_group_id, source_id, state, content_ad_submission_policy in ad_group_sources_settings:
            settings_map[ad_group_id][source_id] = {
                "state": state,
                "content_ad_submission_policy": content_ad_submission_policy,
            }
        return settings_map

    def _get_source_link(self, content_ad, content_ad_submission_policy):
        if self.user.has_perm("zemauth.can_see_amplify_review_link") and self._should_use_amplify_review(
            content_ad, content_ad_submission_policy
        ):
            return "{}?ad_group_id={}&source_id={}".format(
                reverse("supply_dash_redirect"), content_ad.ad_group.id, OUTBRAIN_SOURCE_ID
            )
        return None

    def _should_use_amplify_review(self, content_ad, content_ad_submission_policy):
        return (
            content_ad_submission_policy == constants.SourceSubmissionPolicy.AUTOMATIC_WITH_AMPLIFY_APPROVAL
            and content_ad.amplify_review
            and content_ad.id in self.amplify_reviews_map
        )

    @cached_property
    def amplify_reviews_map(self):
        qs = models.ContentAdSource.objects.filter(content_ad_id__in=self.objs_ids, source_id=OUTBRAIN_SOURCE_ID)

        amplify_reviews_map = {}
        for content_ad_source in qs:
            amplify_reviews_map[content_ad_source.content_ad_id] = content_ad_source
        return amplify_reviews_map

    @cached_property
    def content_ads_sources_map(self):
        qs = models.ContentAdSource.objects.filter(content_ad_id__in=self.objs_ids).filter_by_sources(
            self.filtered_sources_qs
        )

        content_ads_sources_map = collections.defaultdict(list)
        for content_ad_source in qs:
            content_ads_sources_map[content_ad_source.content_ad_id].append(content_ad_source)

        return content_ads_sources_map

    @cached_property
    def amplify_internal_ids_map(self):
        content_ad_ids = []
        ob_external_ids = []
        for content_ad_id, amplify_content_ad_source in self.amplify_reviews_map.items():
            ob_external_id = amplify_content_ad_source.source_content_ad_id
            if not ob_external_id:
                continue
            content_ad_ids.append(content_ad_id)
            ob_external_ids.append(ob_external_id)
        try:
            ob_internal_ids = outbrain_internal_helper.to_internal_ids(ob_external_ids)
            return dict(zip(content_ad_ids, ob_internal_ids))
        except Exception:
            return {}


class ContentAdsOnAdGroupLevelLoader(ContentAdsLoader):
    def __init__(self, ad_group, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ad_group = ad_group

    @classmethod
    def from_constraints(cls, user, constraints, **kwargs):
        return cls(
            constraints["ad_group"],
            constraints["allowed_content_ads"],
            constraints["filtered_sources"],
            user,
            start_date=constraints.get("date__gte"),
            end_date=constraints.get("date__lte"),
        )

    @cached_property
    def bid_modifiers_by_ad(self):
        bid_modifiers_qs = bid_modifiers.BidModifier.objects.filter(
            ad_group=self.ad_group, type=bid_modifiers.BidModifierType.AD, target__in=map(str, self.objs_ids)
        )
        return {int(x.target): x for x in bid_modifiers_qs}


class PublisherBlacklistLoader(Loader):
    def __init__(
        self, blacklist_qs, whitelist_qs, publisher_group_targeting, filtered_sources_qs, user, account=None, **kwargs
    ):
        super(PublisherBlacklistLoader, self).__init__(blacklist_qs | whitelist_qs, **kwargs)
        self.filtered_sources_qs = filtered_sources_qs.select_related("source_type")
        self.user = user

        self.publisher_group_targeting = publisher_group_targeting
        self.whitelist_qs = whitelist_qs
        self.blacklist_qs = blacklist_qs
        self.account = account

        self.default = {"status": constants.PublisherTargetingStatus.UNLISTED}

        self.has_bid_modifiers = False

    @classmethod
    def _get_obj_id(cls, obj):
        return publisher_helpers.create_publisher_id(obj.publisher, obj.source_id)

    @cached_property
    def objs_count(self):
        return DEFAULT_OBJS_COUNT

    @classmethod
    def from_constraints(cls, user, constraints, **kwargs):
        return cls(
            constraints["publisher_blacklist"],
            constraints["publisher_whitelist"],
            constraints["publisher_group_targeting"],
            constraints["filtered_sources"],
            user,
            start_date=constraints.get("date__gte"),
            end_date=constraints.get("date__lte"),
            account=constraints.get("account"),
        )

    @cached_property
    def publisher_group_entry_map(self):
        return publisher_helpers.PublisherIdLookupMap(self.blacklist_qs, self.whitelist_qs)

    def _find_blacklisted_status_for_level(self, row, level, publisher_group_entry):
        targeting = self.publisher_group_targeting[level].get(
            row.get(level + "_id"),  # for reports there can be multiple entities per level
            self.publisher_group_targeting[level],  # default is used for grid
        )

        if publisher_group_entry.publisher_group_id in targeting["included"]:
            return {"status": constants.PublisherTargetingStatus.WHITELISTED}

        if publisher_group_entry.publisher_group_id in targeting["excluded"]:
            return {"status": constants.PublisherTargetingStatus.BLACKLISTED}

        return None

    def _find_blacklisted_status(self, row, publisher_group_entry):
        status = self._find_blacklisted_status_for_level(row, "ad_group", publisher_group_entry)
        if status is not None:
            status["blacklisted_level"] = constants.PublisherBlacklistLevel.ADGROUP
            return status

        status = self._find_blacklisted_status_for_level(row, "campaign", publisher_group_entry)
        if status is not None:
            status["blacklisted_level"] = constants.PublisherBlacklistLevel.CAMPAIGN
            return status

        status = self._find_blacklisted_status_for_level(row, "account", publisher_group_entry)
        if status is not None:
            status["blacklisted_level"] = constants.PublisherBlacklistLevel.ACCOUNT
            return status

        if publisher_group_entry.publisher_group_id in self.publisher_group_targeting["global"]["excluded"]:
            return {
                "status": constants.PublisherTargetingStatus.BLACKLISTED,
                "blacklisted_level": constants.PublisherBlacklistLevel.GLOBAL,
            }

        return self.default

    def find_blacklisted_status_by_subdomain(self, row):
        publisher_group_entry = self.publisher_group_entry_map[self._get_publisher_group_entry_map_key(row)]
        if publisher_group_entry is not None:
            return self._find_blacklisted_status(row, publisher_group_entry)

        # nothing matched, return the default value
        return self.default

    def _get_publisher_group_entry_map_key(self, row):
        return row["publisher_id"]

    @cached_property
    def source_map(self):
        return {x.id: x for x in self.filtered_sources_qs}


class SourcesLoader(Loader):
    @classmethod
    def from_constraints(cls, user, constraints, **kwargs):
        return cls(
            constraints["filtered_sources"],
            start_date=constraints.get("date__gte"),
            end_date=constraints.get("date__lte"),
            include_entity_tags=constraints.get("include_entity_tags"),
        )

    @cached_property
    def settings_map(self):
        # return empty settings - compatibility with AdGroupSourcesLoader
        return {x: {} for x in self.objs_ids}

    @cached_property
    def totals(self):
        return {}


class AdGroupSourcesLoader(Loader):
    def __init__(self, sources_qs, ad_group, user, **kwargs):
        super(AdGroupSourcesLoader, self).__init__(sources_qs.select_related("source_type"), **kwargs)

        self.base_objects = [ad_group]
        self.ad_group = ad_group
        self.ad_group_settings = ad_group.get_current_settings()
        self.campaign_settings = ad_group.campaign.get_current_settings()
        self.user = user

    @classmethod
    def from_constraints(cls, user, constraints, **kwargs):
        return cls(
            constraints["filtered_sources"],
            constraints["ad_group"],
            user,
            start_date=constraints.get("date__gte"),
            end_date=constraints.get("date__lte"),
        )

    @cached_property
    def settings_map(self):
        result = {}
        ad_group_sources_map = {x.source_id: x for x in self._active_ad_groups_sources_qs}

        for source_id, source in list(self.objs_map.items()):
            ad_group_source = ad_group_sources_map[source_id]
            source_settings = self._ad_group_source_settings_map[source_id]

            editable_fields = view_helpers.get_editable_fields(
                self.user,
                ad_group_source.ad_group,
                ad_group_source,
                self.ad_group_settings,
                source_settings,
                self.campaign_settings,
                self._allowed_sources,
            )

            if editable_fields.get("status_setting"):
                editable_fields["state"] = editable_fields.pop("status_setting")

            state = source_settings.state if source_settings else constants.AdGroupSourceSettingsState.INACTIVE
            result[source_id] = {
                "state": state,
                "status": data_helper.get_source_status(ad_group_source, state, self.ad_group_settings.state),
                "bid_cpc": source_settings.cpc_cc if source_settings else None,
                "local_bid_cpc": source_settings.local_cpc_cc if source_settings else None,
                "bid_cpm": source_settings.cpm if source_settings else None,
                "local_bid_cpm": source_settings.local_cpm if source_settings else None,
                "daily_budget": source_settings.daily_budget_cc if source_settings else None,
                "local_daily_budget": source_settings.local_daily_budget_cc if source_settings else None,
                "supply_dash_url": ad_group_source.get_supply_dash_url(),
                "supply_dash_disabled_message": view_helpers.get_source_supply_dash_disabled_message(
                    ad_group_source, source
                ),
                "editable_fields": editable_fields,
                "notifications": data_helper.get_ad_group_source_notification(
                    ad_group_source, self.ad_group_settings, source_settings
                ),
            }

            # MVP for all-RTB-sources-as-one
            if self.ad_group_settings.b1_sources_group_enabled and source.source_type.type == constants.SourceType.B1:
                # daily_budget
                result[source_id]["daily_budget"] = None
                result[source_id]["local_daily_budget"] = None
                result[source_id]["editable_fields"]["daily_budget"]["enabled"] = False
                result[source_id]["editable_fields"]["daily_budget"]["message"] = None
                # bid_cpc
                result[source_id]["bid_cpc"] = None
                result[source_id]["local_bid_cpc"] = None
                result[source_id]["editable_fields"]["bid_cpc"]["enabled"] = False
                result[source_id]["editable_fields"]["bid_cpc"]["message"] = None
                # bid_cpm
                result[source_id]["bid_cpm"] = None
                result[source_id]["local_bid_cpm"] = None
                result[source_id]["editable_fields"]["bid_cpm"]["enabled"] = False
                result[source_id]["editable_fields"]["bid_cpm"]["message"] = None
                if (
                    self.ad_group_settings.b1_sources_group_state == constants.AdGroupSourceSettingsState.INACTIVE
                    and result[source_id]["status"] == constants.AdGroupSourceSettingsState.ACTIVE
                ):
                    result[source_id]["status"] = constants.AdGroupSourceSettingsState.INACTIVE
                    result[source_id]["notifications"] = {
                        "message": "This media source is enabled but will not run until you enable RTB Sources.",
                        "important": True,
                    }

        return result

    @cached_property
    def _allowed_sources(self):
        return self.ad_group.campaign.account.allowed_sources.all().values_list("pk", flat=True)

    @cached_property
    def _active_ad_groups_sources_qs(self):
        if isinstance(self.base_objects, QuerySet):
            modelcls = self.base_objects.model
        else:
            modelcls = type(self.base_objects[0])

        return view_helpers.get_active_ad_group_sources(modelcls, self.base_objects)

    @cached_property
    def _ad_group_source_settings_map(self):
        source_settings = (
            models.AdGroupSourceSettings.objects.filter(
                ad_group_source_id__in=[x.pk for x in self._active_ad_groups_sources_qs]
            )
            .group_current_settings()
            .select_related("ad_group_source")
        )
        return {x.ad_group_source.source_id: x for x in source_settings}

    @cached_property
    def bid_modifiers_by_source(self):
        bid_modifiers_qs = bid_modifiers.BidModifier.objects.filter(
            type=bid_modifiers.BidModifierType.SOURCE, ad_group=self.ad_group
        )
        return {int(bid_modifier.target): bid_modifier for bid_modifier in bid_modifiers_qs}

    @cached_property
    def totals(self):
        daily_budget = sum(
            [
                v["daily_budget"]
                for v in list(self.settings_map.values())
                if v["daily_budget"] and v["state"] == constants.AdGroupSourceSettingsState.ACTIVE
            ]
        )

        local_daily_budget = sum(
            [
                v["local_daily_budget"]
                for v in list(self.settings_map.values())
                if v["local_daily_budget"] and v["state"] == constants.AdGroupSourceSettingsState.ACTIVE
            ]
        )

        # MVP for all-RTB-sources-as-one
        if (
            self.ad_group_settings.b1_sources_group_enabled
            and self.ad_group_settings.b1_sources_group_state == constants.AdGroupSourceSettingsState.ACTIVE
        ):
            daily_budget += self.ad_group_settings.b1_sources_group_daily_budget
            local_daily_budget += self.ad_group_settings.local_b1_sources_group_daily_budget

        totals = {
            "daily_budget": daily_budget,
            "local_daily_budget": local_daily_budget,
            "current_daily_budget": daily_budget,
            "local_current_daily_budget": local_daily_budget,
        }

        return totals


class PublisherBidModifierLoader(PublisherBlacklistLoader):
    def __init__(
        self,
        ad_group,
        blacklist_qs,
        whitelist_qs,
        publisher_group_targeting,
        filtered_sources_qs,
        user,
        account=None,
        **kwargs,
    ):
        super(PublisherBidModifierLoader, self).__init__(
            blacklist_qs, whitelist_qs, publisher_group_targeting, filtered_sources_qs, user, account=None, **kwargs
        )
        self.ad_group = ad_group
        self.has_bid_modifiers = True

    @classmethod
    def from_constraints(cls, user, constraints, **kwargs):
        return cls(
            constraints["ad_group"],
            constraints["publisher_blacklist"],
            constraints["publisher_whitelist"],
            constraints["publisher_group_targeting"],
            constraints["filtered_sources"],
            user,
            start_date=constraints.get("date__gte"),
            end_date=constraints.get("date__lte"),
            account=constraints.get("account"),
        )

    @cached_property
    def modifier_map(self):
        modifiers = bid_modifiers.BidModifier.objects.filter_publisher_bid_modifiers().filter(ad_group=self.ad_group)
        modifiers = modifiers.filter(source__in=self.filtered_sources_qs)
        return {(x.source_id, x.target): x for x in modifiers}


class DeliveryLoader(Loader):
    def __init__(self, ad_group, user, **kwargs):
        breakdown = kwargs.pop("breakdown", None)
        self.delivery_dimension = breakdown[0] if breakdown else None
        self.ad_group = ad_group
        self.user = user

        bid_modifiers_qs = bid_modifiers.BidModifier.objects.filter(
            type=core.features.bid_modifiers.helpers.breakdown_name_to_modifier_type(self.delivery_dimension),
            ad_group=self.ad_group,
        )

        super().__init__(bid_modifiers_qs, **kwargs)

    @classmethod
    def _get_obj_id(cls, bid_modifier):
        try:
            return int(bid_modifier.target)
        except ValueError:
            return bid_modifier.target

    @classmethod
    def from_constraints(cls, user, constraints, **kwargs):
        return cls(
            constraints.get("ad_group"),
            user,
            start_date=constraints.get("date__gte"),
            end_date=constraints.get("date__lte"),
            **kwargs,
        )

    @cached_property
    def objs_count(self):
        return DEFAULT_OBJS_COUNT


class PlacementLoader(PublisherBlacklistLoader):
    @classmethod
    def _get_obj_id(cls, obj):
        return publisher_helpers.create_placement_id(obj.publisher, obj.source_id, obj.placement)

    @cached_property
    def publisher_group_entry_map(self):
        return publisher_helpers.PublisherPlacementLookupMap(self.blacklist_qs, self.whitelist_qs)

    def _get_publisher_group_entry_map_key(self, row):
        return row["placement_id"]


class PlacementBidModifierLoader(PlacementLoader, PublisherBidModifierLoader):
    @cached_property
    def modifier_map(self):
        modifiers = bid_modifiers.BidModifier.objects.filter_placement_bid_modifiers().filter(ad_group=self.ad_group)
        modifiers = modifiers.filter(source__in=self.filtered_sources_qs)
        return {x.target: x for x in modifiers}
