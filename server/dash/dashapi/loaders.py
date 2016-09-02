import collections

from automation import campaign_stop

from dash import models
from dash import constants
from dash.views import helpers as view_helpers
from dash.dashapi import data_helper


"""
Objects that load necessary related objects. All try to execute queries as seldom as possible.

Notes on implementation:
  - always compare a queryset with None, otherwise it executes a query on a database.
  - remember to select_related for objects that you will need
  - settings_map properties should return a default dict that returns default field values
  - same for status_map - should return default value
"""


class Loader(object):
    def __init__(self, objs_qs):
        self.objs_qs = objs_qs
        self._objs_map = None

    @property
    def objs_map(self):
        if self._objs_map is None:
            self._objs_map = {x.pk: x for x in self.objs_qs}
        return self._objs_map

    @property
    def objs_ids(self):
        return self.objs_map.keys()


class AccountsLoader(Loader):
    def __init__(self, accounts_qs, filtered_sources_qs):
        super(AccountsLoader, self).__init__(accounts_qs)

        self.filtered_sources_qs = filtered_sources_qs

        self._settings_qs = None
        self._settings_map = None

        self._status_map = None

    @property
    def settings_qs(self):
        if self._settings_qs is None:
            self._settings_qs = models.AccountSettings.objects\
                                                      .filter(account_id__in=self.objs_ids)\
                                                      .group_current_settings()\
                                                      .select_related(
                                                          'default_account_manager',
                                                          'default_sales_representative')
        return self._settings_qs

    @property
    def settings_map(self):
        if self._settings_map is None:
            self._settings_map = collections.defaultdict(models.AccountSettings)
            self._settings_map.update({x.account_id: x for x in self.settings_qs})

        return self._settings_map

    @property
    def status_map(self):
        if self._status_map is None:

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

            self._status_map = view_helpers.get_ad_group_state_by_sources_running_status(
                ad_groups, ad_groups_settings, ad_groups_sources_settings, 'campaign__account_id')

            # the helper function only sets active, does not set inactive
            for account_id in self.objs_ids:
                if account_id not in self._status_map:
                    self._status_map[account_id] = constants.AdGroupRunningStatus.INACTIVE

        return self._status_map


class CampaignsLoader(Loader):
    def __init__(self, campaigns_qs, filtered_sources_qs):
        super(CampaignsLoader, self).__init__(campaigns_qs)

        self.filtered_sources_qs = filtered_sources_qs

        self._settings_qs = None
        self._settings_map = None

        self._status_map = None

    @property
    def settings_qs(self):
        if self._settings_qs is None:
            self._settings_qs = models.CampaignSettings.objects\
                                                       .filter(campaign_id__in=self.objs_ids)\
                                                       .select_related('campaign_manager')\
                                                       .group_current_settings()
        return self._settings_qs

    @property
    def settings_map(self):
        if self._settings_map is None:
            self._settings_map = collections.defaultdict(models.CampaignSettings)
            self._settings_map.update({x.campaign_id: x for x in self.settings_qs})

        return self._settings_map

    @property
    def status_map(self):
        if self._status_map is None:
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

            self._status_map = view_helpers.get_ad_group_state_by_sources_running_status(
                ad_groups, ad_groups_settings, ad_groups_sources_settings, 'campaign_id')

            # the helper function only sets active, does not set inactive
            for obj_id in self.objs_ids:
                if obj_id not in self._status_map:
                    self._status_map[obj_id] = constants.AdGroupRunningStatus.INACTIVE

        return self._status_map


class AdGroupsLoader(Loader):
    def __init__(self, ad_groups_qs, filtered_sources_qs):
        super(AdGroupsLoader, self).__init__(ad_groups_qs)

        self.filtered_sources_qs = filtered_sources_qs

        self._settings_qs = None
        self._settings_map = None

        self._sources_settings_qs = None
        self._status_map = None
        self._other_settings_map = None

    @property
    def settings_qs(self):
        if self._settings_qs is None:
            self._settings_qs = models.AdGroupSettings\
                                      .objects\
                                      .filter(ad_group_id__in=self.objs_ids)\
                                      .group_current_settings()
        return self._settings_qs

    @property
    def settings_map(self):
        if self._settings_map is None:
            self._settings_map = collections.defaultdict(models.AdGroupSettings)
            self._settings_map.update({x.ad_group_id: x for x in self.settings_qs})

        return self._settings_map

    @property
    def other_settings_map(self):
        if self._other_settings_map is None:
            campaign_ad_groups = collections.defaultdict(list)
            for _, ad_group in self.objs_map.iteritems():
                campaign_ad_groups[ad_group.campaign_id].append(ad_group)

            campaigns_map = {x.id: x for x in models.Campaign.objects.filter(pk__in=campaign_ad_groups.keys())}

            self._other_settings_map = {}
            for campaign_id, ad_groups in campaign_ad_groups.items():
                campaign = campaigns_map[campaign_id]
                campaign_stop_check_map = campaign_stop.can_enable_ad_groups(campaign, campaign.get_current_settings())
                campaign_has_available_budget = data_helper.campaign_has_available_budget(campaign)

                for ad_group in ad_groups:
                    self._other_settings_map[ad_group.id] = {
                        'campaign_stop_inactive': campaign_stop_check_map.get(ad_group, True),
                        'campaign_has_available_budget': campaign_has_available_budget,
                    }

        return self._other_settings_map

    @property
    def sources_settings_qs(self):
        if self._sources_settings_qs is None:
            self._sources_settings_qs = models.AdGroupSourceSettings\
                                              .objects\
                                              .filter(ad_group_source__ad_group_id__in=self.objs_ids)\
                                              .filter_by_sources(self.filtered_sources_qs)\
                                              .group_current_settings()\
                                              .select_related('ad_group_source')
        return self._sources_settings_qs

    @property
    def status_map(self):
        if self._status_map is None:
            self._status_map = view_helpers.get_ad_group_state_by_sources_running_status(
                self.objs_qs,
                self.settings_qs,
                self.sources_settings_qs,
                group_by_key='id'
            )

            # the helper function only sets active, does not set inactive
            for obj_id in self.objs_ids:
                if obj_id not in self._status_map:
                    self._status_map[obj_id] = constants.AdGroupRunningStatus.INACTIVE

        return self._status_map


class ContentAdsLoader(Loader):
    def __init__(self, content_ads_qs, filtered_sources_qs):
        super(ContentAdsLoader, self).__init__(content_ads_qs.select_related('batch'))

        self.filtered_sources_qs = filtered_sources_qs

        self._batch_map = None
        self._ad_group_loader = None
        self._ad_group_map = None
        self._is_demo_map = None
        self._status_map = None
        self._content_ads_sources_qs = None
        self._content_ads_sources_map = None

    @property
    def batch_map(self):
        if self._batch_map is None:
            self._batch_map = {x.pk: x.batch for x in self.objs_qs}
        return self._batch_map

    @property
    def ad_group_loader(self):
        if self._ad_group_loader is None:
            self._ad_group_loader = AdGroupsLoader(models.AdGroup.objects.filter(
                pk__in=set(x.ad_group_id for x in self.objs_qs)), self.filtered_sources_qs)
        return self._ad_group_loader

    @property
    def ad_group_map(self):
        if self._ad_group_map is None:
            self._ad_group_map = {}
            for content_ad in self.objs_qs:
                self._ad_group_map[content_ad.id] = self.ad_group_loader.objs_map[content_ad.ad_group_id]
        return self._ad_group_map

    @property
    def is_demo_map(self):
        if self._is_demo_map is None:
            demo_ad_group_ids = models.AdGroup.demo_objects.all().values_list('pk', flat=True)

            self._is_demo_map = {
                content_ad_id: (content_ad.ad_group_id in demo_ad_group_ids)
                for content_ad_id, content_ad
                in self.objs_map.iteritems()
            }
        return self._is_demo_map

    @property
    def status_map(self):
        if self._status_map is None:
            self._status_map = {}
            for content_ad_id, content_ad in self.objs_map.iteritems():
                content_ad_sources = self.content_ads_sources_map[content_ad_id]
                if (any([x.state == constants.ContentAdSourceState.ACTIVE for x in content_ad_sources]) and
                   self.ad_group_loader.status_map[content_ad.ad_group_id] == constants.AdGroupRunningStatus.ACTIVE):
                    self._status_map[content_ad_id] = constants.ContentAdSourceState.ACTIVE
                else:
                    self._status_map[content_ad_id] = constants.ContentAdSourceState.INACTIVE
        return self._status_map

    @property
    def content_ads_sources_qs(self):
        if self._content_ads_sources_qs is None:
            self._content_ads_sources_qs = models.ContentAdSource.objects.filter(
                content_ad_id__in=self.objs_ids).filter_by_sources(self.filtered_sources_qs)
        return self._content_ads_sources_qs

    @property
    def content_ads_sources_map(self):
        if self._content_ads_sources_map is None:
            self._content_ads_sources_map = collections.defaultdict(list)
            for content_ad_source in self.content_ads_sources_qs:
                self._content_ads_sources_map[content_ad_source.content_ad_id].append(content_ad_source)
        return self._content_ads_sources_map


class SourcesLoader(Loader):

    def __init__(self, sources_qs, ad_groups_sources_qs):
        super(SourcesLoader, self).__init__(sources_qs)

        self.ad_groups_sources_qs = ad_groups_sources_qs
        self._ad_groups_sources_map = None

        self._settings_map = None

        self._ad_groups_sources_settings_qs = None
        self._ad_groups_sources_settings_map = None
        self._ad_groups_settings_qs = None
        self._ad_groups_settings_map = None

    def _load_settings_maps(self):
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

        self._settings_map = {}

        for source_id, _ in self.objs_map.items():
            source_states = by_source_statuses[source_id]
            ad_group_source_settings = self.ad_groups_sources_settings_map.get(source_id, [])
            status = view_helpers.get_source_status_from_ad_group_source_states(source_states)

            settings = {
                'daily_budget': data_helper.get_daily_budget_total(source_states),
                'status': status,
                # only for ad group level
                'state': ad_group_source_settings[0].state if len(ad_group_source_settings) == 1 else status,
            }

            settings.update(data_helper.get_source_min_max_cpc(by_source_statuses[source_id]))
            self._settings_map[source_id] = settings

    @property
    def settings_map(self):
        if self._settings_map is None:
            self._load_settings_maps()
        return self._settings_map

    @property
    def ad_groups_sources_settings_qs(self):
        if self._ad_groups_sources_settings_qs is None:

            self._ad_groups_source_settings_qs = models.AdGroupSourceSettings.objects.filter(
                ad_group_source__in=self.ad_groups_sources_qs
            ).group_current_settings()

        return self._ad_groups_source_settings_qs

    @property
    def ad_groups_sources_settings_map(self):
        if self._ad_groups_sources_settings_map is None:
            # ad_group_source_id: source_id
            source_id_by_ad_group_source_id = {x.pk: x.source_id for x in self.ad_groups_sources_qs}

            # source_id: [ad_group_source_settings, ...]
            self._ad_groups_sources_settings_map = collections.defaultdict(list)

            for ad_group_source_settings in self.ad_groups_sources_settings_qs:
                source_id = source_id_by_ad_group_source_id.get(ad_group_source_settings.ad_group_source_id)
                self._ad_groups_sources_settings_map[source_id].append(ad_group_source_settings)

        return self._ad_groups_sources_settings_map

    @property
    def ad_groups_sources_map(self):
        if self._ad_groups_sources_map is None:

            # source_id: [ad_group_source, ...]
            self._ad_groups_sources_map = collections.defaultdict(list)

            for ad_group_source in self.ad_groups_sources_qs:
                self._ad_groups_sources_map[ad_group_source.source_id].append(ad_group_source)

        return self._ad_groups_sources_map

    @property
    def ad_groups_settings_qs(self):
        if self._ad_groups_settings_qs is None:

            self._ad_groups_settings_qs = models.AdGroupSettings.objects.filter(
                ad_group_id__in=self.ad_groups_sources_qs.values_list('ad_group_id', flat=True)
            ).group_current_settings()

        return self._ad_groups_settings_qs
