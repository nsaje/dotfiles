from django.core import exceptions
from django.test import TestCase

import core.models
from utils.magic_mixer import magic_mixer

from .model import DirectDealConnection


class TestDirectDealConnectionManager(TestCase):
    def test_create_deal_connection_with_account(self):
        request = magic_mixer.blend_request_user()
        account = magic_mixer.blend(core.models.Account, id=1)
        deal = magic_mixer.blend(core.features.deals.DirectDeal, id=2, account=account)

        deal_connection = DirectDealConnection.objects.create(request, deal, account=account)

        self.assertTrue(deal_connection.pk)
        self.assertEqual(deal_connection.account, account)
        self.assertEqual(deal_connection.campaign, None)
        self.assertEqual(deal_connection.adgroup, None)
        self.assertEqual(deal_connection.deal, deal)

    def test_create_deal_connection_with_campaign(self):
        request = magic_mixer.blend_request_user()
        account = magic_mixer.blend(core.models.Account, id=1)
        campaign = magic_mixer.blend(core.models.Campaign, id=1)
        deal = magic_mixer.blend(core.features.deals.DirectDeal, id=2, account=account)

        deal_connection = DirectDealConnection.objects.create(request, deal, campaign=campaign)

        self.assertTrue(deal_connection.pk)
        self.assertEqual(deal_connection.account, None)
        self.assertEqual(deal_connection.campaign, campaign)
        self.assertEqual(deal_connection.adgroup, None)
        self.assertEqual(deal_connection.deal, deal)

    def test_create_deal_connection_with_adgroup(self):
        request = magic_mixer.blend_request_user()
        account = magic_mixer.blend(core.models.Account, id=1)
        adgroup = magic_mixer.blend(core.models.AdGroup, id=1)
        deal = magic_mixer.blend(core.features.deals.DirectDeal, id=2, account=account)

        deal_connection = DirectDealConnection.objects.create(request, deal, adgroup=adgroup)

        self.assertTrue(deal_connection.pk)
        self.assertEqual(deal_connection.account, None)
        self.assertEqual(deal_connection.campaign, None)
        self.assertEqual(deal_connection.adgroup, adgroup)
        self.assertEqual(deal_connection.deal, deal)

    def test_create_deal_connection_without_deal(self):
        request = magic_mixer.blend_request_user()
        adgroup = magic_mixer.blend(core.models.AdGroup, id=1)

        with self.assertRaises(exceptions.ValidationError):
            DirectDealConnection.objects.create(request, None, adgroup=adgroup)

    def test_clone_direct_deal_connection_with_account(self):
        request = magic_mixer.blend_request_user()
        account = magic_mixer.blend(core.models.Account, id=1)
        deal = magic_mixer.blend(core.features.deals.DirectDeal, id=2, account=account)
        deal_connection = magic_mixer.blend(core.features.deals.DirectDealConnection, account=account, deal=deal)

        deal_connection_clone = DirectDealConnection.objects.clone(request, deal_connection, account=account)

        self.assertTrue(deal_connection_clone.pk)
        self.assertNotEqual(deal_connection.pk, deal_connection_clone.pk)
        self.assertEqual(deal_connection.account, deal_connection_clone.account)
        self.assertEqual(deal_connection_clone.campaign, None)
        self.assertEqual(deal_connection_clone.adgroup, None)
        self.assertEqual(deal_connection.deal, deal_connection_clone.deal)

    def test_clone_direct_deal_connection_with_campaign(self):
        request = magic_mixer.blend_request_user()
        account = magic_mixer.blend(core.models.Account, id=1)
        campaign = magic_mixer.blend(core.models.Campaign, id=1)
        deal = magic_mixer.blend(core.features.deals.DirectDeal, id=2, account=account)
        deal_connection = magic_mixer.blend(core.features.deals.DirectDealConnection, campaign=campaign, deal=deal)

        deal_connection_clone = DirectDealConnection.objects.clone(request, deal_connection, campaign=campaign)

        self.assertTrue(deal_connection_clone.pk)
        self.assertNotEqual(deal_connection.pk, deal_connection_clone.pk)
        self.assertEqual(deal_connection.account, None)
        self.assertEqual(deal_connection_clone.campaign, deal_connection_clone.campaign)
        self.assertEqual(deal_connection_clone.adgroup, None)
        self.assertEqual(deal_connection.deal, deal_connection_clone.deal)

    def test_clone_direct_deal_connection_with_adgroup(self):
        request = magic_mixer.blend_request_user()
        account = magic_mixer.blend(core.models.Account, id=1)
        adgroup = magic_mixer.blend(core.models.AdGroup, id=1)
        deal = magic_mixer.blend(core.features.deals.DirectDeal, id=2, account=account)
        deal_connection = magic_mixer.blend(core.features.deals.DirectDealConnection, adgroup=adgroup, deal=deal)

        deal_connection_clone = DirectDealConnection.objects.clone(request, deal_connection, adgroup=adgroup)

        self.assertTrue(deal_connection_clone.pk)
        self.assertNotEqual(deal_connection.pk, deal_connection_clone.pk)
        self.assertEqual(deal_connection.account, None)
        self.assertEqual(deal_connection_clone.campaign, None)
        self.assertEqual(deal_connection_clone.adgroup, deal_connection_clone.adgroup)
        self.assertEqual(deal_connection.deal, deal_connection_clone.deal)
