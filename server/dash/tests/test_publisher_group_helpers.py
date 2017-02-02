import mock
import datetime

from django.test import TestCase, override_settings
from django.http.request import HttpRequest

from dash import models
from dash import constants
from dash import publisher_group_helpers

from utils import test_helper

import zemauth.models


class PublisherGroupHelpersTest(TestCase):
    fixtures = ['test_publishers.yaml']

    def setUp(self):
        self.request = HttpRequest()
        self.request.user = zemauth.models.User.objects.get(id=1)

    def assertEntriesEqual(self, publisher_group, entries):
        self.assertItemsEqual(
            publisher_group.entries.all().values('publisher', 'include_subdomains', 'source'),
            entries
        )

    def assertWhitelistCreated(self, obj):
        self.assertIsNotNone(obj.default_whitelist)
        self.assertEqual(obj.default_whitelist.name, obj.get_default_whitelist_name())

    def assertBlacklistCreated(self, obj):
        self.assertIsNotNone(obj.default_blacklist)
        self.assertEqual(obj.default_blacklist.name, obj.get_default_blacklist_name())

    def test_blacklist_publisher_ad_group(self):
        obj = models.AdGroup.objects.get(pk=1)
        publisher_group_helpers.blacklist_publishers(
            self.request, [{
                'publisher': 'cnn.com',
                'source': None,
                'include_subdomains': False,
            }], obj)

        self.assertEntriesEqual(obj.default_blacklist, [{
            'publisher': 'cnn.com',
            'source': None,
            'include_subdomains': False,
        }])

    def test_whitelist_publisher_ad_group(self):
        obj = models.AdGroup.objects.get(pk=1)
        publisher_group_helpers.whitelist_publishers(
            self.request, [{
                'publisher': 'cnn.com',
                'source': None,
                'include_subdomains': False,
            }], obj)

        self.assertEntriesEqual(obj.default_whitelist, [{
            'publisher': 'cnn.com',
            'source': None,
            'include_subdomains': False,
        }])

    def test_unlist_whitelisted_publisher_ad_group(self):
        obj = models.AdGroup.objects.get(pk=1)
        entry = models.PublisherGroupEntry.objects.create(
            publisher_group=obj.default_whitelist,
            source=None,
            publisher='cnn.com')
        self.assertEntriesEqual(obj.default_whitelist, [{
            'publisher': 'cnn.com',
            'source': None,
            'include_subdomains': True,
        }])

        publisher_group_helpers.unlist_publishers(self.request, [{
            'publisher': 'cnn.com',
            'source': None,
        }], obj)
        self.assertEntriesEqual(obj.default_whitelist, [])

    def test_unlist_blacklisted_publisher_ad_group(self):
        obj = models.AdGroup.objects.get(pk=1)
        entry = models.PublisherGroupEntry.objects.create(
            publisher_group=obj.default_blacklist,
            source=None,
            publisher='cnn.com')
        self.assertEntriesEqual(obj.default_blacklist, [{
            'publisher': 'cnn.com',
            'source': None,
            'include_subdomains': True,
        }])

        publisher_group_helpers.unlist_publishers(self.request, [{
            'publisher': 'cnn.com',
            'source': None,
        }], obj)
        self.assertEntriesEqual(obj.default_blacklist, [])

    def test_blacklist_publisher_campaign(self):
        obj = models.Campaign.objects.get(pk=1)
        self.assertIsNone(obj.default_blacklist)

        publisher_group_helpers.blacklist_publishers(
            self.request, [{
                'publisher': 'cnn.com',
                'source': None,
                'include_subdomains': False,
            }], obj)

        self.assertEntriesEqual(obj.default_blacklist, [{
            'publisher': 'cnn.com',
            'source': None,
            'include_subdomains': False,
        }])
        self.assertBlacklistCreated(obj)

    def test_whitelist_publisher_campaign(self):
        obj = models.Campaign.objects.get(pk=1)
        self.assertIsNone(obj.default_whitelist)

        publisher_group_helpers.whitelist_publishers(
            self.request, [{
                'publisher': 'cnn.com',
                'source': None,
                'include_subdomains': False,
            }], obj)

        self.assertEntriesEqual(obj.default_whitelist, [{
            'publisher': 'cnn.com',
            'source': None,
            'include_subdomains': False,
        }])
        self.assertWhitelistCreated(obj)

    def test_unlist_whitelisted_publisher_campaign(self):
        obj = models.Campaign.objects.get(pk=1)
        publisher_group = models.PublisherGroup(name='was')
        publisher_group.save(self.request)

        obj.default_whitelist = publisher_group
        obj.save(self.request)

        entry = models.PublisherGroupEntry.objects.create(
            publisher_group=obj.default_whitelist,
            source=None,
            publisher='cnn.com')
        self.assertEntriesEqual(obj.default_whitelist, [{
            'publisher': 'cnn.com',
            'source': None,
            'include_subdomains': True,
        }])

        publisher_group_helpers.unlist_publishers(self.request, [{
            'publisher': 'cnn.com',
            'source': None,
        }], obj)
        self.assertEntriesEqual(obj.default_whitelist, [])

    def test_unlist_blacklisted_publisher_campaign(self):
        obj = models.Campaign.objects.get(pk=1)
        publisher_group = models.PublisherGroup(name='was')
        publisher_group.save(self.request)

        obj.default_blacklist = publisher_group
        obj.save(self.request)

        entry = models.PublisherGroupEntry.objects.create(
            publisher_group=obj.default_blacklist,
            source=None,
            publisher='cnn.com')
        self.assertEntriesEqual(obj.default_blacklist, [{
            'publisher': 'cnn.com',
            'source': None,
            'include_subdomains': True,
        }])

        publisher_group_helpers.unlist_publishers(self.request, [{
            'publisher': 'cnn.com',
            'source': None,
        }], obj)
        self.assertEntriesEqual(obj.default_blacklist, [])

    def test_blacklist_publisher_account(self):
        obj = models.Account.objects.get(pk=1)
        publisher_group_helpers.blacklist_publishers(
            self.request, [{
                'publisher': 'cnn.com',
                'source': None,
                'include_subdomains': False,
            }], obj)

        self.assertEntriesEqual(obj.default_blacklist, [{
            'publisher': 'cnn.com',
            'source': None,
            'include_subdomains': False,
        }])
        self.assertBlacklistCreated(obj)

    def test_whitelist_publisher_account(self):
        obj = models.Account.objects.get(pk=1)
        publisher_group_helpers.whitelist_publishers(
            self.request, [{
                'publisher': 'cnn.com',
                'source': None,
                'include_subdomains': False,
            }], obj)

        self.assertEntriesEqual(obj.default_whitelist, [{
            'publisher': 'cnn.com',
            'source': None,
            'include_subdomains': False,
        }])
        self.assertWhitelistCreated(obj)

    def test_unlist_whitelisted_publisher_account(self):
        obj = models.Account.objects.get(pk=1)
        publisher_group = models.PublisherGroup(name='was')
        publisher_group.save(self.request)

        obj.default_whitelist = publisher_group
        obj.save(self.request)

        entry = models.PublisherGroupEntry.objects.create(
            publisher_group=obj.default_whitelist,
            source=None,
            publisher='cnn.com')

        publisher_group_helpers.unlist_publishers(self.request, [{
            'publisher': 'cnn.com',
            'source': None,
            'include_subdomains': False,
        }], obj)
        self.assertEntriesEqual(obj.default_whitelist, [])

    def test_blacklist_publisher_global(self):
        global_group = models.PublisherGroup(name='imglobal')
        global_group.save(self.request)

        with override_settings(GLOBAL_BLACKLIST_ID=global_group.id):
            publisher_group_helpers.blacklist_publishers(
                self.request, [{
                    'publisher': 'cnn.com',
                    'source': None,
                    'include_subdomains': False,
                }], None)

            self.assertEntriesEqual(global_group, [{
                'publisher': 'cnn.com',
                'source': None,
                'include_subdomains': False,
            }])

    def test_whitelist_publisher_global(self):
        with self.assertRaises(publisher_group_helpers.PublisherGroupTargetingException):
            # not available
            publisher_group_helpers.whitelist_publishers(
                self.request, [{
                    'publisher': 'cnn.com',
                    'source': None,
                    'include_subdomains': False,
                }], None)

    def test_unlist_publisher_global(self):
        global_group = models.PublisherGroup(name='imglobal')
        global_group.save(self.request)

        entry = models.PublisherGroupEntry.objects.create(
            publisher_group=global_group,
            source=None,
            publisher='cnn.com')

        with override_settings(GLOBAL_BLACKLIST_ID=global_group.id):
            publisher_group_helpers.unlist_publishers(
                self.request, [{
                    'publisher': 'cnn.com',
                    'source': None,
                    'include_subdomains': False,
                }], None)

            self.assertEntriesEqual(global_group, [])

    def test_concat_publisher_targeting(self):
        ad_group = models.AdGroup.objects.get(pk=1)
        ad_group_settings = ad_group.get_current_settings()
        campaign = models.Campaign.objects.get(pk=1)
        campaign_settings = campaign.get_current_settings()
        account = models.Account.objects.get(pk=1)
        account_settings = account.get_current_settings()

        with override_settings(GLOBAL_BLACKLIST_ID=1):
            ad_group.default_blacklist_id = 2
            ad_group_settings.blacklist_publisher_groups = [3]
            campaign.default_blacklist_id = 4
            campaign_settings.blacklist_publisher_groups = [5]
            account.default_blacklist_id = 6
            account_settings.blacklist_publisher_groups = [7]

            ad_group.default_whitelist_id = 11
            ad_group_settings.whitelist_publisher_groups = [12]
            campaign.default_whitelist_id = 13
            campaign_settings.whitelist_publisher_groups = [14]
            account.default_whitelist_id = 15
            account_settings.whitelist_publisher_groups = [16]

            blacklist, whitelist = publisher_group_helpers.concat_publisher_group_targeting(
                ad_group, ad_group_settings, campaign, campaign_settings, account, account_settings
            )

        self.assertItemsEqual(blacklist, [1, 2, 3, 4, 5, 6, 7])
        self.assertItemsEqual(whitelist, [11, 12, 13, 14, 15, 16])
