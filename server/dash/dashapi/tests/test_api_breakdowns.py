import datetime
from decimal import Decimal
from mock import patch

from django.test import TestCase, override_settings

from utils.dict_helper import dict_join
from zemauth.models import User

from dash import models
from dash import threads
from dash.constants import Level, PublisherBlacklistLevel
from dash.dashapi import api_breakdowns
from dash.dashapi import helpers
from dash.dashapi import augmenter


"""
NOTE 1: The following dicts represent rows that are returned by dashapi.api_breakdowns query functions.
Whenever a new field is added to augmenter/loader, add it here so that all instances of the row
get updated.

NOTE 2: To check for correct results use "assertEqual" and not "assertItemsEqual" as the order in which results
are returned matters.
"""


START_DATE, END_DATE = datetime.date(2016, 7, 1), datetime.date(2016, 8, 31)

SOURCE_1 = {'archived': False, 'maintenance': False, 'name': 'AdsNative', 'source_id': 1, 'source_slug': 'adsnative', 'id': 1}  # noqa
SOURCE_2 = {'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2, 'source_slug': 'gravity', 'id': 2}  # noqa

ACCOUNT_1 = {
    'account_id': 1, 'archived': False, 'name': 'test account 1', 'status': 1,
    'default_account_manager': 'mad.max@zemanta.com', 'default_sales_representative': 'supertestuser@test.com',
    'agency': '', 'account_type': 'Activated',
    'pacing': None, 'allocated_budgets': Decimal('0'), 'spend_projection': Decimal('0'),
    'license_fee_projection': Decimal('0'), 'flat_fee': 0, 'total_fee': 0, 'total_fee_projection': Decimal('0'),
}

CAMPAIGN_1 = {
    'campaign_id': 1, 'archived': False, 'name': 'test campaign 1', 'status': 1,
    'campaign_manager': 'supertestuser@test.com',
    'pacing': None, 'allocated_budgets': None, 'spend_projection': None, 'license_fee_projection': None,
}
CAMPAIGN_2 = {
    'campaign_id': 2, 'archived': True, 'name': 'test campaign 2', 'status': 2,
    'campaign_manager': 'mad.max@zemanta.com',
    'pacing': None, 'allocated_budgets': None, 'spend_projection': None, 'license_fee_projection': None,
}

AD_GROUP_1 = {'ad_group_id': 1, 'archived': False, 'name': 'test adgroup 1', 'status': 1, 'state': 1}
AD_GROUP_2 = {'ad_group_id': 2, 'archived': False, 'name': 'test adgroup 2', 'status': 2, 'state': 2}

AD_GROUP_BASE_1 = dict_join(AD_GROUP_1, {'campaign_has_available_budget': False, 'campaign_stop_inactive': True})
AD_GROUP_BASE_2 = dict_join(AD_GROUP_2, {'campaign_has_available_budget': False, 'campaign_stop_inactive': False})

CONTENT_AD_1 = {
    'content_ad_id': 1, 'title': 'Title 1', 'description': 'Example description', 'brand_name': 'Example',
    'archived': False, 'name': 'Title 1', 'display_url': 'example.com', 'call_to_action': 'Call to action', 'label': '',
    'image_hash': '100', 'image_urls': {
        'square': '/100.jpg?w=160&h=160&fit=crop&crop=center&fm=jpg',
        'landscape': '/100.jpg?w=256&h=160&fit=crop&crop=center&fm=jpg'
    },
    'batch_id': 1, 'batch_name': 'batch 1', 'upload_time': datetime.datetime(2015, 2, 23, 0, 0),
    'redirector_url': 'http://r1.zemanta.com/b/r1/z1/1/1/', 'url': 'http://testurl1.com',
    'state': 1, 'status': 1, 'status_per_source': {
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
}
CONTENT_AD_2 = {
    'content_ad_id': 2, 'title': 'Title 2', 'description': 'Example description', 'brand_name': 'Example',
    'archived': False, 'name': 'Title 2', 'display_url': 'example.com', 'call_to_action': 'Call to action', 'label': '',
    'image_hash': '200', 'image_urls': {
        'square': '/200.jpg?w=160&h=160&fit=crop&crop=center&fm=jpg',
        'landscape': '/200.jpg?w=256&h=160&fit=crop&crop=center&fm=jpg'
    },
    'batch_id': 1, 'batch_name': 'batch 1', 'upload_time': datetime.datetime(2015, 2, 23, 0, 0),
    'redirector_url': 'http://r1.zemanta.com/b/r2/z1/1/2/', 'url': 'http://testurl2.com',
    'state': 2, 'status': 2, 'status_per_source': {
        2: {
            'source_id': 2,
            'submission_status': 2,
            'source_name': 'Gravity',
            'source_status': 2,
            'submission_errors': None
        }
    },
}

# sources on ad group level
AD_GROUP_SOURCE_1 = {
    'source_id': 1, 'source_slug': 'adsnative', 'id': 1, 'name': 'AdsNative',
    'daily_budget': Decimal('10.0000'), 'current_daily_budget': Decimal('10.0000'),
    'bid_cpc': Decimal('0.5010'), 'current_bid_cpc': Decimal('0.5010'),
    'archived': False, 'maintenance': False,
    'supply_dash_url': None,
    'supply_dash_disabled_message': "This media source doesn't have a dashboard of its own. All campaign management is done through Zemanta One dashboard.",  # noqa
    'state': 1, 'status': 1,
    'editable_fields': {
        'state': {
            'message': 'This source must be managed manually.',
            'enabled': False
        },
        'bid_cpc': {
            'message': 'The ad group has end date set in the past. No modifications to media source parameters are possible.',  # noqa
            'enabled': False
        },
        'daily_budget': {
            'message': 'The ad group has end date set in the past. No modifications to media source parameters are possible.',  # noqa
            'enabled': False
        }
    },
    'notifications': {},
}
AD_GROUP_SOURCE_2 = {
    'source_id': 2, 'source_slug': 'gravity', 'id': 2, 'name': 'Gravity',
    'daily_budget': Decimal('20.0000'), 'current_daily_budget': Decimal('20.0000'),
    'bid_cpc': Decimal('0.5020'), 'current_bid_cpc': Decimal('0.5020'),
    'archived': False, 'maintenance': False,
    'supply_dash_url': None,
    'supply_dash_disabled_message': "This media source doesn't have a dashboard of its own. All campaign management is done through Zemanta One dashboard.",  # noqa
    'state': 2, 'status': 2, 'editable_fields': {
        'state': {
            'message': 'Please add additional budget to your campaign to make changes.',
            'enabled': False
        },
        'bid_cpc': {
            'message': 'The ad group has end date set in the past. No modifications to media source parameters are possible.',  # noqa
            'enabled': False
        },
        'daily_budget': {
            'message': 'The ad group has end date set in the past. No modifications to media source parameters are possible.',  # noqa
            'enabled': False
        }
    },
    'notifications': {},
}

SOURCE_1__CONTENT_AD_1 = {
    'source_id': 1,
    'content_ad_id': 1, 'title': 'Title 1', 'description': 'Example description', 'brand_name': 'Example',
    'archived': False, 'name': 'Title 1', 'display_url': 'example.com', 'call_to_action': 'Call to action', 'label': '',
    'image_hash': '100', 'image_urls': {
        'square': '/100.jpg?w=160&h=160&fit=crop&crop=center&fm=jpg',
        'landscape': '/100.jpg?w=256&h=160&fit=crop&crop=center&fm=jpg'
    },
    'batch_id': 1, 'batch_name': 'batch 1', 'upload_time': datetime.datetime(2015, 2, 23, 0, 0),
    'redirector_url': 'http://r1.zemanta.com/b/r1/z1/1/1/', 'url': 'http://testurl1.com',
    'state': 1, 'status': 1, 'status_per_source': {
        1: {
            'source_id': 1,
            'submission_status': 1,
            'source_name': 'AdsNative',
            'source_status': 1,
            'submission_errors': None
        },
    },
}

PUBLISHER_1__SOURCE_1 = {
    'publisher_id': 'pub1.com__1', 'publisher': 'pub1.com', 'domain': 'pub1.com', 'name': 'pub1.com', 'domain_link': 'http://pub1.com',  # noqa
    'source_id': 1, 'source_name': 'AdsNative', 'exchange': 'AdsNative', 'source_slug': 'adsnative',
    'status': 2, 'blacklisted': 'Blacklisted', 'blacklisted_level': PublisherBlacklistLevel.ADGROUP,
    'blacklisted_level_description': PublisherBlacklistLevel.verbose(PublisherBlacklistLevel.ADGROUP),
    'can_blacklist_publisher': True,
    'notifications': {
        'message': PublisherBlacklistLevel.verbose(PublisherBlacklistLevel.ADGROUP)
    },
}
PUBLISHER_2__SOURCE_1 = {
    'publisher_id': 'pub2.com__1', 'publisher': 'pub2.com', 'domain': 'pub2.com', 'name': 'pub2.com', 'domain_link': 'http://pub2.com',  # noqa
    'source_id': 1, 'source_name': 'AdsNative', 'exchange': 'AdsNative', 'source_slug': 'adsnative',
    'status': 1, 'blacklisted': 'Active', 'can_blacklist_publisher': True,
}
PUBLISHER_2__SOURCE_2 = {
    'publisher_id': 'pub2.com__2', 'publisher': 'pub2.com', 'domain': 'pub2.com', 'name': 'pub2.com', 'domain_link': 'http://pub2.com',  # noqa
    'source_id': 2, 'source_name': 'Gravity', 'exchange': 'Gravity', 'source_slug': 'gravity',
    'status': 2, 'blacklisted': 'Blacklisted', 'blacklisted_level': PublisherBlacklistLevel.CAMPAIGN,
    'blacklisted_level_description': PublisherBlacklistLevel.verbose(PublisherBlacklistLevel.CAMPAIGN),
    'can_blacklist_publisher': False,
    'notifications': {
        'message': PublisherBlacklistLevel.verbose(PublisherBlacklistLevel.CAMPAIGN)
    },
}
PUBLISHER_3__SOURCE_1 = {
    'publisher_id': 'pub3.com__1', 'publisher': 'pub3.com', 'name': 'pub3.com', 'domain': 'pub3.com', 'domain_link': 'http://pub3.com',  # noqa
    'source_id': 1, 'source_name': 'AdsNative', 'exchange': 'AdsNative', 'source_slug': 'adsnative',
    'status': 2, 'blacklisted': 'Blacklisted', 'blacklisted_level': PublisherBlacklistLevel.ACCOUNT,
    'blacklisted_level_description': PublisherBlacklistLevel.verbose(PublisherBlacklistLevel.ACCOUNT),
    'can_blacklist_publisher': True,
    'notifications': {
        'message': PublisherBlacklistLevel.verbose(PublisherBlacklistLevel.ACCOUNT)
    },
}
PUBLISHER_3__SOURCE_2 = {
    'publisher_id': 'pub3.com__2', 'publisher': 'pub3.com', 'name': 'pub3.com', 'domain': 'pub3.com', 'domain_link': 'http://pub3.com',  # noqa
    'source_id': 2, 'source_name': 'Gravity', 'exchange': 'Gravity', 'source_slug': 'gravity',
    'status': 1, 'blacklisted': 'Active', 'can_blacklist_publisher': False,
}
PUBLISHER_4__SOURCE_2 = {
    'publisher_id': 'pub4.com__2', 'publisher': 'pub4.com', 'name': 'pub4.com', 'domain': 'pub4.com', 'domain_link': 'http://pub4.com',  # noqa
    'source_id': 2, 'source_name': 'Gravity', 'exchange': 'Gravity', 'source_slug': 'gravity',
    'status': 2, 'blacklisted': 'Blacklisted', 'blacklisted_level': PublisherBlacklistLevel.GLOBAL,
    'blacklisted_level_description': PublisherBlacklistLevel.verbose(PublisherBlacklistLevel.GLOBAL),
    'can_blacklist_publisher': False,
    'notifications': {
        'message': PublisherBlacklistLevel.verbose(PublisherBlacklistLevel.GLOBAL)
    },
}


@patch('dash.threads.AsyncFunction', threads.MockAsyncFunction)
@override_settings(R1_BLANK_REDIRECT_URL='http://r1.zemanta.com/b/{redirect_id}/z1/1/{content_ad_id}/')
class QueryTest(TestCase):

    fixtures = ['test_api_breakdowns.yaml']

    def test_query_all_accounts_break_account(self):
        rows = api_breakdowns.query(
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ['account_id'],
            {
                'date__gte': datetime.date(2016, 7, 1),
                'date__lte': datetime.date(2016, 7, 31),
                'allowed_accounts': models.Account.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            },
            None,
            'name', 0, 1
        )

        self.assertEqual(rows, [ACCOUNT_1])

    def test_query_all_accounts_break_source(self):
        rows = api_breakdowns.query(
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ['source_id'],
            {
                'allowed_accounts': models.Account.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            },
            None,
            'name', 0, 2
        )

        self.assertEqual(rows, [SOURCE_1, SOURCE_2])

    def test_query_all_accounts_break_account_source(self):
        rows = api_breakdowns.query(
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ['account_id', 'source_id'],
            {
                'allowed_accounts': models.Account.objects.all(),
                'allowed_campaigns': models.Campaign.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            },
            [{'account_id': 1}],
            'name', 0, 2
        )

        self.assertEqual(rows, [
            dict_join({'account_id': 1}, SOURCE_1),
            dict_join({'account_id': 1}, SOURCE_2),
        ])

    def test_query_all_accounts_break_source_account(self):
        rows = api_breakdowns.query(
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ['source_id', 'account_id'],
            {
                'date__gte': datetime.date(2016, 7, 1),
                'date__lte': datetime.date(2016, 7, 31),
                'allowed_accounts': models.Account.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            },
            [{'source_id': 1}, {'source_id': 2}],
            'name', 0, 1
        )

        self.assertEqual(rows, [
            dict_join({'source_id': 1}, ACCOUNT_1),
            dict_join({'source_id': 2}, ACCOUNT_1),
        ])

    def test_query_all_accounts_break_source_campaign(self):
        rows = api_breakdowns.query(
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ['source_id', 'campaign_id'],
            {
                'date__gte': datetime.date(2016, 7, 1),
                'date__lte': datetime.date(2016, 7, 31),
                'allowed_accounts': models.Account.objects.all(),
                'allowed_campaigns': models.Campaign.objects.filter(pk=1),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            },
            [{'source_id': 1}, {'source_id': 2}],
            'name', 0, 1
        )

        self.assertEqual(rows, [
            dict_join({'source_id': 1}, CAMPAIGN_1),
            dict_join({'source_id': 2}, CAMPAIGN_1),
        ])

    def test_query_all_accounts_break_account_campaign(self):
        rows = api_breakdowns.query(
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ['account_id', 'campaign_id'],
            {
                'date__gte': datetime.date(2016, 7, 1),
                'date__lte': datetime.date(2016, 7, 31),
                'allowed_accounts': models.Account.objects.all(),
                'allowed_campaigns': models.Campaign.objects.filter(pk=1),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            },
            [{'account_id': 1}, {'account_id': 2}],
            'name', 0, 1
        )

        self.assertEqual(rows, [
            dict_join({'account_id': 1}, CAMPAIGN_1),
        ])

    def test_query_accounts_break_campaign(self):
        rows = api_breakdowns.query(
            Level.ACCOUNTS,
            User.objects.get(pk=1),
            ['campaign_id'],
            {
                'date__gte': datetime.date(2016, 7, 1),
                'date__lte': datetime.date(2016, 7, 31),
                'account': models.Account.objects.get(pk=1),
                'allowed_campaigns': models.Campaign.objects.filter(account_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            None,
            'name', 0, 2
        )

        self.assertEqual(rows,  [CAMPAIGN_1, CAMPAIGN_2])

    def test_query_accounts_break_source(self):
        rows = api_breakdowns.query(
            Level.ACCOUNTS,
            User.objects.get(pk=1),
            ['source_id'],
            {
                'account': models.Account.objects.get(pk=1),
                'allowed_campaigns': models.Campaign.objects.filter(account_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            None,
            'name', 0, 2
        )

        self.assertEqual(rows,  [SOURCE_1, SOURCE_2])

    def test_query_accounts_break_campaign_source(self):
        rows = api_breakdowns.query(
            Level.ACCOUNTS,
            User.objects.get(pk=1),
            ['campaign_id', 'source_id'],
            {
                'account': models.Account.objects.get(pk=1),
                'allowed_campaigns': models.Campaign.objects.filter(account_id=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign__account_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            [{'campaign_id': 1}, {'campaign_id': 2}],
            'name', 0, 2
        )

        self.assertEqual(rows,  [
            dict_join({'campaign_id': 1}, SOURCE_1),
            dict_join({'campaign_id': 1}, SOURCE_2),
            dict_join({'campaign_id': 2}, SOURCE_1),
        ])

    def test_query_accounts_break_source_campaign(self):
        rows = api_breakdowns.query(
            Level.ACCOUNTS,
            User.objects.get(pk=1),
            ['source_id', 'campaign_id'],
            {
                'date__gte': datetime.date(2016, 7, 1),
                'date__lte': datetime.date(2016, 7, 31),
                'account': models.Account.objects.get(pk=1),
                'allowed_campaigns': models.Campaign.objects.filter(account_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            [{'source_id': 1}, {'source_id': 2}],
            'name', 0, 2
        )

        self.assertEqual(rows,  [
            dict_join({'source_id': 1}, CAMPAIGN_1),
            dict_join({'source_id': 1}, CAMPAIGN_2),
            dict_join({'source_id': 2}, CAMPAIGN_1),
        ])

    def test_query_accounts_break_source_ad_group(self):
        rows = api_breakdowns.query(
            Level.ACCOUNTS,
            User.objects.get(pk=1),
            ['source_id', 'ad_group_id'],
            {
                'account': models.Account.objects.get(pk=1),
                'allowed_campaigns': models.Campaign.objects.filter(pk=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            [{'source_id': 1}, {'source_id': 2}],
            'name', 0, 2
        )

        self.assertEqual(rows,  [
            dict_join({'source_id': 1}, AD_GROUP_1),
            dict_join({'source_id': 1}, AD_GROUP_2),
            dict_join({'source_id': 2}, AD_GROUP_1),
            dict_join({'source_id': 2}, AD_GROUP_2),
        ])

    def test_query_accounts_break_campaign_ad_group_not_allowed(self):
        rows = api_breakdowns.query(
            Level.ACCOUNTS,
            User.objects.get(pk=1),
            ['campaign_id', 'ad_group_id'],
            {
                'account': models.Account.objects.get(pk=1),
                'allowed_campaigns': models.Campaign.objects.filter(pk=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            [{'campaign_id': 1}, {'campaign_id': 2}],  # campaign 2 is not allowed
            'name', 0, 2
        )

        # campaign_id: 2 does not get queried
        self.assertEqual(rows, [
            dict_join({'campaign_id': 1}, AD_GROUP_1),
            dict_join({'campaign_id': 1}, AD_GROUP_2),
        ])

    def test_query_accounts_break_campaign_ad_group(self):
        rows = api_breakdowns.query(
            Level.ACCOUNTS,
            User.objects.get(pk=1),
            ['campaign_id', 'ad_group_id'],
            {
                'account': models.Account.objects.get(pk=1),
                'allowed_campaigns': models.Campaign.objects.filter(pk=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            [{'campaign_id': 1}],
            'name', 0, 2
        )

        self.assertEqual(rows, [
            dict_join({'campaign_id': 1}, AD_GROUP_1),
            dict_join({'campaign_id': 1}, AD_GROUP_2),
        ])

    def test_query_campaigns_break_ad_group(self):
        rows = api_breakdowns.query(
            Level.CAMPAIGNS,
            User.objects.get(pk=1),
            ['ad_group_id'],
            {
                'campaign': models.Campaign.objects.get(pk=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            None,
            'name', 0, 2
        )

        self.assertEqual(rows,  [AD_GROUP_BASE_1, AD_GROUP_BASE_2])

    def test_query_campaigns_break_source(self):
        rows = api_breakdowns.query(
            Level.CAMPAIGNS,
            User.objects.get(pk=1),
            ['source_id'],
            {
                'campaign': models.Campaign.objects.get(pk=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            None,
            'name', 0, 2
        )

        self.assertEqual(rows,  [SOURCE_1, SOURCE_2])

    def test_query_campaigns_break_ad_group_source(self):
        rows = api_breakdowns.query(
            Level.CAMPAIGNS,
            User.objects.get(pk=1),
            ['ad_group_id', 'source_id'],
            {
                'campaign': models.Campaign.objects.get(pk=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign_id=1),
                'allowed_content_ads': models.ContentAd.objects.filter(ad_group__campaign_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            [{'ad_group_id': 1}, {'ad_group_id': 2}],
            'name', 0, 2
        )

        self.assertEqual(rows,  [
            dict_join({'ad_group_id': 1}, SOURCE_1),
            dict_join({'ad_group_id': 1}, SOURCE_2),
            dict_join({'ad_group_id': 2}, SOURCE_1),
            dict_join({'ad_group_id': 2}, SOURCE_2),
        ])

    def test_query_campaigns_break_source_ad_group(self):
        rows = api_breakdowns.query(
            Level.CAMPAIGNS,
            User.objects.get(pk=1),
            ['source_id', 'ad_group_id'],
            {
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign_id=1),
                'campaign': models.Campaign.objects.get(pk=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            [{'source_id': 1}, {'source_id': 2}],
            'name', 0, 2
        )

        self.assertEqual(rows,  [
            dict_join({'source_id': 1}, AD_GROUP_1),
            dict_join({'source_id': 1}, AD_GROUP_2),
            dict_join({'source_id': 2}, AD_GROUP_1),
            dict_join({'source_id': 2}, AD_GROUP_2),
        ])

    def test_query_ad_groups_break_content_ad(self):
        rows = api_breakdowns.query(
            Level.AD_GROUPS,
            User.objects.get(pk=1),
            ['content_ad_id'],
            {
                'ad_group': models.AdGroup.objects.get(pk=1),
                'allowed_content_ads': models.ContentAd.objects.filter(ad_group=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            None,
            'name', 0, 2
        )

        self.assertEqual(rows,  [CONTENT_AD_1, CONTENT_AD_2])

    def test_query_ad_groups_break_content_ad_source(self):
        rows = api_breakdowns.query(
            Level.AD_GROUPS,
            User.objects.get(pk=1),
            ['content_ad_id', 'source_id'],
            {
                'ad_group': models.AdGroup.objects.get(pk=1),
                'allowed_content_ads': models.ContentAd.objects.filter(ad_group=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            [{'content_ad_id': 1}],
            'name', 0, 2
        )

        self.assertEqual(rows,  [
            dict_join({'content_ad_id': 1}, AD_GROUP_SOURCE_1),
            dict_join({'content_ad_id': 1}, AD_GROUP_SOURCE_2),
        ])

    def test_query_ad_groups_break_source(self):
        rows = api_breakdowns.query(
            Level.AD_GROUPS,
            User.objects.get(pk=1),
            ['source_id'],
            {
                'ad_group': models.AdGroup.objects.get(pk=1),
                'allowed_content_ads': models.ContentAd.objects.filter(ad_group=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            None,
            'name', 0, 2
        )

        self.assertEqual(rows,  [AD_GROUP_SOURCE_1, AD_GROUP_SOURCE_2])

    def test_query_ad_groups_break_source_content_ad(self):
        rows = api_breakdowns.query(
            Level.AD_GROUPS,
            User.objects.get(pk=1),
            ['source_id', 'content_ad_id'],
            {
                'ad_group': models.AdGroup.objects.get(pk=1),
                'allowed_content_ads': models.ContentAd.objects.filter(pk=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            [{'source_id': 1}],
            'name', 0, 2
        )

        self.assertEqual(rows,  [SOURCE_1__CONTENT_AD_1])

    def test_query_ad_groups_break_publishers(self):
        # this query is not used in the wild as we always perform RS query and than dash for publishers
        rows = api_breakdowns.query(
            Level.AD_GROUPS,
            User.objects.get(pk=1),
            ['publisher_id'],
            {
                'ad_group': models.AdGroup.objects.get(pk=1),
                'allowed_content_ads': models.ContentAd.objects.filter(ad_group=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
                'publisher_blacklist': models.PublisherBlacklist.objects.all(),
            },
            None,
            'name', 0, 4
        )

        self.assertEqual(rows, [PUBLISHER_1__SOURCE_1, PUBLISHER_2__SOURCE_2, PUBLISHER_3__SOURCE_1, PUBLISHER_4__SOURCE_2])


@patch('dash.threads.AsyncFunction', threads.MockAsyncFunction)
@override_settings(R1_BLANK_REDIRECT_URL='http://r1.zemanta.com/b/{redirect_id}/z1/1/{content_ad_id}/')
class QueryOrderTest(TestCase):

    fixtures = ['test_api_breakdowns.yaml']

    def test_query_campaigns_break_ad_group(self):
        rows = api_breakdowns.query(
            Level.CAMPAIGNS,
            User.objects.get(pk=1),
            ['ad_group_id'],
            {
                'campaign': models.Campaign.objects.get(pk=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            None,
            'name', 0, 2
        )

        self.assertEqual(rows,  [AD_GROUP_BASE_1, AD_GROUP_BASE_2])

        rows = api_breakdowns.query(
            Level.CAMPAIGNS,
            User.objects.get(pk=1),
            ['ad_group_id'],
            {
                'campaign': models.Campaign.objects.get(pk=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            None,
            '-name', 0, 2
        )

        self.assertEqual(rows,  [AD_GROUP_BASE_2, AD_GROUP_BASE_1])

    def test_query_campaigns_break_source(self):
        rows = api_breakdowns.query(
            Level.CAMPAIGNS,
            User.objects.get(pk=1),
            ['source_id'],
            {
                'campaign': models.Campaign.objects.get(pk=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            None,
            'name', 0, 2
        )

        self.assertEqual(rows,  [SOURCE_1, SOURCE_2])

        rows = api_breakdowns.query(
            Level.CAMPAIGNS,
            User.objects.get(pk=1),
            ['source_id'],
            {
                'campaign': models.Campaign.objects.get(pk=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            None,
            '-name', 0, 2
        )

        self.assertEqual(rows,  [SOURCE_2, SOURCE_1])


@patch('dash.threads.AsyncFunction', threads.MockAsyncFunction)
@override_settings(R1_BLANK_REDIRECT_URL='http://r1.zemanta.com/b/{redirect_id}/z1/1/{content_ad_id}/')
class QueryForRowsTest(TestCase):

    fixtures = ['test_api_breakdowns.yaml']

    def test_query_for_rows_all_accounts_break_account(self):
        rows = api_breakdowns.query_for_rows(
            [
                {'account_id': 1, 'clicks': 1},
            ],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ['account_id'],
            {
                'date__gte': datetime.date(2016, 7, 1),
                'date__lte': datetime.date(2016, 7, 31),
                'allowed_accounts': models.Account.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            }, None,
            'clicks', 0, 2,
            [
                {'account_id': 1}
            ]
        )

        self.assertEqual(rows, [ACCOUNT_1])

    def test_query_for_rows_all_accounts_break_account_no_rows(self):
        rows = api_breakdowns.query_for_rows(
            [],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ['account_id'],
            {
                'date__gte': datetime.date(2016, 7, 1),
                'date__lte': datetime.date(2016, 7, 31),
                'allowed_accounts': models.Account.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            }, None,
            'clicks', 0, 2,
            []
        )

        self.assertEqual(rows, [ACCOUNT_1])

    def test_query_for_rows_all_accounts_break_source(self):
        rows = api_breakdowns.query_for_rows(
            [
                {'source_id': 1, 'clicks': 11},
                {'source_id': 2, 'clicks': 22},
            ],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ['source_id'],
            {
                'allowed_accounts': models.Account.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            }, None, 'clicks', 0, 2,
            [
                {'source_id': 1, 'clicks': 11},
                {'source_id': 2, 'clicks': 22},
            ]
        )

        self.assertEqual(rows, [SOURCE_1, SOURCE_2])

    def test_query_for_rows_all_accounts_break_source_missing_row(self):
        rows = api_breakdowns.query_for_rows(
            [
                {'source_id': 1, 'clicks': 11},
            ],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ['source_id'],
            {
                'allowed_accounts': models.Account.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            }, None, 'clicks', 0, 2,
            [
                {'source_id': 1},
            ]
        )

        self.assertEqual(rows, [SOURCE_1, SOURCE_2])

    def test_query_for_rows_all_accounts_break_source_new_request(self):
        rows = api_breakdowns.query_for_rows(
            [],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ['source_id'],
            {
                'allowed_accounts': models.Account.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            }, None, 'clicks', 1, 2,
            [
                {'source_id': 1},
            ]
        )

        self.assertEqual(rows, [SOURCE_2])

    def test_query_for_rows_all_accounts_break_account_source(self):
        rows = api_breakdowns.query_for_rows(
            [
                {'account_id': 1, 'source_id': 1, 'clicks': 11},
                {'account_id': 1, 'source_id': 2, 'clicks': 12},
            ],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ['account_id', 'source_id'],
            {
                'allowed_accounts': models.Account.objects.all(),
                'allowed_campaigns': models.Campaign.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            },
            [
                {'account_id': 1},
            ],
            'clicks', 0, 2,
            [
                {'account_id': 1, 'source_id': 1},
                {'account_id': 1, 'source_id': 2},
            ])

        self.assertEqual(rows, [
            dict_join({'account_id': 1}, SOURCE_1),
            dict_join({'account_id': 1}, SOURCE_2),
        ])

    def test_query_for_rows_all_accounts_break_account_source_missing_row(self):
        rows = api_breakdowns.query_for_rows(
            [
                {'account_id': 1, 'source_id': 1, 'clicks': 11},
            ],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ['account_id', 'source_id'],
            {
                'allowed_accounts': models.Account.objects.all(),
                'allowed_campaigns': models.Campaign.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            },
            [
                {'account_id': 1},
            ],
            'clicks', 0, 2,
            [
                {'account_id': 1, 'source_id': 1},
            ])

        self.assertEqual(rows, [
            dict_join({'account_id': 1}, SOURCE_1),
            dict_join({'account_id': 1}, SOURCE_2),
        ])

    def test_query_for_rows_all_accounts_break_account_source_new_request(self):
        rows = api_breakdowns.query_for_rows(
            [],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ['account_id', 'source_id'],
            {
                'allowed_accounts': models.Account.objects.all(),
                'allowed_campaigns': models.Campaign.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            },
            [
                {'account_id': 1},
            ],
            'clicks', 1, 2,
            [
                {'account_id': 1, 'source_id': 1},
            ])

        self.assertEqual(rows, [
            dict_join({'account_id': 1}, SOURCE_2),
        ])

    def test_query_for_rows_all_accounts_break_source_account(self):
        rows = api_breakdowns.query_for_rows(
            [
                {'account_id': 1, 'source_id': 1, 'clicks': 11},
                {'account_id': 1, 'source_id': 2, 'clicks': 12},
            ],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ['source_id', 'account_id'],
            {
                'date__gte': datetime.date(2016, 7, 1),
                'date__lte': datetime.date(2016, 7, 31),
                'allowed_accounts': models.Account.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            },
            [
                {'source_id': 1},
                {'source_id': 2},
            ],
            'clicks', 0, 2,
            [
                {'account_id': 1, 'source_id': 1},
                {'account_id': 1, 'source_id': 2},
            ]
        )

        self.assertEqual(rows, [
            dict_join({'source_id': 1}, ACCOUNT_1),
            dict_join({'source_id': 2}, ACCOUNT_1),
        ])

    def test_query_for_rows_all_accounts_break_source_account_missing_row(self):
        rows = api_breakdowns.query_for_rows(
            [
                {'account_id': 1, 'source_id': 2, 'clicks': 12},
            ],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ['source_id', 'account_id'],
            {
                'date__gte': datetime.date(2016, 7, 1),
                'date__lte': datetime.date(2016, 7, 31),
                'allowed_accounts': models.Account.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            },
            [
                {'source_id': 1},
                {'source_id': 2},
            ],
            'clicks', 0, 2,
            [
                {'account_id': 1, 'source_id': 2},
            ]
        )

        self.assertEqual(rows, [
            dict_join({'source_id': 1}, ACCOUNT_1),
            dict_join({'source_id': 2}, ACCOUNT_1),
        ])

    def test_query_for_rows_all_accounts_break_source_account_new_request(self):
        rows = api_breakdowns.query_for_rows(
            [],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ['source_id', 'account_id'],
            {
                'date__gte': datetime.date(2016, 7, 1),
                'date__lte': datetime.date(2016, 7, 31),
                'allowed_accounts': models.Account.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            },
            [
                {'source_id': 1},
                {'source_id': 2},
            ],
            'clicks', 1, 2,
            [
                {'account_id': 1, 'source_id': 1},
            ]
        )

        self.assertEqual(rows, [])  # all rows were already shown

    def test_query_for_rows_all_accounts_break_source_campaign(self):
        rows = api_breakdowns.query_for_rows(
            [
                {'campaign_id': 1, 'source_id': 1, 'clicks': 11},
                {'campaign_id': 1, 'source_id': 2, 'clicks': 12},
            ],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ['source_id', 'campaign_id'],
            {
                'date__gte': datetime.date(2016, 7, 1),
                'date__lte': datetime.date(2016, 7, 31),
                'allowed_accounts': models.Account.objects.all(),
                'allowed_campaigns': models.Campaign.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            },
            [
                {'source_id': 1},
                {'source_id': 2},
            ],
            'clicks', 0, 2,
            [
                {'campaign_id': 1, 'source_id': 1},
                {'campaign_id': 1, 'source_id': 2},
            ]
        )

        self.assertEqual(rows, [
            dict_join({'source_id': 1}, CAMPAIGN_1),
            dict_join({'source_id': 1}, CAMPAIGN_2),
            dict_join({'source_id': 2}, CAMPAIGN_1),
        ])

    def test_query_for_rows_all_accounts_break_source_campaign_no_rows(self):
        rows = api_breakdowns.query_for_rows(
            [],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ['source_id', 'campaign_id'],
            {
                'date__gte': datetime.date(2016, 7, 1),
                'date__lte': datetime.date(2016, 7, 31),
                'allowed_accounts': models.Account.objects.all(),
                'allowed_campaigns': models.Campaign.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            },
            [
                {'source_id': 1},
                {'source_id': 2},
            ],
            'clicks', 0, 2,
            []
        )

        self.assertEqual(rows, [
            dict_join({'source_id': 1}, CAMPAIGN_1),
            dict_join({'source_id': 1}, CAMPAIGN_2),
            dict_join({'source_id': 2}, CAMPAIGN_1),
        ])

    def test_query_for_rows_accounts_break_campaign(self):
        rows = api_breakdowns.query_for_rows(
            [
                {'campaign_id': 1, 'clicks': 11},
                {'campaign_id': 2, 'clicks': 22},
            ],
            Level.ACCOUNTS,
            User.objects.get(pk=1),
            ['campaign_id'],
            {
                'date__gte': datetime.date(2016, 7, 1),
                'date__lte': datetime.date(2016, 7, 31),
                'account': models.Account.objects.get(pk=1),
                'allowed_campaigns': models.Campaign.objects.filter(account_id=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign__account_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            None, 'clicks', 0, 2,
            []
        )

        self.assertEqual(rows,  [CAMPAIGN_1, CAMPAIGN_2])

    def test_query_for_rows_accounts_break_source(self):
        rows = api_breakdowns.query_for_rows(
            [
                {'source_id': 1, 'clicks': 11},
                {'source_id': 2, 'clicks': 22},
            ],
            Level.ACCOUNTS,
            User.objects.get(pk=1),
            ['source_id'],
            {
                'account': models.Account.objects.get(pk=1),
                'allowed_campaigns': models.Campaign.objects.filter(account_id=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign__account_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            None, 'clicks', 0, 2,
            []
        )

        self.assertEqual(rows,  [SOURCE_1, SOURCE_2])

    def test_query_for_rows_accounts_break_campaign_source(self):
        rows = api_breakdowns.query_for_rows(
            [
                {'campaign_id': 1, 'source_id': 1, 'clicks': 11},
                {'campaign_id': 1, 'source_id': 2, 'clicks': 12},
                {'campaign_id': 2, 'source_id': 1, 'clicks': 21},
                {'campaign_id': 2, 'source_id': 2, 'clicks': 22},
            ],
            Level.ACCOUNTS,
            User.objects.get(pk=1),
            ['campaign_id', 'source_id'],
            {
                'account': models.Account.objects.get(pk=1),
                'allowed_campaigns': models.Campaign.objects.filter(account_id=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign__account_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            [
                {'campaign_id': 1},
                {'campaign_id': 2},
            ],
            'clicks', 0, 2,
            [
                {'campaign_id': 1, 'source_id': 1},
                {'campaign_id': 1, 'source_id': 2},
                {'campaign_id': 2, 'source_id': 1},
                {'campaign_id': 2, 'source_id': 2},
            ]
        )

        # source_id: 2 was not added to campaign
        self.assertEqual(rows,  [
            dict_join({'campaign_id': 1}, SOURCE_1),
            dict_join({'campaign_id': 1}, SOURCE_2),
            dict_join({'campaign_id': 2}, SOURCE_1),
        ])

    def test_query_for_rows_accounts_break_source_campaign(self):
        rows = api_breakdowns.query_for_rows(
            [
                {'campaign_id': 1, 'source_id': 1, 'clicks': 11},
                {'campaign_id': 1, 'source_id': 2, 'clicks': 12},
                {'campaign_id': 2, 'source_id': 1, 'clicks': 21},
                {'campaign_id': 2, 'source_id': 2, 'clicks': 22},
            ],
            Level.ACCOUNTS,
            User.objects.get(pk=1),
            ['source_id', 'campaign_id'],
            {
                'date__gte': datetime.date(2016, 7, 1),
                'date__lte': datetime.date(2016, 7, 31),
                'account': models.Account.objects.get(pk=1),
                'allowed_campaigns': models.Campaign.objects.filter(account_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            [
                {'source_id': 1},
                {'source_id': 2},
            ],
            'clicks', 0, 2,
            [
                {'campaign_id': 1, 'source_id': 1, 'clicks': 11},
                {'campaign_id': 1, 'source_id': 2, 'clicks': 12},
                {'campaign_id': 2, 'source_id': 1, 'clicks': 21},
                {'campaign_id': 2, 'source_id': 2, 'clicks': 22},
            ],
        )

        self.assertEqual(rows,  [
            dict_join({'source_id': 1}, CAMPAIGN_1),
            dict_join({'source_id': 1}, CAMPAIGN_2),
            dict_join({'source_id': 2}, CAMPAIGN_1),
        ])

    def test_query_for_rows_campaigns_break_ad_group(self):
        rows = api_breakdowns.query_for_rows(
            [
                {'ad_group_id': 1, 'clicks': 11},
                {'ad_group_id': 2, 'clicks': 22},
            ],
            Level.CAMPAIGNS,
            User.objects.get(pk=1),
            ['ad_group_id'],
            {
                'campaign': models.Campaign.objects.get(pk=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            None, 'clicks', 0, 2,
            []
        )

        self.assertEqual(rows,  [AD_GROUP_BASE_1, AD_GROUP_BASE_2])

    def test_query_for_rows_campaigns_break_source(self):
        rows = api_breakdowns.query_for_rows(
            [
                {'source_id': 1, 'clicks': 11},
                {'source_id': 2, 'clicks': 22},
            ],
            Level.CAMPAIGNS,
            User.objects.get(pk=1),
            ['source_id'],
            {
                'campaign': models.Campaign.objects.get(pk=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign_id=1),
            },
            None, 'clicks', 0, 2,
            []
        )

        self.assertEqual(rows,  [SOURCE_1, SOURCE_2])

    def test_query_for_rows_campaigns_break_ad_group_source(self):
        rows = api_breakdowns.query_for_rows(
            [
                {'ad_group_id': 1, 'source_id': 1, 'clicks': 11},
                {'ad_group_id': 1, 'source_id': 2, 'clicks': 12},
                {'ad_group_id': 2, 'source_id': 1, 'clicks': 21},
                {'ad_group_id': 2, 'source_id': 2, 'clicks': 22},
            ],
            Level.CAMPAIGNS,
            User.objects.get(pk=1),
            ['ad_group_id', 'source_id'],
            {
                'campaign': models.Campaign.objects.get(pk=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign_id=1),
                'allowed_content_ads': models.ContentAd.objects.filter(ad_group__campaign_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            [
                {'ad_group_id': 1},
                {'ad_group_id': 2},
            ],
            'clicks', 0, 2,
            [
                {'ad_group_id': 1, 'source_id': 1, 'clicks': 11},
                {'ad_group_id': 1, 'source_id': 2, 'clicks': 12},
                {'ad_group_id': 2, 'source_id': 1, 'clicks': 21},
                {'ad_group_id': 2, 'source_id': 2, 'clicks': 22},
            ]
        )

        self.assertEqual(rows,  [
            dict_join({'ad_group_id': 1}, SOURCE_1),
            dict_join({'ad_group_id': 1}, SOURCE_2),
            dict_join({'ad_group_id': 2}, SOURCE_1),
            dict_join({'ad_group_id': 2}, SOURCE_2),
        ])

    def test_query_for_rows_campaigns_break_source_ad_group(self):
        rows = api_breakdowns.query_for_rows(
            [
                {'ad_group_id': 1, 'source_id': 1, 'clicks': 11},
                {'ad_group_id': 1, 'source_id': 2, 'clicks': 12},
                {'ad_group_id': 2, 'source_id': 1, 'clicks': 21},
                {'ad_group_id': 2, 'source_id': 2, 'clicks': 22},
            ],
            Level.CAMPAIGNS,
            User.objects.get(pk=1),
            ['source_id', 'ad_group_id'],
            {
                'campaign': models.Campaign.objects.get(pk=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign_id=1),
                'allowed_content_ads': models.ContentAd.objects.filter(ad_group__campaign_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            [
                {'source_id': 1},
                {'source_id': 2},
            ],
            'clicks', 0, 2,
            [
                {'ad_group_id': 1, 'source_id': 1, 'clicks': 11},
                {'ad_group_id': 1, 'source_id': 2, 'clicks': 12},
                {'ad_group_id': 2, 'source_id': 1, 'clicks': 21},
                {'ad_group_id': 2, 'source_id': 2, 'clicks': 22},
            ]
        )

        self.assertEqual(rows,  [
            dict_join({'source_id': 1}, AD_GROUP_1),
            dict_join({'source_id': 1}, AD_GROUP_2),
            dict_join({'source_id': 2}, AD_GROUP_1),
            dict_join({'source_id': 2}, AD_GROUP_2),
        ])

    def test_query_for_rows_ad_groups_break_content_ad(self):
        rows = api_breakdowns.query_for_rows(
            [
                {'content_ad_id': 1, 'clicks': 11},
                {'content_ad_id': 2, 'clicks': 22},
            ],
            Level.AD_GROUPS,
            User.objects.get(pk=1),
            ['content_ad_id'],
            {
                'ad_group': models.AdGroup.objects.get(pk=1),
                'allowed_content_ads': models.ContentAd.objects.filter(ad_group_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            None, 'clicks', 0, 2,
            []
        )

        self.assertEqual(rows,  [CONTENT_AD_1, CONTENT_AD_2])

    def test_query_for_rows_ad_groups_break_source(self):
        rows = api_breakdowns.query_for_rows(
            [
                {'source_id': 1, 'clicks': 11},
                {'source_id': 2, 'clicks': 22},
            ],
            Level.AD_GROUPS,
            User.objects.get(pk=1),
            ['source_id'],
            {
                'ad_group': models.AdGroup.objects.get(pk=1),
                'allowed_content_ads': models.ContentAd.objects.filter(ad_group_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            None, 'clicks', 0, 2,
            []
        )

        self.assertEqual(rows,  [AD_GROUP_SOURCE_1, AD_GROUP_SOURCE_2])

    def test_query_for_rows_ad_groups_break_publisher(self):
        rows = api_breakdowns.query_for_rows(
            [
                {'publisher_id': 'pub1.com__1', 'clicks': 11},
                {'publisher_id': 'pub2.com__1', 'clicks': 22},  # this one is not blacklisted
                {'publisher_id': 'pub3.com__2', 'clicks': 33},  # this one is not blacklisted
                {'publisher_id': 'pub4.com__2', 'clicks': 44},
            ],
            Level.AD_GROUPS,
            User.objects.get(pk=1),
            ['publisher_id'],
            {
                'ad_group': models.AdGroup.objects.get(pk=1),
                'allowed_content_ads': models.ContentAd.objects.filter(ad_group_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
                'publisher_blacklist': models.PublisherBlacklist.objects.all(),
            },
            None, 'clicks', 0, 2,
            []
        )

        self.assertEqual(rows,  [PUBLISHER_1__SOURCE_1, PUBLISHER_2__SOURCE_1, PUBLISHER_3__SOURCE_2, PUBLISHER_4__SOURCE_2])


class HelpersTest(TestCase):

    def test_get_adjusted_limits_for_additional_rows(self):

        self.assertEquals(helpers.get_adjusted_limits_for_additional_rows(range(5), range(5), 0, 10), (0, 5))

        self.assertEquals(helpers.get_adjusted_limits_for_additional_rows([], range(5), 5, 10), (0, 10))

        self.assertEquals(helpers.get_adjusted_limits_for_additional_rows([], range(5), 10, 10), (5, 10))

        self.assertEquals(helpers.get_adjusted_limits_for_additional_rows(range(5), range(15), 10, 10), (0, 5))

    def test_get_default_order(self):

        self.assertEquals(api_breakdowns.get_default_order('source_id', '-clicks'), ['-name', '-source_id'])

        self.assertEquals(api_breakdowns.get_default_order('source_id', 'clicks'), ['name', 'source_id'])

        self.assertEquals(api_breakdowns.get_default_order('ad_group_id', 'clicks'), ['name', 'ad_group_id'])

    def test_make_rows(self):
        self.assertItemsEqual(augmenter.make_dash_rows('account_id', [1, 2, 3], None), [
            {'account_id': 1},
            {'account_id': 2},
            {'account_id': 3},
        ])

        self.assertItemsEqual(augmenter.make_dash_rows('account_id', [1, 2, 3], {'source_id': 2}), [
            {'account_id': 1, 'source_id': 2},
            {'account_id': 2, 'source_id': 2},
            {'account_id': 3, 'source_id': 2},
        ])
