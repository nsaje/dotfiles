import collections
from django.utils.functional import cached_property

from automation import campaign_stop

from analytics.projections import BudgetProjections

from dash import models
from dash import constants
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


class Loader(object):
    def __init__(self, objs_qs, start_date=None, end_date=None):
        self.objs_qs = objs_qs

        self._start_date = start_date
        self._end_date = end_date

    @cached_property
    def objs_map(self):
        return {x.pk: x for x in self.objs_qs}

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

    @cached_property
    def settings_qs(self):
        return models.AccountSettings.objects\
                                     .filter(account_id__in=self.objs_ids)\
                                     .group_current_settings()\
                                     .select_related(
                                         'default_account_manager',
                                         'default_sales_representative')

    @cached_property
    def settings_map(self):
        settings_map = collections.defaultdict(models.AccountSettings)
        settings_map.update({x.account_id: x for x in self.settings_qs})

        return settings_map

    @cached_property
    def status_map(self):
        """
        Returns dict with account_id as key and status as value
        """

        ad_groups = models.AdGroup.objects.filter(campaign__account_id__in=self.objs_ids)
        ad_groups_settings = models.AdGroupSettings.objects\
                                                   .filter(ad_group__in=ad_groups)\
                                                   .group_current_settings()

        ad_groups_sources_settings = models.AdGroupSourceSettings\
                                           .objects\
                                           .filter(ad_group_source__ad_group__in=ad_groups)\
                                           .filter_by_sources(self.filtered_sources_qs)\
                                           .group_current_settings()\
                                           .select_related('ad_group_source')

        status_map = view_helpers.get_ad_group_state_by_sources_running_status(
            ad_groups, ad_groups_settings, ad_groups_sources_settings, 'campaign__account_id')

        # the helper function only sets active, does not set inactive
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
        super(CampaignsLoader, self).__init__(campaigns_qs, **kwargs)
        self.filtered_sources_qs = filtered_sources_qs

    @cached_property
    def settings_qs(self):
        return models.CampaignSettings.objects\
                                      .filter(campaign_id__in=self.objs_ids)\
                                      .select_related('campaign_manager')\
                                      .group_current_settings()

    @cached_property
    def settings_map(self):
        settings_map = collections.defaultdict(models.CampaignSettings)
        settings_map.update({x.campaign_id: x for x in self.settings_qs})

        return settings_map

    @cached_property
    def status_map(self):
        ad_groups = models.AdGroup.objects.filter(campaign_id__in=self.objs_ids)
        ad_groups_settings = models.AdGroupSettings.objects\
                                                   .filter(ad_group__in=ad_groups)\
                                                   .group_current_settings()

        ad_groups_sources_settings = models.AdGroupSourceSettings\
                                           .objects\
                                           .filter(ad_group_source__ad_group__in=ad_groups)\
                                           .filter_by_sources(self.filtered_sources_qs)\
                                           .group_current_settings()\
                                           .select_related('ad_group_source')

        status_map = view_helpers.get_ad_group_state_by_sources_running_status(
            ad_groups, ad_groups_settings, ad_groups_sources_settings, 'campaign_id')

        # the helper function only sets active, does not set inactive
        for obj_id in self.objs_ids:
            if obj_id not in status_map:
                status_map[obj_id] = constants.AdGroupRunningStatus.INACTIVE

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
        super(AdGroupsLoader, self).__init__(ad_groups_qs, **kwargs)
        self.filtered_sources_qs = filtered_sources_qs

    @cached_property
    def settings_qs(self):
        settings_qs = models.AdGroupSettings\
                            .objects\
                            .filter(ad_group_id__in=self.objs_ids)\
                            .group_current_settings()
        return settings_qs

    @cached_property
    def settings_map(self):
        settings_map = collections.defaultdict(models.AdGroupSettings)
        settings_map.update({x.ad_group_id: x for x in self.settings_qs})

        return settings_map

    @cached_property
    def other_settings_map(self):
        campaign_ad_groups = collections.defaultdict(list)
        for _, ad_group in self.objs_map.iteritems():
            campaign_ad_groups[ad_group.campaign_id].append(ad_group)

        campaigns_map = {x.id: x for x in models.Campaign.objects.filter(pk__in=campaign_ad_groups.keys())}

        other_settings_map = {}
        for campaign_id, ad_groups in campaign_ad_groups.items():
            campaign = campaigns_map[campaign_id]
            campaign_stop_check_map = campaign_stop.can_enable_ad_groups(campaign, campaign.get_current_settings())
            campaign_has_available_budget = data_helper.campaign_has_available_budget(campaign)

            for ad_group in ad_groups:
                other_settings_map[ad_group.id] = {
                    'campaign_stop_inactive': campaign_stop_check_map.get(ad_group.id, True),
                    'campaign_has_available_budget': campaign_has_available_budget,
                }

        return other_settings_map

    @cached_property
    def sources_settings_qs(self):
        return models.AdGroupSourceSettings\
                     .objects\
                     .filter(ad_group_source__ad_group_id__in=self.objs_ids)\
                     .filter_by_sources(self.filtered_sources_qs)\
                     .group_current_settings()\
                     .select_related('ad_group_source')

    @cached_property
    def sources_settings_map(self):
        m = collections.defaultdict(dict)
        for ad_group_id in self.objs_ids:
            for ad_group_source_settings in self.sources_settings_qs:
                m[ad_group_id][ad_group_source_settings.ad_group_source.source_id] = ad_group_source_settings
        return m

    @cached_property
    def status_map(self):
        status_map = view_helpers.get_ad_group_state_by_sources_running_status(
            self.objs_qs,
            self.settings_qs,
            self.sources_settings_qs,
            group_by_key='id'
        )

        # the helper function only sets active, does not set inactive
        for obj_id in self.objs_ids:
            if obj_id not in status_map:
                status_map[obj_id] = constants.AdGroupRunningStatus.INACTIVE

        return status_map


class ContentAdsLoader(Loader):
    def __init__(self, content_ads_qs, filtered_sources_qs, **kwargs):
        super(ContentAdsLoader, self).__init__(content_ads_qs.select_related('batch'), **kwargs)
        self.filtered_sources_qs = filtered_sources_qs

    @cached_property
    def batch_map(self):
        return {x.pk: x.batch for x in self.objs_qs}

    @cached_property
    def ad_groups_qs(self):
        return models.AdGroup.objects.filter(
            pk__in=set(x.ad_group_id for x in self.objs_qs))

    @cached_property
    def ad_group_loader(self):
        return AdGroupsLoader(self.ad_groups_qs, self.filtered_sources_qs)

    @cached_property
    def ad_group_map(self):
        ad_group_map = {}
        for content_ad in self.objs_qs:
            ad_group_map[content_ad.id] = self.ad_group_loader.objs_map[content_ad.ad_group_id]
        return ad_group_map

    @cached_property
    def is_demo_map(self):
        # TODO this should be deprecated when old demo code is thrown out
        demo_ad_group_ids = models.AdGroup.demo_objects.all().values_list('pk', flat=True)

        return {
            content_ad_id: (content_ad.ad_group_id in demo_ad_group_ids)
            for content_ad_id, content_ad
            in self.objs_map.iteritems()
        }

    @cached_property
    def status_map(self):
        status_map = {}
        for content_ad_id, content_ad in self.objs_map.iteritems():
            content_ad_sources = self.content_ads_sources_map[content_ad_id]
            if (any([x.state == constants.ContentAdSourceState.ACTIVE for x in content_ad_sources]) and
               self.ad_group_loader.status_map[content_ad.ad_group_id] == constants.AdGroupRunningStatus.ACTIVE):
                status_map[content_ad_id] = constants.ContentAdSourceState.ACTIVE
            else:
                status_map[content_ad_id] = constants.ContentAdSourceState.INACTIVE
        return status_map

    @cached_property
    def per_source_status_map(self):
        per_source_map = collections.defaultdict(dict)
        sources = {x.id: x.name for x in self.filtered_sources_qs}

        for content_ad_id, content_ad in self.objs_map.iteritems():
            for content_ad_source in self.content_ads_sources_map[content_ad_id]:
                source_id = content_ad_source.source_id
                ad_group_source_settings = self.ad_group_loader.sources_settings_map[content_ad.ad_group_id].get(source_id)
                source_status = (ad_group_source_settings.state if ad_group_source_settings else
                                 constants.AdGroupSourceSettingsState.INACTIVE)

                per_source_map[content_ad_id][content_ad_source.source_id] = {
                    'source_id': source_id,
                    'source_name': sources.get(source_id),
                    'source_status': source_status,
                    'submission_status': content_ad_source.get_submission_status(),
                    'submission_errors': content_ad_source.submission_errors,
                }

        return per_source_map

    @cached_property
    def content_ads_sources_qs(self):
        return models.ContentAdSource.objects.filter(
            content_ad_id__in=self.objs_ids).filter_by_sources(self.filtered_sources_qs)

    @cached_property
    def content_ads_sources_map(self):
        content_ads_sources_map = collections.defaultdict(list)
        for content_ad_source in self.content_ads_sources_qs:
            content_ads_sources_map[content_ad_source.content_ad_id].append(content_ad_source)

        return content_ads_sources_map


class SourcesLoader(Loader):

    def __init__(self, sources_qs, ad_groups_sources_qs, **kwargs):
        super(SourcesLoader, self).__init__(sources_qs, **kwargs)

        self.ad_groups_sources_qs = ad_groups_sources_qs

    @cached_property
    def settings_map(self):
        ad_group_source_status_map = {}

        ad_groups_settings_map = {x.ad_group_id: x for x in self.ad_groups_settings_qs}
        ad_groups_sources_settings_map = {x.ad_group_source_id: x for x in self.ad_groups_sources_settings_qs}

        statuses = view_helpers.get_fake_ad_group_source_states(
            self.ad_groups_sources_qs,
            ad_groups_sources_settings_map,
            ad_groups_settings_map)

        by_source_statuses = collections.defaultdict(list)
        for status in statuses:
            by_source_statuses[status.ad_group_source.source_id].append(status)

        settings_map = {}

        for source_id, _ in self.objs_map.items():
            source_states = by_source_statuses[source_id]
            ad_group_source_settings = self.ad_groups_sources_settings_map.get(source_id, [])
            status = view_helpers.get_source_status_from_ad_group_source_states(source_states)
            bids_dict = data_helper.get_source_min_max_cpc(by_source_statuses[source_id])

            settings = {
                'daily_budget': data_helper.get_daily_budget_total(source_states),
                'min_bid_cpc': bids_dict['min_bid_cpc'],
                'max_bid_cpc': bids_dict['max_bid_cpc'],
                'status': status,

                # only for ad group level
                'state': ad_group_source_settings[0].state if len(ad_group_source_settings) == 1 else status,
            }
            settings_map[source_id] = settings

        return settings_map

    @cached_property
    def ad_groups_sources_settings_qs(self):
        return models.AdGroupSourceSettings.objects\
                                           .filter(ad_group_source__in=self.ad_groups_sources_qs)\
                                           .group_current_settings()

    @cached_property
    def ad_groups_sources_settings_map(self):
        # ad_group_source_id: source_id
        source_id_by_ad_group_source_id = {x.pk: x.source_id for x in self.ad_groups_sources_qs}

        # source_id: [ad_group_source_settings, ...]
        ad_groups_sources_settings_map = collections.defaultdict(list)

        for ad_group_source_settings in self.ad_groups_sources_settings_qs:
            source_id = source_id_by_ad_group_source_id.get(ad_group_source_settings.ad_group_source_id)
            ad_groups_sources_settings_map[source_id].append(ad_group_source_settings)

        return ad_groups_sources_settings_map

    @cached_property
    def ad_groups_sources_map(self):
        # source_id: [ad_group_source, ...]
        ad_groups_sources_map = collections.defaultdict(list)

        for ad_group_source in self.ad_groups_sources_qs:
            ad_groups_sources_map[ad_group_source.source_id].append(ad_group_source)

        return ad_groups_sources_map

    @cached_property
    def ad_groups_settings_qs(self):
        return models.AdGroupSettings.objects.filter(
            ad_group_id__in=self.ad_groups_sources_qs.values_list('ad_group_id', flat=True))\
                                             .group_current_settings()

    @cached_property
    def totals(self):
        min_cpcs = [v['min_bid_cpc'] for v in self.settings_map.values() if v['min_bid_cpc'] is not None]
        max_cpcs = [v['max_bid_cpc'] for v in self.settings_map.values() if v['max_bid_cpc'] is not None]

        totals = {
            'min_bid_cpc': min(min_cpcs) if min_cpcs else None,
            'max_bid_cpc': max(max_cpcs) if max_cpcs else None,
            'daily_budget': sum([v['daily_budget'] for v in self.settings_map.values() if v['daily_budget']])
        }

        return totals
