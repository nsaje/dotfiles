from datetime import date
from decimal import Decimal

from django.test import TestCase

import dash.constants
import stats.constants
from core.features import bid_modifiers
from core.features.bid_modifiers.service_test import add_non_publisher_bid_modifiers
from dash import models
from dash.dashapi import augmenter
from dash.dashapi import loaders
from utils import test_helper
from utils.magic_mixer import magic_mixer


class PublisherAugmenterTest(TestCase):
    def setUp(self):
        ad_group = magic_mixer.blend(models.AdGroup)
        self.source = magic_mixer.blend(models.Source)
        add_non_publisher_bid_modifiers(ad_group=ad_group, source=self.source)
        self.bid_modifier = magic_mixer.blend(
            bid_modifiers.BidModifier,
            ad_group=ad_group,
            source=self.source,
            source_slug=self.source.bidder_slug,
            target="pub1.com",
            modifier=0.5,
            type=bid_modifiers.constants.BidModifierType.PUBLISHER,
        )
        ad_group_source = magic_mixer.blend(models.AdGroupSource, source=self.source, ad_group=ad_group)
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
        row = {"publisher_id": f"pub1.com__{self.source.id}", "source_id": self.source.id}
        self.augmenter([row], self.bid_modifier_loader)
        self.assertDictEqual(
            row["bid_modifier"],
            {
                "id": self.bid_modifier.id,
                "type": bid_modifiers.BidModifierType.get_name(bid_modifiers.BidModifierType.PUBLISHER),
                "modifier": self.bid_modifier.modifier,
                "target": self.bid_modifier.target,
                "source_slug": self.bid_modifier.source_slug,
            },
        )

    def test_report_augmenter_bid_modifiers(self):
        row = {"publisher_id": f"pub1.com__{self.source.id}", "source_id": self.source.id}
        self.report_augmenter([row], self.bid_modifier_loader)
        self.assertEqual(row["bid_modifier"], 0.5)


class PlacementAugmenterTest(TestCase):
    def setUp(self):
        self.user = magic_mixer.blend_user()

        self.source = magic_mixer.blend(models.Source, name="Some Source", bidder_slug="somesource")

        self.pg = magic_mixer.blend(models.PublisherGroup)

        self.pge_1 = magic_mixer.blend(
            models.PublisherGroupEntry, publisher="example.com", placement=None, source=None, publisher_group=self.pg
        )
        self.pge_2 = magic_mixer.blend(
            models.PublisherGroupEntry,
            publisher="sub.example.com",
            placement=None,
            source=self.source,
            publisher_group=self.pg,
        )
        self.pge_3 = magic_mixer.blend(
            models.PublisherGroupEntry,
            publisher="example.com",
            placement="someplacement",
            source=None,
            publisher_group=self.pg,
        )
        self.pge_4 = magic_mixer.blend(
            models.PublisherGroupEntry,
            publisher="sub.example.com",
            placement="someplacement",
            source=self.source,
            publisher_group=self.pg,
        )

        self.loader = loaders.PlacementLoader(
            models.PublisherGroupEntry.objects.filter(
                id__in=[self.pge_1.id, self.pge_2.id, self.pge_3.id, self.pge_4.id]
            ),
            models.PublisherGroupEntry.objects.none(),
            {},
            models.Source.objects.all(),
            {"account": {"excluded": {self.pg.id}}},
            self.user,
        )

        self.augmenter = augmenter.get_augmenter_for_dimension("placement_id")

    def test_augment_placement(self):
        rows = [
            {
                "placement_id": f"pub1.com__{self.source.id}__someplacement",
                "publisher": "pub1.com",
                "source_id": self.source.id,
                "placement": "someplacement",
            },
            {
                "placement_id": f"sub.pub1.com__{self.source.id}__someplacement",
                "publisher": "sub.pub1.com",
                "source_id": self.source.id,
                "placement": "someplacement",
            },
        ]
        for row in rows:
            self.augmenter([row], self.loader)

        self.assertEqual(
            rows,
            [
                {
                    "placement_id": f"pub1.com__{self.source.id}__someplacement",
                    "publisher": "pub1.com",
                    "source_id": self.source.id,
                    "placement": "someplacement",
                    "name": "someplacement",
                    "source_name": "Some Source",
                    "source_slug": "somesource",
                    "exchange": "Some Source",
                    "domain": "pub1.com",
                    "domain_link": "http://pub1.com",
                    "status": 3,
                    "blacklisted": "Active",
                },
                {
                    "placement_id": f"sub.pub1.com__{self.source.id}__someplacement",
                    "publisher": "sub.pub1.com",
                    "source_id": self.source.id,
                    "placement": "someplacement",
                    "name": "someplacement",
                    "source_name": "Some Source",
                    "source_slug": "somesource",
                    "exchange": "Some Source",
                    "domain": "sub.pub1.com",
                    "domain_link": "http://sub.pub1.com",
                    "status": 3,
                    "blacklisted": "Active",
                },
            ],
        )


class DeliveryAugmenterTest(TestCase):
    def setUp(self):
        ad_group = magic_mixer.blend(models.AdGroup)
        ad_group.settings.update_unsafe(None, cpc=Decimal("3.0"))
        source = magic_mixer.blend(models.Source)
        add_non_publisher_bid_modifiers(
            omit_types={bid_modifiers.BidModifierType.SOURCE}, ad_group=ad_group, source=source
        )
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
