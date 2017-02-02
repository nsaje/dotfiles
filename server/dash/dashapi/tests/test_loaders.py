from django.test import TestCase
from decimal import Decimal
from mock import patch

from zemauth.models import User
from utils import test_helper

from dash import models
from dash import constants
from dash.dashapi import loaders


class GetLoaderTest(TestCase):
    def test_get_loader(self):
        self.assertEqual(loaders.get_loader_for_dimension('content_ad_id', None), loaders.ContentAdsLoader)
        self.assertEqual(loaders.get_loader_for_dimension('ad_group_id', None), loaders.AdGroupsLoader)
        self.assertEqual(loaders.get_loader_for_dimension('campaign_id', None), loaders.CampaignsLoader)
        self.assertEqual(loaders.get_loader_for_dimension('account_id', None), loaders.AccountsLoader)
        self.assertEqual(loaders.get_loader_for_dimension(
            'source_id', constants.Level.ACCOUNTS), loaders.SourcesLoader)
        self.assertEqual(loaders.get_loader_for_dimension(
            'source_id', constants.Level.AD_GROUPS), loaders.AdGroupSourcesLoader)


class AccountsLoaderTest(TestCase):
    fixtures = ['test_api_breakdowns.yaml']

    def setUp(self):
        accounts = models.Account.objects.all()
        sources = models.Source.objects.all()

        self.loader = loaders.AccountsLoader(accounts, sources)

    def test_from_constraints(self):
        loader = loaders.AccountsLoader.from_constraints(User.objects.get(pk=1), {
            'allowed_accounts': models.Account.objects.all(),
            'filtered_sources': models.Source.objects.all(),
        })

        self.assertItemsEqual(loader.objs_ids, self.loader.objs_ids)
        self.assertItemsEqual(loader.settings_map, self.loader.settings_map)

    def test_objs(self):
        self.assertItemsEqual(self.loader.objs_ids, [1])
        self.assertDictEqual(self.loader.objs_map, {
            1: models.Account.objects.get(pk=1)
        })

    def test_settings_map(self):
        self.assertDictEqual(self.loader.settings_map, {1: {
            'archived': False,
            'status': constants.AdGroupRunningStatus.ACTIVE,
            'default_account_manager': 'mad.max@zemanta.com',
            'default_sales_representative': 'supertestuser@test.com',
            'account_type': constants.AccountType.get_text(constants.AccountType.ACTIVATED),
            'settings_id': 1,
        }})

    def test_status_map_filtered_sources(self):
        accounts = models.Account.objects.all()
        sources = models.Source.objects.filter(pk=2)

        loader = loaders.AccountsLoader(accounts, sources)

        self.assertDictEqual(loader.settings_map, {1: {
            'archived': False,
            'status': constants.AdGroupRunningStatus.ACTIVE,
            'default_account_manager': 'mad.max@zemanta.com',
            'default_sales_representative': 'supertestuser@test.com',
            'account_type': constants.AccountType.get_text(constants.AccountType.ACTIVATED),
            'settings_id': 1,
        }})


class CampaignsLoaderTest(TestCase):
    fixtures = ['test_api_breakdowns.yaml']

    def setUp(self):
        campaigns = models.Campaign.objects.all()
        sources = models.Source.objects.all()

        self.loader = loaders.CampaignsLoader(campaigns, sources)

    def test_from_constraints(self):
        loader = loaders.CampaignsLoader.from_constraints(User.objects.get(pk=1), {
            'allowed_campaigns': models.Campaign.objects.all(),
            'filtered_sources': models.Source.objects.all(),
        })

        self.assertItemsEqual(loader.objs_ids, self.loader.objs_ids)
        self.assertItemsEqual(loader.settings_map, self.loader.settings_map)

    def test_objs(self):
        self.assertItemsEqual(self.loader.objs_ids, [1, 2])
        self.assertDictEqual(self.loader.objs_map, {
            1: models.Campaign.objects.get(pk=1),
            2: models.Campaign.objects.get(pk=2),
        })

    def test_settings_map(self):
        self.assertDictEqual(self.loader.settings_map, {
            1: {
                'status': constants.AdGroupRunningStatus.ACTIVE,
                'archived': False,
                'settings_id': 1,
                'campaign_manager': 'supertestuser@test.com',
            },
            2: {
                'status': constants.AdGroupRunningStatus.INACTIVE,
                'archived': True,
                'settings_id': 2,
                'campaign_manager': 'mad.max@zemanta.com',
            }
        })

    def test_status_map_filtered_sources(self):
        campaigns = models.Campaign.objects.all()
        sources = models.Source.objects.filter(pk=2)

        loader = loaders.CampaignsLoader(campaigns, sources)

        self.assertDictEqual(loader.settings_map, {
            1: {
                'status': constants.AdGroupRunningStatus.ACTIVE,
                'archived': False,
                'settings_id': 1,
                'campaign_manager': 'supertestuser@test.com',
            },
            2: {
                'status': constants.AdGroupRunningStatus.INACTIVE,
                'archived': True,
                'settings_id': 2,
                'campaign_manager': 'mad.max@zemanta.com',
            }
        })


class AdGroupsLoaderTest(TestCase):
    fixtures = ['test_api_breakdowns.yaml']

    def setUp(self):
        ad_groups = models.AdGroup.objects.all()
        sources = models.Source.objects.all()

        self.loader = loaders.AdGroupsLoader(ad_groups, sources)

    def test_from_constraints(self):
        loader = loaders.AdGroupsLoader.from_constraints(User.objects.get(pk=1), {
            'allowed_ad_groups': models.AdGroup.objects.all(),
            'filtered_sources': models.Source.objects.all(),
        })

        self.assertItemsEqual(loader.objs_ids, self.loader.objs_ids)
        self.assertItemsEqual(loader.settings_map, self.loader.settings_map)

    def test_settings_map(self):
        self.assertDictEqual(self.loader.settings_map, {
            1: {
                'status': constants.AdGroupRunningStatus.ACTIVE,
                'state': constants.AdGroupRunningStatus.ACTIVE,
                'archived': False,
                'settings_id': 4,
            },
            2: {
                'status': constants.AdGroupRunningStatus.INACTIVE,
                'state': constants.AdGroupRunningStatus.INACTIVE,
                'archived': False,
                'settings_id': 2,
            },
            3: {
                'status': constants.AdGroupRunningStatus.INACTIVE,
                'state': constants.AdGroupRunningStatus.INACTIVE,
                'archived': True,
                'settings_id': 3,
            },
        })

    def test_base_level_settings_map(self):
        self.assertDictEqual(self.loader.base_level_settings_map, {
            1: {
                'campaign_has_available_budget': False,
                'campaign_stop_inactive': True,
            },
            2: {
                'campaign_has_available_budget': False,
                'campaign_stop_inactive': False,
            },
            3: {
                'campaign_has_available_budget': False,
                'campaign_stop_inactive': None,
            },
        })

    def test_objs(self):
        self.assertItemsEqual(self.loader.objs_ids, [1, 2, 3])
        self.assertDictEqual(self.loader.objs_map, {
            1: models.AdGroup.objects.get(pk=1),
            2: models.AdGroup.objects.get(pk=2),
            3: models.AdGroup.objects.get(pk=3),
        })

    def test_status_map_filtered_sources(self):
        ad_groups = models.AdGroup.objects.all()
        sources = models.Source.objects.filter(pk=2)

        loader = loaders.AdGroupsLoader(ad_groups, sources)

        self.assertDictEqual(loader.settings_map, {
            1: {
                'status': constants.AdGroupRunningStatus.ACTIVE,
                'state': constants.AdGroupRunningStatus.ACTIVE,
                'archived': False,
                'settings_id': 4,
            },
            2: {
                'status': constants.AdGroupRunningStatus.INACTIVE,
                'state': constants.AdGroupRunningStatus.INACTIVE,
                'archived': False,
                'settings_id': 2,
            },
            3: {
                'status': constants.AdGroupRunningStatus.INACTIVE,
                'state': constants.AdGroupRunningStatus.INACTIVE,
                'archived': True,
                'settings_id': 3,
            },
        })


class ContentAdLoaderTest(TestCase):
    fixtures = ['test_api_breakdowns.yaml']

    def setUp(self):
        content_ads = models.ContentAd.objects.all()
        sources = models.Source.objects.all()

        self.loader = loaders.ContentAdsLoader(content_ads, sources)

    def test_from_constraints(self):
        loader = loaders.ContentAdsLoader.from_constraints(User.objects.get(pk=1), {
            'allowed_content_ads': models.ContentAd.objects.all(),
            'filtered_sources': models.Source.objects.all(),
        })

        self.assertItemsEqual(loader.objs_ids, self.loader.objs_ids)
        self.assertItemsEqual(loader.status_map, self.loader.status_map)

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

    def test_status_per_source(self):
        self.assertDictEqual(self.loader.per_source_status_map, {
            1: {
                1: {
                    'source_id': 1,
                    'submission_status': 1,
                    'source_name': 'AdsNative',
                    'source_status': 1,
                    'submission_errors': None
                },
                2: {
                    'source_id': 2,
                    'submission_status': 2,
                    'source_name': 'Gravity',
                    'source_status': 2,
                    'submission_errors': None
                }
            },
            2: {
                2: {
                    'source_id': 2,
                    'submission_status': 2,
                    'source_name': 'Gravity',
                    'source_status': 2,
                    'submission_errors': None
                }
            }
        })

    def test_status_per_source_filtered(self):
        content_ads = models.ContentAd.objects.all()
        sources = models.Source.objects.filter(pk=1)

        loader = loaders.ContentAdsLoader(content_ads, sources)
        self.assertDictEqual(loader.per_source_status_map, {
            1: {
                1: {
                    'source_id': 1,
                    'submission_status': 1,
                    'source_name': 'AdsNative',
                    'source_status': 1,
                    'submission_errors': None
                },
            },
        })


class SourcesLoaderTest(TestCase):
    fixtures = ['test_api_breakdowns.yaml']

    def setUp(self):
        sources = models.Source.objects.all()
        self.loader = loaders.SourcesLoader(sources, models.AdGroup.objects.all())

    def test_from_constraints(self):
        loader = loaders.SourcesLoader.from_constraints(User.objects.get(pk=1), {
            'allowed_ad_groups': models.AdGroup.objects.all(),
            'filtered_sources': models.Source.objects.all(),
        })

        self.assertItemsEqual(loader.objs_ids, self.loader.objs_ids)
        self.assertItemsEqual(loader.settings_map, self.loader.settings_map)

    def test_objs(self):
        self.assertItemsEqual(self.loader.objs_ids, [1, 2])
        self.assertDictEqual(self.loader.objs_map, {
            1: models.Source.objects.get(pk=1),
            2: models.Source.objects.get(pk=2),
        })

    def test_settings_map(self):
        self.assertDictEqual(self.loader.settings_map, {
            1: {},
            2: {},
        })

    def test_settings_map_filtered_ad_group_sources(self):
        sources = models.Source.objects.filter(pk=2)
        loader = loaders.SourcesLoader(sources, models.AdGroup.objects.all())

        self.assertDictEqual(loader.settings_map, {
            2: {},
        })


class AdGroupSourcesLoaderTest(TestCase):
    fixtures = ['test_api_breakdowns.yaml']

    def setUp(self):
        sources = models.Source.objects.all()
        self.loader = loaders.AdGroupSourcesLoader(sources, models.AdGroup.objects.get(pk=1), User.objects.get(pk=1))

    def test_from_constraints_select_loader_class(self):
        loader = loaders.AdGroupSourcesLoader.from_constraints(User.objects.get(pk=1), {
            'ad_group': models.AdGroup.objects.get(pk=1),
            'filtered_sources': models.Source.objects.all(),
        })

        self.assertItemsEqual(loader.objs_ids, self.loader.objs_ids)
        self.assertItemsEqual(loader.settings_map, self.loader.settings_map)

    def test_objs(self):
        self.assertItemsEqual(self.loader.objs_ids, [1, 2])
        self.assertDictEqual(self.loader.objs_map, {
            1: models.Source.objects.get(pk=1),
            2: models.Source.objects.get(pk=2),
        })

    def test_status_with_blockers(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        ad_group_source.blockers = {'test-blocker': 'My blocker'}
        ad_group_source.save()
        source = self.loader.settings_map[1]
        self.assertEqual(source['status'], 2)
        self.assertEqual(source['notifications'], {
            'important': True,
            'message': 'This media source is enabled but it is not running because: My blocker',
        })

    def test_settings_map_all_rtb_enabled(self):
        self.loader.ad_group_settings.b1_sources_group_enabled = True
        self.loader.ad_group_settings.b1_sources_group_state = 1

        rtb_source = self.loader.settings_map[1]
        reg_source = self.loader.settings_map[2]

        rtb_source = self.loader.settings_map[1]
        self.assertEqual(rtb_source['state'], 1)
        self.assertEqual(rtb_source['status'], 1)
        self.assertEqual(rtb_source['daily_budget'], None)
        self.assertEqual(rtb_source['editable_fields']['daily_budget']['enabled'], False)

        self.assertEqual(reg_source['state'], 2)
        self.assertEqual(reg_source['status'], 2)
        self.assertEqual(reg_source['daily_budget'], Decimal('20.0'))
        self.assertEqual(reg_source['editable_fields']['daily_budget']['enabled'], False)

    def test_settings_map_all_rtb_enabled_and_inactive(self):
        self.loader.ad_group_settings.b1_sources_group_enabled = True
        self.loader.ad_group_settings.b1_sources_group_state = 2

        rtb_source = self.loader.settings_map[1]
        self.assertEqual(rtb_source['state'], 1)
        self.assertEqual(rtb_source['status'], 2)
        self.assertEqual(rtb_source['daily_budget'], None)
        self.assertEqual(rtb_source['editable_fields']['daily_budget']['enabled'], False)

    def test_settings_map(self):
        self.assertDictEqual(self.loader.settings_map, {
            1: {
                'state': 1,
                'status': 1,
                'supply_dash_disabled_message': "This media source doesn't have a dashboard of its own. All campaign management is done through Zemanta One dashboard.",
                'daily_budget': Decimal('10.0000'),
                'cpc': Decimal('0.5010'),
                'editable_fields': {
                    'state': {
                        'message': 'This source must be managed manually.',
                        'enabled': False
                    },
                    'bid_cpc': {
                        'message': 'This value cannot be edited because the ad group is on Autopilot.',
                        'enabled': False
                    },
                    'daily_budget': {
                        'message': 'This value cannot be edited because the ad group is on Autopilot.',
                        'enabled': False
                    }
                },
                'supply_dash_url': None,
                'notifications': {},
            },
            2: {
                'state': 2,
                'status': 2,
                'supply_dash_disabled_message': "This media source doesn't have a dashboard of its own. All campaign management is done through Zemanta One dashboard.",
                'daily_budget': Decimal('20.0000'),
                'cpc': Decimal('0.5020'),
                'editable_fields': {
                    'state': {
                        'message': 'Please add additional budget to your campaign to make changes.',
                        'enabled': False
                    },
                    'bid_cpc': {
                        'message': 'This value cannot be edited because the ad group is on Autopilot.',
                        'enabled': False
                    },
                    'daily_budget': {
                        'message': 'This value cannot be edited because the ad group is on Autopilot.',
                        'enabled': False
                    }
                },
                'supply_dash_url': None,
                'notifications': {},
            }
        })

    def test_totals(self):
        # only use active ad group sources
        self.assertDictEqual(self.loader.totals, {
            'daily_budget': Decimal('10.0000'),
            'current_daily_budget': Decimal('10.0000'),
        })

    def test_totals_all_rtb_enabled(self):
        self.loader.ad_group_settings.b1_sources_group_enabled = True
        self.loader.ad_group_settings.b1_sources_group_daily_budget = Decimal('100.00')
        self.loader.ad_group_settings.b1_sources_group_state = 1
        self.assertDictEqual(self.loader.totals, {
            'daily_budget': Decimal('100.0000'),
            'current_daily_budget': Decimal('100.0000'),
        })

    def test_totals_all_rtb_enabled_and_inactive(self):
        self.loader.ad_group_settings.b1_sources_group_enabled = True
        self.loader.ad_group_settings.b1_sources_group_daily_budget = Decimal('100.00')
        self.loader.ad_group_settings.b1_sources_group_state = 2
        self.assertDictEqual(self.loader.totals, {
            'daily_budget': Decimal('0'),
            'current_daily_budget': Decimal('0'),
        })
