from datetime import date
from decimal import Decimal

from django.test import TestCase

import dash.constants
import stats.constants
from core.features import bid_modifiers
from core.features.publisher_bid_modifiers.service_test import add_non_publisher_bid_modifiers
from dash import models
from dash.dashapi import augmenter
from dash.dashapi import loaders
from utils import test_helper
from utils.magic_mixer import magic_mixer


class PublisherAugmenterTest(TestCase):
    def setUp(self):
        ad_group = magic_mixer.blend(models.AdGroup, id=1)
        source = magic_mixer.blend(models.Source, id=1)
        add_non_publisher_bid_modifiers(ad_group=ad_group, source=source)
        magic_mixer.blend(
            bid_modifiers.BidModifier,
            ad_group=ad_group,
            source=source,
            source_slug=source.bidder_slug,
            target="pub1.com",
            modifier=0.5,
            type=bid_modifiers.constants.BidModifierType.PUBLISHER,
        )
        ad_group_source = magic_mixer.blend(models.AdGroupSource, source=source, ad_group=ad_group)
        ad_group_source.settings.update(None, cpc_cc=Decimal("1.5"), cpm=Decimal("2.5"), skip_validation=True)
        user = magic_mixer.blend_user()

        self.bid_modifier_loader = loaders.PublisherBidModifierLoader(
            models.AdGroup.objects.all().first(),
            models.PublisherGroupEntry.objects.filter(),
            models.PublisherGroupEntry.objects.all(),
            {},
            models.Source.objects.all(),
            user,
        )

        self.augmenter = augmenter.get_augmenter_for_dimension("publisher_id")
        self.report_augmenter = augmenter.get_report_augmenter_for_dimension("publisher_id", None)

    def test_augmenter_bid_modifiers(self):
        row = {"publisher_id": "pub1.com__1", "source_id": 1}
        self.augmenter([row], self.bid_modifier_loader)
        self.assertDictEqual(
            row["bid_modifier"],
            {
                "modifier": 0.5,
                "source_bid_value": {
                    "bid_cpc_value": Decimal("1.5000"),
                    "bid_cpm_value": Decimal("2.5000"),
                    "currency_symbol": "$",
                },
            },
        )

    def test_report_augmenter_bid_modifiers(self):
        row = {"publisher_id": "pub1.com__1", "source_id": 1}
        self.report_augmenter([row], self.bid_modifier_loader)
        self.assertEqual(row["bid_modifier"], 0.5)


class DeliveryAugmenterTest(TestCase):
    def setUp(self):
        ad_group = magic_mixer.blend(models.AdGroup, id=1)
        source = magic_mixer.blend(models.Source, id=1)
        add_non_publisher_bid_modifiers(ad_group=ad_group, source=source)
        self.bid_modifier = magic_mixer.blend(
            bid_modifiers.BidModifier,
            ad_group=ad_group,
            source=source,
            source_slug=source.bidder_slug,
            target=str(dash.constants.DeviceType.DESKTOP),
            modifier=0.5,
            type=bid_modifiers.constants.BidModifierType.DEVICE,
        )
        ad_group_source = magic_mixer.blend(models.AdGroupSource, source=source, ad_group=ad_group)
        ad_group_source.settings.update(None, cpc_cc=Decimal("1.5"), cpm=Decimal("2.5"), skip_validation=True)
        self.user = magic_mixer.blend_user()

        ad_group = models.AdGroup.objects.all().first()
        self.delivery_loader = loaders.DeliveryLoader(
            ad_group, self.user, breakdown=[stats.constants.DeliveryDimension.DEVICE]
        )
        self.augmenter = augmenter.get_augmenter_for_dimension("device_type")
        self.report_augmenter = augmenter.get_report_augmenter_for_dimension("device_type", None)

        self.expected_min = pow(
            0.5,
            bid_modifiers.BidModifier.objects.filter(ad_group=ad_group)
            .exclude(type=bid_modifiers.BidModifierType.DEVICE)
            .count(),
        )
        self.expected_max = 1.0

    def test_augmenter_bid_modifiers(self):
        row = {"device_type": dash.constants.DeviceType.DESKTOP}
        self.augmenter([row], self.delivery_loader)
        self.assertDictEqual(
            row,
            {
                "device_type": dash.constants.DeviceType.DESKTOP,
                "bid_modifier": {
                    "id": self.bid_modifier.id,
                    "type": "DEVICE",
                    "source_slug": self.bid_modifier.source_slug,
                    "target": "DESKTOP",
                    "modifier": self.bid_modifier.modifier,
                    "bid_min": self.expected_min,
                    "bid_max": self.expected_max,
                },
                "editable_fields": {"bid_modifier": {"enabled": True, "message": None}},
            },
        )

    def test_augmenter_no_bid_modifier_data(self):
        row = {"device_type": dash.constants.DeviceType.MOBILE}
        self.augmenter([row], self.delivery_loader)
        self.assertDictEqual(
            row,
            {
                "device_type": dash.constants.DeviceType.MOBILE,
                "bid_modifier": {
                    "id": None,
                    "type": "DEVICE",
                    "source_slug": None,
                    "target": "MOBILE",
                    "modifier": None,
                    "bid_min": self.expected_min,
                    "bid_max": self.expected_max,
                },
                "editable_fields": {"bid_modifier": {"enabled": True, "message": None}},
            },
        )

    def test_augmenter_no_bid_modifier_data_invalid_target(self):
        row = {"device_type": None}
        self.augmenter([row], self.delivery_loader)
        self.assertDictEqual(
            row, {"device_type": None, "editable_fields": {"bid_modifier": {"enabled": True, "message": None}}}
        )

    def test_report_augmenter_bid_modifiers(self):
        row = {"device_type": dash.constants.DeviceType.DESKTOP}
        self.report_augmenter([row], self.delivery_loader)
        self.assertEqual(0.5, row["bid_modifier"])

    def test_report_augmenter_no_bid_modifier_data(self):
        row = {"device_type": dash.constants.DeviceType.MOBILE}
        self.report_augmenter([row], self.delivery_loader)
        self.assertEqual(None, row["bid_modifier"])


class IncludeEntityTagsAugmentersTestCase(TestCase):
    def setUp(self):
        self.agency = magic_mixer.blend(models.Agency)
        self.agency.entity_tags.add("some/agency", "another/agency")
        self.account = magic_mixer.blend(models.Account, agency=self.agency)
        self.account.entity_tags.add("some/account", "another/account")
        self.campaign = magic_mixer.blend(models.Campaign)
        self.campaign.entity_tags.add("some/campaign", "another/campaign")
        self.ad_group = magic_mixer.blend(models.AdGroup)
        self.ad_group.entity_tags.add("some/ad_group", "another/ad_group")
        self.source = magic_mixer.blend(models.Source)
        self.source.entity_tags.add("some/source", "another/source")

        self.user_with_permission = magic_mixer.blend_user()
        test_helper.add_permissions(self.user_with_permission, ["can_include_tags_in_reports"])
        self.user_without_permission = magic_mixer.blend_user()

    def test_account_augmenter_with_none_kwarg(self):
        row = {"account_id": self.account.id}
        the_loader = loaders.AccountsLoader(
            models.Account.objects.filter(id=self.account.id),
            models.Source.objects.none(),
            self.user_with_permission,
            start_date=date.today(),
            end_date=date.today(),
            include_entity_tags=None,
        )
        augmenter.augment_account(row, the_loader)
        self.assertFalse("agency_tags" in row)
        self.assertFalse("account_tags" in row)

    def test_account_augmenter_with_false_kwarg(self):
        row = {"account_id": self.account.id}
        the_loader = loaders.AccountsLoader(
            models.Account.objects.filter(id=self.account.id),
            models.Source.objects.none(),
            self.user_with_permission,
            start_date=date.today(),
            end_date=date.today(),
            include_entity_tags=False,
        )
        augmenter.augment_account(row, the_loader)
        self.assertFalse("account_tags" in row)

    def test_account_augmenter_without_permission(self):
        row = {"account_id": self.account.id}
        the_loader = loaders.AccountsLoader(
            models.Account.objects.filter(id=self.account.id),
            models.Source.objects.none(),
            self.user_without_permission,
            start_date=date.today(),
            end_date=date.today(),
            include_entity_tags=False,
        )
        augmenter.augment_account(row, the_loader)
        self.assertFalse("agency_tags" in row)
        self.assertFalse("account_tags" in row)

    def test_account_augmenter(self):
        row = {"account_id": self.account.id}
        the_loader = loaders.AccountsLoader(
            models.Account.objects.filter(id=self.account.id),
            models.Source.objects.none(),
            self.user_with_permission,
            start_date=date.today(),
            end_date=date.today(),
            include_entity_tags=True,
        )
        augmenter.augment_account(row, the_loader)
        self.assertTrue("agency_tags" in row)
        self.assertEqual(row["agency_tags"], "another/agency,some/agency")
        self.assertTrue("account_tags" in row)
        self.assertEqual(row["account_tags"], "another/account,some/account")

    def test_account_augmenter_without_agency(self):
        account = magic_mixer.blend(models.Account)
        account.entity_tags.add("other/account", "foreign/account")
        row = {"account_id": account.id}
        the_loader = loaders.AccountsLoader(
            models.Account.objects.filter(id=account.id),
            models.Source.objects.none(),
            self.user_with_permission,
            start_date=date.today(),
            end_date=date.today(),
            include_entity_tags=True,
        )
        augmenter.augment_account(row, the_loader)
        self.assertTrue("agency_tags" in row)
        self.assertEqual(row["agency_tags"], "")
        self.assertTrue("account_tags" in row)
        self.assertEqual(row["account_tags"], "foreign/account,other/account")

    def test_campaign_augmenter(self):
        row = {"campaign_id": self.campaign.id}
        the_loader = loaders.CampaignsLoader(
            models.Campaign.objects.filter(id=self.campaign.id),
            models.Source.objects.none(),
            self.user_with_permission,
            start_date=date.today(),
            end_date=date.today(),
            include_entity_tags=True,
        )
        augmenter.augment_campaign(row, the_loader)
        self.assertTrue("campaign_tags" in row)
        self.assertEqual(row["campaign_tags"], "another/campaign,some/campaign")

    def test_ad_group_augmenter(self):
        row = {"ad_group_id": self.ad_group.id}
        the_loader = loaders.AdGroupsLoader(
            models.AdGroup.objects.filter(id=self.ad_group.id),
            models.Source.objects.none(),
            self.user_with_permission,
            start_date=date.today(),
            end_date=date.today(),
            include_entity_tags=True,
        )
        augmenter.augment_ad_group(row, the_loader)
        self.assertTrue("ad_group_tags" in row)
        self.assertEqual(row["ad_group_tags"], "another/ad_group,some/ad_group")
