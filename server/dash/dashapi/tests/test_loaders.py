from django.test import TestCase
from decimal import Decimal

from utils import test_helper

from dash import models
from dash import constants
from dash.dashapi import loaders


class AccountsLoaderTest(TestCase):

    fixtures = ['test_api_breakdowns.yaml']

    def setUp(self):
        accounts = models.Account.objects.all()
        sources = models.Source.objects.all()

        self.loader = loaders.AccountsLoader(accounts, sources)

    def test_objs(self):
        self.assertItemsEqual(self.loader.objs_ids, [1])
        self.assertDictEqual(self.loader.objs_map, {
            1: models.Account.objects.get(pk=1)
        })

    def test_settings_qs(self):
        self.assertDictEqual(self.loader.settings_map, {
            1: models.AccountSettings.objects.get(pk=1)
        })

    def test_status_map(self):
        self.assertDictEqual(self.loader.status_map, {
            1: constants.AdGroupRunningStatus.ACTIVE,
        })

    def test_status_map_filtered_sources(self):
        accounts = models.Account.objects.all()
        sources = models.Source.objects.filter(pk=2)

        loader = loaders.AccountsLoader(accounts, sources)

        self.assertDictEqual(dict(loader.status_map), {
            1: constants.AdGroupRunningStatus.INACTIVE,
        })


class CampaignsLoaderTest(TestCase):

    fixtures = ['test_api_breakdowns.yaml']

    def setUp(self):
        campaigns = models.Campaign.objects.all()
        sources = models.Source.objects.all()

        self.loader = loaders.CampaignsLoader(campaigns, sources)

    def test_objs(self):
        self.assertItemsEqual(self.loader.objs_ids, [1, 2])
        self.assertDictEqual(self.loader.objs_map, {
            1: models.Campaign.objects.get(pk=1),
            2: models.Campaign.objects.get(pk=2),
        })

    def test_settings_qs(self):
        self.assertDictEqual(self.loader.settings_map, {
            1: models.CampaignSettings.objects.get(pk=1),
            2: models.CampaignSettings.objects.get(pk=2),
        })

    def test_status_map(self):
        self.assertDictEqual(self.loader.status_map, {
            1: constants.AdGroupRunningStatus.ACTIVE,
            2: constants.AdGroupRunningStatus.INACTIVE,
        })

    def test_status_map_filtered_sources(self):
        campaigns = models.Campaign.objects.all()
        sources = models.Source.objects.filter(pk=2)

        loader = loaders.CampaignsLoader(campaigns, sources)

        self.assertDictEqual(dict(loader.status_map), {
            1: constants.AdGroupRunningStatus.INACTIVE,
            2: constants.AdGroupRunningStatus.INACTIVE,
        })


class AdGroupsLoaderTest(TestCase):

    fixtures = ['test_api_breakdowns.yaml']

    def setUp(self):
        ad_groups = models.AdGroup.objects.all()
        sources = models.Source.objects.all()

        self.loader = loaders.AdGroupsLoader(ad_groups, sources)

    def test_objs(self):
        self.assertItemsEqual(self.loader.objs_ids, [1, 2, 3])
        self.assertDictEqual(self.loader.objs_map, {
            1: models.AdGroup.objects.get(pk=1),
            2: models.AdGroup.objects.get(pk=2),
            3: models.AdGroup.objects.get(pk=3),
        })

    def test_settings_qs(self):
        self.assertDictEqual(self.loader.settings_map, {
            1: models.AdGroupSettings.objects.get(pk=4),
            2: models.AdGroupSettings.objects.get(pk=2),
            3: models.AdGroupSettings.objects.get(pk=3),
        })

    def test_status_map(self):
        self.assertDictEqual(self.loader.status_map, {
            1: constants.AdGroupRunningStatus.ACTIVE,
            2: constants.AdGroupRunningStatus.INACTIVE,
            3: constants.AdGroupRunningStatus.INACTIVE,
        })

    def test_status_map_filtered_sources(self):
        ad_groups = models.AdGroup.objects.all()
        sources = models.Source.objects.filter(pk=2)

        loader = loaders.AdGroupsLoader(ad_groups, sources)

        self.assertDictEqual(dict(loader.status_map), {
            1: constants.AdGroupRunningStatus.INACTIVE,
            2: constants.AdGroupRunningStatus.INACTIVE,
            3: constants.AdGroupRunningStatus.INACTIVE,
        })

    def test_other_settings_map(self):
        ad_groups = models.AdGroup.objects.all()
        sources = models.Source.objects.filter(pk=2)

        loader = loaders.AdGroupsLoader(ad_groups, sources)

        self.assertDictEqual(dict(loader.other_settings_map), {
            1: {'campaign_has_available_budget': False, 'campaign_stop_inactive': True},
            2: {'campaign_has_available_budget': False, 'campaign_stop_inactive': True},
            3: {'campaign_has_available_budget': False, 'campaign_stop_inactive': True},
        })


class ContentAdLoaderTest(TestCase):

    fixtures = ['test_api_breakdowns.yaml']

    def setUp(self):
        content_ads = models.ContentAd.objects.all()
        sources = models.Source.objects.all()

        self.loader = loaders.ContentAdsLoader(content_ads, sources)

    def test_objs(self):
        self.assertItemsEqual(self.loader.objs_ids, [1, 2, 3])
        self.assertDictEqual(self.loader.objs_map, {
            1: models.ContentAd.objects.get(pk=1),
            2: models.ContentAd.objects.get(pk=2),
            3: models.ContentAd.objects.get(pk=3),
        })

    def test_batch_map(self):
        self.assertDictEqual(self.loader.batch_map, {
            1: models.UploadBatch.objects.get(pk=1),
            2: models.UploadBatch.objects.get(pk=1),
            3: models.UploadBatch.objects.get(pk=2),
        })

    def test_ad_group_loader(self):
        self.assertDictEqual(self.loader.ad_group_loader.objs_map, {
            1: models.AdGroup.objects.get(pk=1),
        })

    def test_ad_group_map(self):
        self.assertDictEqual(self.loader.ad_group_map, {
            1: models.AdGroup.objects.get(pk=1),
            2: models.AdGroup.objects.get(pk=1),
            3: models.AdGroup.objects.get(pk=1),
        })

    def test_is_demo_map(self):
        self.assertDictEqual(self.loader.is_demo_map, {
            1: False,
            2: False,
            3: False,
        })

    def test_status_map(self):
        self.assertDictEqual(self.loader.status_map, {
            1: constants.ContentAdSourceState.ACTIVE,
            2: constants.ContentAdSourceState.ACTIVE,
            3: constants.ContentAdSourceState.INACTIVE,
        })

    def test_status_map_filtered_by_sources(self):
        content_ads = models.ContentAd.objects.all()
        sources = models.Source.objects.filter(pk=1)

        loader = loaders.ContentAdsLoader(content_ads, sources)

        self.assertDictEqual(loader.status_map, {
            1: constants.ContentAdSourceState.ACTIVE,
            2: constants.ContentAdSourceState.INACTIVE,
            3: constants.ContentAdSourceState.INACTIVE,
        })

    def test_content_ads_sources_map(self):
        self.assertDictEqual(self.loader.content_ads_sources_map, {
            1: [models.ContentAdSource.objects.get(pk=1), models.ContentAdSource.objects.get(pk=2)],
            2: [models.ContentAdSource.objects.get(pk=3)],
        })

    def test_content_ads_sources_map_filtered_by_sources(self):
        content_ads = models.ContentAd.objects.all()
        sources = models.Source.objects.filter(pk=1)

        loader = loaders.ContentAdsLoader(content_ads, sources)

        self.assertDictEqual(loader.content_ads_sources_map, {
            1: [models.ContentAdSource.objects.get(pk=1)],
        })


class SourcesLoaderTest(TestCase):

    fixtures = ['test_api_breakdowns.yaml']

    def setUp(self):
        sources = models.Source.objects.all()
        ad_groups_sources = models.AdGroupSource.objects.all()

        self.loader = loaders.SourcesLoader(sources, ad_groups_sources)

    def test_objs(self):
        self.assertItemsEqual(self.loader.objs_ids, [1, 2])
        self.assertDictEqual(self.loader.objs_map, {
            1: models.Source.objects.get(pk=1),
            2: models.Source.objects.get(pk=2),
        })

    def test_ad_groups_sources_map(self):
        self.assertDictEqual(self.loader.ad_groups_sources_map, {
            1: test_helper.QuerySetMatcher(models.AdGroupSource.objects.filter(pk__in=[1, 3, 5])),
            2: test_helper.QuerySetMatcher(models.AdGroupSource.objects.filter(pk__in=[2, 4])),
        })

    def test_ad_groups_sources_settings_map(self):
        self.assertDictEqual(self.loader.ad_groups_sources_settings_map, {
            1: test_helper.QuerySetMatcher(models.AdGroupSourceSettings.objects.filter(pk__in=[1, 3, 5])),
            2: test_helper.QuerySetMatcher(models.AdGroupSourceSettings.objects.filter(pk__in=[2, 4])),
        })

    def test_settings_map(self):
        self.assertDictEqual(self.loader.settings_map, {
            1: {
                'state': constants.AdGroupSourceSettingsState.ACTIVE,
                'status': constants.AdGroupSourceSettingsState.ACTIVE,
                'daily_budget': Decimal('50.0000'),
                'max_bid_cpc': 0.12,
                'min_bid_cpc': 0.12,
            },
            2: {
                'state': constants.AdGroupSourceSettingsState.INACTIVE,
                'status': constants.AdGroupSourceSettingsState.INACTIVE,
                'daily_budget': None,
                'max_bid_cpc': None,
                'min_bid_cpc': None,
            },
        })

    def test_settings_map_filtered_ad_group_sources(self):
        sources = models.Source.objects.all()
        ad_groups_sources = models.AdGroupSource.objects.filter(pk__in=[2, 3, 4, 5])

        loader = loaders.SourcesLoader(sources, ad_groups_sources)

        self.assertDictEqual(self.loader.settings_map, {
            1: {
                'state': constants.AdGroupSourceSettingsState.ACTIVE,
                'status': constants.AdGroupSourceSettingsState.ACTIVE,
                'daily_budget': Decimal('50.0000'),
                'max_bid_cpc': 0.12,
                'min_bid_cpc': 0.12,
            },
            2: {
                'state': constants.AdGroupSourceSettingsState.INACTIVE,
                'status': constants.AdGroupSourceSettingsState.INACTIVE,
                'daily_budget': None,
                'max_bid_cpc': None,
                'min_bid_cpc': None,
            },
        })


class AdGroupSourcesLoaderTest(TestCase):

    fixtures = ['test_api_breakdowns.yaml']

    def setUp(self):
        sources = models.Source.objects.all()
        ad_groups_sources = models.AdGroupSource.objects.filter(ad_group_id=1)

        self.loader = loaders.SourcesLoader(sources, ad_groups_sources)

    def test_settings_map(self):
        self.assertDictEqual(self.loader.settings_map, {
            1: {
                'state': constants.AdGroupSourceSettingsState.ACTIVE,
                'status': constants.AdGroupSourceSettingsState.ACTIVE,
                'daily_budget': Decimal('50.0000'),
                'max_bid_cpc': 0.12,
                'min_bid_cpc': 0.12,
            },
            2: {
                'state': constants.AdGroupSourceSettingsState.INACTIVE,
                'status': constants.AdGroupSourceSettingsState.INACTIVE,
                'daily_budget': None,
                'max_bid_cpc': None,
                'min_bid_cpc': None,
            },
        })
