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
        self.assertEqual(loaders.get_loader_for_dimension('content_ad_id'), loaders.ContentAdsLoader)
        self.assertEqual(loaders.get_loader_for_dimension('ad_group_id'), loaders.AdGroupsLoader)
        self.assertEqual(loaders.get_loader_for_dimension('campaign_id'), loaders.CampaignsLoader)
        self.assertEqual(loaders.get_loader_for_dimension('account_id'), loaders.AccountsLoader)
        self.assertEqual(loaders.get_loader_for_dimension('source_id'), loaders.SourcesLoader)


class AccountsLoaderTest(TestCase):

    fixtures = ['test_api_breakdowns.yaml']

    def setUp(self):
        accounts = models.Account.objects.all()
        sources = models.Source.objects.all()

        self.loader = loaders.AccountsLoader(accounts, sources)

    def test_from_constraints(self):
        loader = loaders.AccountsLoader.from_constraints(constants.Level.ALL_ACCOUNTS, User.objects.get(pk=1), {
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
            'account_type': constants.AccountType.get_text(constants.AccountType.SELF_MANAGED),
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
            'account_type': constants.AccountType.get_text(constants.AccountType.SELF_MANAGED),
            'settings_id': 1,
        }})


class CampaignsLoaderTest(TestCase):

    fixtures = ['test_api_breakdowns.yaml']

    def setUp(self):
        campaigns = models.Campaign.objects.all()
        sources = models.Source.objects.all()

        self.loader = loaders.CampaignsLoader(campaigns, sources)

    def test_from_constraints(self):
        loader = loaders.CampaignsLoader.from_constraints(constants.Level.ACCOUNTS, User.objects.get(pk=1), {
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
        loader = loaders.AdGroupsLoader.from_constraints(constants.Level.CAMPAIGNS, User.objects.get(pk=1), {
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
        loader = loaders.ContentAdsLoader.from_constraints(constants.Level.AD_GROUPS, User.objects.get(pk=1), {
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
        loader = loaders.SourcesLoader.from_constraints(constants.Level.CAMPAIGNS, User.objects.get(pk=1), {
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
        self.loader = loaders.AdGroupSourcesLoader(sources, models.AdGroup.objects.get(pk=1))

    def test_from_constraints_select_loader_class(self):
        loader = loaders.SourcesLoader.from_constraints(constants.Level.AD_GROUPS, User.objects.get(pk=1), {
            'ad_group': models.AdGroup.objects.get(pk=1),
            'filtered_sources': models.Source.objects.all(),
        })

        self.assertIsInstance(loader, loaders.AdGroupSourcesLoader)
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
                        'message': 'The ad group has end date set in the past. No modifications to media source parameters are possible.',
                        'enabled': False
                    },
                    'daily_budget': {
                        'message': 'The ad group has end date set in the past. No modifications to media source parameters are possible.',
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
                        'message': 'The ad group has end date set in the past. No modifications to media source parameters are possible.',
                        'enabled': False
                    },
                    'daily_budget': {
                        'message': 'The ad group has end date set in the past. No modifications to media source parameters are possible.',
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
