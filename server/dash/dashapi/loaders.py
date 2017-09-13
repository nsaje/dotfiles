import collections
from django.utils.functional import cached_property
from django.db.models.query import QuerySet

from automation import campaign_stop
from zemauth.models import User as ZemUser

from analytics.projections import BudgetProjections

from dash import models
from dash import constants
from dash import publisher_helpers
from dash.views import helpers as view_helpers
from dash.dashapi import data_helper


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


def get_loader_for_dimension(target_dimension, level):
    if target_dimension == 'account_id':
        return AccountsLoader
    elif target_dimension == 'campaign_id':
        return CampaignsLoader
    elif target_dimension == 'ad_group_id':
        return AdGroupsLoader
    elif target_dimension == 'content_ad_id':
        return ContentAdsLoader
    elif target_dimension == 'source_id':
        if level == constants.Level.AD_GROUPS:
            return AdGroupSourcesLoader
        return SourcesLoader
    elif target_dimension == 'publisher_id':
        return PublisherBlacklistLoader
    return None


class Loader(object):

    def __init__(self, objs_qs, start_date=None, end_date=None):
        self.objs_qs = objs_qs

        self._start_date = start_date
        self._end_date = end_date

    @classmethod
    def _get_obj_id(cls, obj):
        return obj.pk

    @cached_property
    def objs_map(self):
        return {self._get_obj_id(x): x for x in self.objs_qs}

    @cached_property
    def objs_ids(self):
        return self.objs_map.keys()

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


class AccountsLoader(Loader):

    def __init__(self, accounts_qs, filtered_sources_qs, **kwargs):
        accounts_qs = accounts_qs.select_related('agency')

        super(AccountsLoader, self).__init__(accounts_qs, **kwargs)
        self.filtered_sources_qs = filtered_sources_qs

    @classmethod
    def from_constraints(cls, user, constraints):
        return cls(
            constraints['allowed_accounts'], constraints['filtered_sources'],
            start_date=constraints.get('date__gte'),
            end_date=constraints.get('date__lte')
        )

    @cached_property
    def settings_map(self):
        settings_qs = models.AccountSettingsReadOnly.objects\
                                                    .filter(account_id__in=self.objs_ids)\
                                                    .group_current_settings()

        # workaround because select_related is currently malfunctioned on models that inherit histroymixin
        # - it doesn't do what its supposed to do
        user_ids = set(x.default_account_manager_id for x in settings_qs)
        user_ids |= set(x.default_sales_representative_id for x in settings_qs)
        user_ids |= set(x.default_cs_representative_id for x in settings_qs)
        user_map = {x.id: x for x in ZemUser.objects.filter(pk__in=user_ids)}

        settings_obj_map = {x.account_id: x for x in settings_qs}
        status_map = self._get_status_map()

        settings_map = {}
        for account_id in self.objs_ids:
            settings = settings_obj_map.get(account_id)

            settings_dict = {
                'status': status_map[account_id],
                'archived': False,
                'default_account_manager': None,
                'default_sales_representative': None,
                'default_cs_representative': None,
                'account_type': constants.AccountType.get_text(constants.AccountType.UNKNOWN),
                'settings_id': None,  # for debugging purposes, isn't used in production code
                'salesforce_url': '',
            }
            if settings is not None:
                settings_dict.update({
                    'archived': settings.archived,
                    'account_type': constants.AccountType.get_text(settings.account_type),
                    'settings_id': settings.id,
                    'default_account_manager': view_helpers.get_user_full_name_or_email(
                        user_map.get(settings.default_account_manager_id), default_value=None),
                    'default_sales_representative': view_helpers.get_user_full_name_or_email(
                        user_map.get(settings.default_sales_representative_id), default_value=None),
                    'default_cs_representative': view_helpers.get_user_full_name_or_email(
                        user_map.get(settings.default_cs_representative_id), default_value=None),
                    'salesforce_url': settings.salesforce_url or ''
                })
            settings_map[account_id] = settings_dict

        return settings_map

    def _get_status_map(self):
        """
        Returns dict with account_id as key and status as value
        """

        ad_group_w_account = models.AdGroup.objects.filter(campaign__account_id__in=self.objs_ids)\
                                                   .values_list('id', 'campaign__account_id')

        ad_groups_settings = models.AdGroupSettings.objects\
                                                   .filter(ad_group_id__in=[x[0] for x in ad_group_w_account])\
                                                   .group_current_settings()\
                                                   .only_state_fields()

        status_map = view_helpers.get_ad_group_table_running_state_by_obj_id(
            ad_group_w_account, ad_groups_settings)

        for account_id in self.objs_ids:
            if account_id not in status_map:
                status_map[account_id] = constants.AdGroupRunningStatus.INACTIVE

        return status_map

    @cached_property
    def _projections(self):
        return BudgetProjections(self.start_date, self.end_date, 'account',
                                 accounts=self.objs_qs,
                                 campaign_id__in=models.Campaign.objects.filter(account_id__in=self.objs_ids))

    @cached_property
    def projections_map(self):
        projections_dict = {}
        for account_id in self.objs_ids:
            projections_dict[account_id] = self._projections.row(account_id)
        return projections_dict

    @cached_property
    def projections_totals(self):
        return self._projections.total()


class CampaignsLoader(Loader):

    def __init__(self, campaigns_qs, filtered_sources_qs, **kwargs):
        super(CampaignsLoader, self).__init__(
            campaigns_qs.select_related('account'), **kwargs)

        self.filtered_sources_qs = filtered_sources_qs

    @classmethod
    def from_constraints(cls, user, constraints):
        return cls(
            constraints['allowed_campaigns'], constraints['filtered_sources'],
            start_date=constraints.get('date__gte'),
            end_date=constraints.get('date__lte')
        )

    @cached_property
    def settings_map(self):
        settings_qs = models.CampaignSettingsReadOnly.objects\
                                                     .filter(campaign_id__in=self.objs_ids)\
                                                     .group_current_settings()\
                                                     .select_related('campaign_manager')
        settings_obj_map = {x.campaign_id: x for x in settings_qs}
        status_map = self._get_status_map()
        settings_map = {}

        for campaign_id in self.objs_ids:
            settings = settings_obj_map.get(campaign_id)

            settings_dict = {
                'status': status_map[campaign_id],
                'archived': False,
                'campaign_manager': None,
                'settings_id': None,  # for debugging purposes, get removed
            }
            if settings is not None:
                settings_dict.update({
                    'archived': settings.archived,
                    'campaign_manager': view_helpers.get_user_full_name_or_email(
                        settings.campaign_manager, default_value=None),
                    'settings_id': settings.id,
                })
            settings_map[campaign_id] = settings_dict

        return settings_map

    def _get_status_map(self):
        ad_group_w_campaing = models.AdGroup.objects.filter(campaign_id__in=self.objs_ids)\
                                                    .values_list('id', 'campaign_id')
        ad_groups_settings = models.AdGroupSettings.objects\
                                                   .filter(ad_group_id__in=[x[0] for x in ad_group_w_campaing])\
                                                   .group_current_settings()\
                                                   .only_state_fields()

        status_map = view_helpers.get_ad_group_table_running_state_by_obj_id(
            ad_group_w_campaing, ad_groups_settings)

        for campaign_id in self.objs_ids:
            if campaign_id not in status_map:
                status_map[campaign_id] = constants.AdGroupRunningStatus.INACTIVE

        return status_map

    @cached_property
    def _projections(self):
        return BudgetProjections(self.start_date, self.end_date, 'campaign',
                                 campaign_id__in=self.objs_ids)

    @cached_property
    def projections_map(self):
        projections_dict = {}
        for campaign_id in self.objs_ids:
            projections_dict[campaign_id] = self._projections.row(campaign_id)
        return projections_dict

    @cached_property
    def projections_totals(self):
        return self._projections.total()


class AdGroupsLoader(Loader):

    def __init__(self, ad_groups_qs, filtered_sources_qs, **kwargs):
        super(AdGroupsLoader, self).__init__(
            ad_groups_qs.select_related('campaign', 'campaign__account'), **kwargs)
        self.filtered_sources_qs = filtered_sources_qs

    @classmethod
    def from_constraints(cls, user, constraints):
        return cls(
            constraints['allowed_ad_groups'], constraints['filtered_sources'],
            start_date=constraints.get('date__gte'),
            end_date=constraints.get('date__lte')
        )

    @cached_property
    def settings_map(self):
        settings_qs = models.AdGroupSettings.objects\
                                            .filter(ad_group_id__in=self.objs_ids)\
                                            .group_current_settings()\
                                            .only('ad_group_id', 'archived', 'state')
        settings_obj_map = {x.ad_group_id: x for x in settings_qs}

        settings_map = {}
        for ad_group_id in self.objs_ids:
            settings = settings_obj_map[ad_group_id]

            settings_map[ad_group_id] = {
                'archived': settings.archived,
                'status': settings.state,
                'state': settings.state,
                'settings_id': settings.id,
            }

        return settings_map

    @cached_property
    def base_level_settings_map(self):
        campaign_ad_groups = collections.defaultdict(list)
        for _, ad_group in self.objs_map.iteritems():
            campaign_ad_groups[ad_group.campaign_id].append(ad_group)

        campaigns_map = {x.id: x for x in models.Campaign.objects.filter(pk__in=campaign_ad_groups.keys())}

        settings_map = {}
        for campaign_id, ad_groups in campaign_ad_groups.items():
            campaign = campaigns_map[campaign_id]
            campaign_stop_check_map = campaign_stop.can_enable_ad_groups(campaign, campaign.get_current_settings())
            campaign_has_available_budget = data_helper.campaign_has_available_budget(campaign)

            for ad_group in ad_groups:
                settings_map[ad_group.id] = {
                    'campaign_stop_inactive': campaign_stop_check_map.get(ad_group.id),
                    'campaign_has_available_budget': campaign_has_available_budget,
                }

        return settings_map


class ContentAdsLoader(Loader):

    def __init__(self, content_ads_qs, filtered_sources_qs, **kwargs):
        super(ContentAdsLoader, self).__init__(content_ads_qs.select_related('batch'), **kwargs)
        self.filtered_sources_qs = filtered_sources_qs

    @classmethod
    def from_constraints(cls, user, constraints):
        return cls(
            constraints['allowed_content_ads'], constraints['filtered_sources'],
            start_date=constraints.get('date__gte'),
            end_date=constraints.get('date__lte')
        )

    @cached_property
    def batch_map(self):
        return {x.pk: x.batch for x in self.objs_qs}

    @cached_property
    def ad_group_loader(self):
        ad_groups_qs = models.AdGroup.objects.filter(
            pk__in=set(x.ad_group_id for x in self.objs_qs))

        return AdGroupsLoader(ad_groups_qs, self.filtered_sources_qs)

    @cached_property
    def ad_group_map(self):
        ad_group_map = {}
        for content_ad_id, content_ad in self.objs_map.iteritems():
            ad_group_map[content_ad_id] = self.ad_group_loader.objs_map[content_ad.ad_group_id]
        return ad_group_map

    @cached_property
    def status_map(self):
        status_map = {}
        for content_ad_id, content_ad in self.objs_map.iteritems():
            content_ad_sources = self.content_ads_sources_map[content_ad_id]
            if (any([x.state == constants.ContentAdSourceState.ACTIVE for x in content_ad_sources]) and
                self.ad_group_loader.settings_map[content_ad.ad_group_id]['status'] ==
                    constants.AdGroupRunningStatus.ACTIVE):
                status_map[content_ad_id] = constants.ContentAdSourceState.ACTIVE
            else:
                status_map[content_ad_id] = constants.ContentAdSourceState.INACTIVE
        return status_map

    @cached_property
    def per_source_status_map(self):
        per_source_map = collections.defaultdict(dict)
        sources = {x.id: x.name for x in self.filtered_sources_qs}
        source_status_map = self._get_per_ad_group_source_status_map()

        for content_ad_id, content_ad in self.objs_map.iteritems():
            for content_ad_source in self.content_ads_sources_map[content_ad_id]:
                source_id = content_ad_source.source_id

                source_status = source_status_map[content_ad.ad_group_id][source_id]
                if source_status is None:
                    source_status = constants.AdGroupSourceSettingsState.INACTIVE

                per_source_map[content_ad_id][content_ad_source.source_id] = {
                    'source_id': source_id,
                    'source_name': sources.get(source_id),
                    'source_status': source_status,
                    'submission_status': content_ad_source.get_submission_status(),
                    'submission_errors': content_ad_source.submission_errors,
                }

        return per_source_map

    def _get_per_ad_group_source_status_map(self):
        ad_group_sources_settings = models.AdGroupSourceSettings.objects.filter(
            ad_group_source__ad_group_id__in=set(x.ad_group_id for x in self.objs_qs)).group_current_settings().values_list(
                'ad_group_source__ad_group_id', 'ad_group_source__source_id', 'state')

        settings_map = collections.defaultdict(dict)
        for ad_group_id, source_id, state in ad_group_sources_settings:
            settings_map[ad_group_id][source_id] = state
        return settings_map

    @cached_property
    def content_ads_sources_map(self):
        qs = models.ContentAdSource.objects.filter(
            content_ad_id__in=self.objs_ids).filter_by_sources(self.filtered_sources_qs)

        content_ads_sources_map = collections.defaultdict(list)
        for content_ad_source in qs:
            content_ads_sources_map[content_ad_source.content_ad_id].append(content_ad_source)

        return content_ads_sources_map


class PublisherBlacklistLoader(Loader):

    def __init__(self, blacklist_qs, whitelist_qs, publisher_group_targeting, filtered_sources_qs, user, account=None, **kwargs):
        super(PublisherBlacklistLoader, self).__init__(blacklist_qs | whitelist_qs, **kwargs)
        self.filtered_sources_qs = filtered_sources_qs.select_related('source_type')
        self.user = user

        self.publisher_group_targeting = publisher_group_targeting
        self.whitelist_qs = whitelist_qs
        self.blacklist_qs = blacklist_qs
        self.account = account

        self.default = {
            'status': constants.PublisherTargetingStatus.UNLISTED,
        }

    @classmethod
    def _get_obj_id(cls, obj):
        return publisher_helpers.create_publisher_id(obj.publisher, obj.source_id)

    @classmethod
    def from_constraints(cls, user, constraints):
        return cls(
            constraints['publisher_blacklist'], constraints['publisher_whitelist'],
            constraints['publisher_group_targeting'],
            constraints['filtered_sources'],
            user,
            start_date=constraints.get('date__gte'),
            end_date=constraints.get('date__lte'),
            account=constraints.get('account'))

    @cached_property
    def publisher_group_entry_map(self):
        return publisher_helpers.PublisherIdLookupMap(self.blacklist_qs, self.whitelist_qs)

    def find_blacklisted_status_for_level(self, row, level, publisher_group_entry):
        targeting = self.publisher_group_targeting[level].get(
            row.get(level + '_id'),  # for reports there can be multiple entities per level
            self.publisher_group_targeting[level],  # default is used for grid
        )

        if publisher_group_entry.publisher_group_id in targeting['included']:
            return {
                'status': constants.PublisherTargetingStatus.WHITELISTED,
            }

        if publisher_group_entry.publisher_group_id in targeting['excluded']:
            return {
                'status': constants.PublisherTargetingStatus.BLACKLISTED,
            }

        return None

    def find_blacklisted_status(self, row, publisher_group_entry):
        status = self.find_blacklisted_status_for_level(row, 'ad_group', publisher_group_entry)
        if status is not None:
            status['blacklisted_level'] = constants.PublisherBlacklistLevel.ADGROUP
            return status

        status = self.find_blacklisted_status_for_level(row, 'campaign', publisher_group_entry)
        if status is not None:
            status['blacklisted_level'] = constants.PublisherBlacklistLevel.CAMPAIGN
            return status

        status = self.find_blacklisted_status_for_level(row, 'account', publisher_group_entry)
        if status is not None:
            status['blacklisted_level'] = constants.PublisherBlacklistLevel.ACCOUNT
            return status

        if publisher_group_entry.publisher_group_id in self.publisher_group_targeting['global']['excluded']:
            return {
                'status': constants.PublisherTargetingStatus.BLACKLISTED,
                'blacklisted_level': constants.PublisherBlacklistLevel.GLOBAL,
            }

        return self.default

    def find_blacklisted_status_by_subdomain(self, row):
        publisher_group_entry = self.publisher_group_entry_map[row['publisher_id']]
        if publisher_group_entry is not None:
            return self.find_blacklisted_status(row, publisher_group_entry)

        # nothing matched, return the default value
        return self.default

    @cached_property
    def source_map(self):
        return {x.id: x for x in self.filtered_sources_qs}

    @cached_property
    def can_blacklist_source_map(self):
        d = collections.defaultdict(lambda: False)

        for source_id, source in self.source_map.items():
            can_blacklist_outbrain_publisher = source.source_type.type == constants.SourceType.OUTBRAIN and\
                self.user.has_perm(
                    'zemauth.can_modify_outbrain_account_publisher_blacklist_status')

            d[source_id] = (source.can_modify_publisher_blacklist_automatically() and
                            (source.source_type.type != constants.SourceType.OUTBRAIN or
                             can_blacklist_outbrain_publisher))
        return d


class SourcesLoader(Loader):

    @classmethod
    def from_constraints(cls, user, constraints):
        return cls(
            constraints['filtered_sources'],
            start_date=constraints.get('date__gte'),
            end_date=constraints.get('date__lte')
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
        super(AdGroupSourcesLoader, self).__init__(sources_qs.select_related('source_type'), **kwargs)

        self.base_objects = [ad_group]
        self.ad_group = ad_group
        self.ad_group_settings = ad_group.get_current_settings()
        self.campaign_settings = ad_group.campaign.get_current_settings()
        self.user = user

    @classmethod
    def from_constraints(cls, user, constraints):
        return cls(constraints['filtered_sources'], constraints['ad_group'], user,
                   start_date=constraints.get('date__gte'),
                   end_date=constraints.get('date__lte'))

    @cached_property
    def settings_map(self):
        result = {}
        ad_group_sources_map = {x.source_id: x for x in self._active_ad_groups_sources_qs}

        for source_id, source in self.objs_map.items():
            ad_group_source = ad_group_sources_map[source_id]
            source_settings = self._ad_group_source_settings_map[source_id]

            editable_fields = view_helpers.get_editable_fields(
                ad_group_source.ad_group, ad_group_source, self.ad_group_settings, source_settings,
                self.campaign_settings, self._allowed_sources,
                self._campaign_stop_can_enable_source_map.get(ad_group_source.id, True),
            )

            if editable_fields.get('status_setting'):
                editable_fields['state'] = editable_fields.pop('status_setting')

            state = source_settings.state if source_settings else constants.AdGroupSourceSettingsState.INACTIVE
            result[source_id] = {
                'state': state,
                'status': data_helper.get_source_status(ad_group_source, state, self.ad_group_settings.state),
                'bid_cpc': source_settings.cpc_cc if source_settings else None,
                'daily_budget': source_settings.daily_budget_cc if source_settings else None,

                'supply_dash_url': ad_group_source.get_supply_dash_url(),
                'supply_dash_disabled_message': view_helpers.get_source_supply_dash_disabled_message(
                    ad_group_source, source),

                'editable_fields': editable_fields,
                'notifications': data_helper.get_ad_group_source_notification(
                    ad_group_source, self.ad_group_settings, source_settings),
            }

            # MVP for all-RTB-sources-as-one
            if self.ad_group_settings.b1_sources_group_enabled and source.source_type.type == constants.SourceType.B1:
                can_edit_cpc = not self.user.has_perm('zemauth.can_set_rtb_sources_as_one_cpc')
                cpc_message = None
                if self.ad_group_settings.autopilot_state != constants.AdGroupSettingsAutopilotState.INACTIVE:
                    cpc_message = 'This value cannot be edited because the ad group is on Autopilot.'
                elif not can_edit_cpc:
                    cpc_message = 'Please edit RTB Sources\' Bid CPC.'
                result[source_id]['daily_budget'] = None
                result[source_id]['editable_fields']['daily_budget']['enabled'] = False
                result[source_id]['editable_fields']['daily_budget']['message'] = None
                result[source_id]['editable_fields']['bid_cpc']['enabled'] = can_edit_cpc
                result[source_id]['editable_fields']['bid_cpc']['message'] = cpc_message
                if self.ad_group_settings.b1_sources_group_state == constants.AdGroupSourceSettingsState.INACTIVE and \
                   result[source_id]['status'] == constants.AdGroupSourceSettingsState.ACTIVE:
                    result[source_id]['status'] = constants.AdGroupSourceSettingsState.INACTIVE
                    result[source_id]['notifications'] = {
                        'message': 'This media source is enabled but will not run until you enable RTB Sources.',
                        'important': True
                    }

        return result

    @cached_property
    def _allowed_sources(self):
        return self.ad_group.campaign.account.allowed_sources.all().values_list('pk', flat=True)

    @cached_property
    def _campaign_stop_can_enable_source_map(self):
        # by ad_group_source_id
        return campaign_stop.can_enable_media_sources(
            self.ad_group,
            self.ad_group.campaign,
            self.campaign_settings,
            self.ad_group_settings)

    @cached_property
    def _active_ad_groups_sources_qs(self):
        if isinstance(self.base_objects, QuerySet):
            modelcls = self.base_objects.model
        else:
            modelcls = type(self.base_objects[0])

        return view_helpers.get_active_ad_group_sources(modelcls, self.base_objects)

    @cached_property
    def _ad_group_source_settings_map(self):
        source_settings = models.AdGroupSourceSettings.objects.filter(
            ad_group_source_id__in=[x.pk for x in self._active_ad_groups_sources_qs])\
            .group_current_settings()\
            .select_related('ad_group_source')
        return {x.ad_group_source.source_id: x for x in source_settings}

    @cached_property
    def totals(self):
        daily_budget = sum([
            v['daily_budget'] for v in self.settings_map.values()
            if v['daily_budget'] and v['state'] == constants.AdGroupSourceSettingsState.ACTIVE])

        # MVP for all-RTB-sources-as-one
        if self.ad_group_settings.b1_sources_group_enabled \
           and self.ad_group_settings.b1_sources_group_state == constants.AdGroupSourceSettingsState.ACTIVE:
            daily_budget += self.ad_group_settings.b1_sources_group_daily_budget

        totals = {
            'daily_budget': daily_budget,
            'current_daily_budget': daily_budget,
        }

        return totals
