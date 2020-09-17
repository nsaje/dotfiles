import csv
from io import StringIO

import mock

import dash.constants
import dash.models
from dash import history_helpers
from dash.features import geolocation
from utils.base_test_case import BaseTestCase
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission

from . import constants
from . import exceptions
from . import helpers
from . import service


def add_non_publisher_bid_modifiers(omit_types=None, **kwargs):
    """Add some non publisher bid modifiers that should not alter test results."""
    omit_types = omit_types or set()
    all_types = {
        constants.BidModifierType.SOURCE,
        constants.BidModifierType.DEVICE,
        constants.BidModifierType.OPERATING_SYSTEM,
        constants.BidModifierType.ENVIRONMENT,
        constants.BidModifierType.COUNTRY,
        constants.BidModifierType.STATE,
        constants.BidModifierType.DMA,
    }
    included_types = all_types - omit_types

    blend_kwargs = {
        "publisher": ("somerandompub%s.com" % i for i in range(len(included_types))),
        "modifier": 0.5,
        "type": (t for t in included_types),
    }
    blend_kwargs.update(kwargs)
    if "source" in blend_kwargs:
        blend_kwargs["source_slug"] = blend_kwargs["source"].bidder_slug

    magic_mixer.cycle(len(included_types)).blend(dash.models.BidModifier, **blend_kwargs)


@mock.patch("utils.k1_helper.update_ad_group", mock.MagicMock())
class BidModifierServiceTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.ad_group = magic_mixer.blend(dash.models.AdGroup)
        self.source = magic_mixer.blend(dash.models.Source, bidder_slug="some_slug")
        self.ad_group_source = magic_mixer.blend(dash.models.AdGroupSource, ad_group=self.ad_group, source=self.source)
        self.content_ad = magic_mixer.blend(dash.models.ContentAd, ad_group=self.ad_group)

    def test_get(self):
        service.set(self.ad_group, constants.BidModifierType.PUBLISHER, "test_publisher", self.source, 0.5)
        service.set(self.ad_group, constants.BidModifierType.SOURCE, self.source.id, None, 4.6)
        service.set(self.ad_group, constants.BidModifierType.DEVICE, dash.constants.DeviceType.DESKTOP, None, 1.3)
        service.set(
            self.ad_group, constants.BidModifierType.OPERATING_SYSTEM, dash.constants.OperatingSystem.ANDROID, None, 1.7
        )
        service.set(self.ad_group, constants.BidModifierType.ENVIRONMENT, dash.constants.Environment.SITE, None, 3.6)
        service.set(self.ad_group, constants.BidModifierType.COUNTRY, "test_country", None, 2.9)
        service.set(self.ad_group, constants.BidModifierType.STATE, "test_state", None, 2.4)
        service.set(self.ad_group, constants.BidModifierType.DMA, "100", None, 0.6)
        service.set(self.ad_group, constants.BidModifierType.AD, str(self.content_ad.id), None, 1.1)
        service.set(self.ad_group, constants.BidModifierType.DAY_HOUR, dash.constants.DayHour.FRIDAY_10, None, 1.2)
        self.assertEqual(
            service.get(self.ad_group),
            [
                {
                    "type": constants.BidModifierType.PUBLISHER,
                    "target": "test_publisher",
                    "source": self.source,
                    "modifier": 0.5,
                },
                {
                    "type": constants.BidModifierType.SOURCE,
                    "target": str(self.source.id),
                    "source": None,
                    "modifier": 4.6,
                },
                {
                    "type": constants.BidModifierType.DEVICE,
                    "target": str(dash.constants.DeviceType.DESKTOP),
                    "source": None,
                    "modifier": 1.3,
                },
                {
                    "type": constants.BidModifierType.OPERATING_SYSTEM,
                    "target": dash.constants.OperatingSystem.ANDROID,
                    "source": None,
                    "modifier": 1.7,
                },
                {
                    "type": constants.BidModifierType.ENVIRONMENT,
                    "target": dash.constants.Environment.SITE,
                    "source": None,
                    "modifier": 3.6,
                },
                {"type": constants.BidModifierType.COUNTRY, "target": "test_country", "source": None, "modifier": 2.9},
                {"type": constants.BidModifierType.STATE, "target": "test_state", "source": None, "modifier": 2.4},
                {"type": constants.BidModifierType.DMA, "target": "100", "source": None, "modifier": 0.6},
                {
                    "type": constants.BidModifierType.AD,
                    "target": str(self.content_ad.id),
                    "source": None,
                    "modifier": 1.1,
                },
                {
                    "type": constants.BidModifierType.DAY_HOUR,
                    "target": str(dash.constants.DayHour.FRIDAY_10),
                    "source": None,
                    "modifier": 1.2,
                },
            ],
        )

    def test_get_include_types(self):
        service.set(self.ad_group, constants.BidModifierType.PUBLISHER, "test_publisher", self.source, 0.5)
        service.set(self.ad_group, constants.BidModifierType.SOURCE, self.source.id, None, 4.6)
        service.set(self.ad_group, constants.BidModifierType.DEVICE, dash.constants.DeviceType.DESKTOP, None, 1.3)
        service.set(
            self.ad_group, constants.BidModifierType.OPERATING_SYSTEM, dash.constants.OperatingSystem.ANDROID, None, 1.7
        )
        service.set(self.ad_group, constants.BidModifierType.ENVIRONMENT, dash.constants.Environment.SITE, None, 3.6)
        service.set(self.ad_group, constants.BidModifierType.COUNTRY, "test_country", None, 2.9)
        service.set(self.ad_group, constants.BidModifierType.STATE, "test_state", None, 2.4)
        service.set(self.ad_group, constants.BidModifierType.DMA, "100", None, 0.6)
        service.set(self.ad_group, constants.BidModifierType.AD, str(self.content_ad.id), None, 1.1)
        self.assertEqual(
            service.get(self.ad_group, include_types=[constants.BidModifierType.DEVICE, constants.BidModifierType.DMA]),
            [
                {
                    "type": constants.BidModifierType.DEVICE,
                    "target": str(dash.constants.DeviceType.DESKTOP),
                    "source": None,
                    "modifier": 1.3,
                },
                {"type": constants.BidModifierType.DMA, "target": "100", "source": None, "modifier": 0.6},
            ],
        )

    def test_get_exclude_types(self):
        service.set(self.ad_group, constants.BidModifierType.PUBLISHER, "test_publisher", self.source, 0.5)
        service.set(self.ad_group, constants.BidModifierType.SOURCE, self.source.id, None, 4.6)
        service.set(self.ad_group, constants.BidModifierType.DEVICE, dash.constants.DeviceType.DESKTOP, None, 1.3)
        service.set(
            self.ad_group, constants.BidModifierType.OPERATING_SYSTEM, dash.constants.OperatingSystem.ANDROID, None, 1.7
        )
        service.set(self.ad_group, constants.BidModifierType.ENVIRONMENT, dash.constants.Environment.SITE, None, 3.6)
        service.set(self.ad_group, constants.BidModifierType.COUNTRY, "test_country", None, 2.9)
        service.set(self.ad_group, constants.BidModifierType.STATE, "test_state", None, 2.4)
        service.set(self.ad_group, constants.BidModifierType.DMA, "100", None, 0.6)
        service.set(self.ad_group, constants.BidModifierType.AD, str(self.content_ad.id), None, 1.1)
        self.assertEqual(
            service.get(
                self.ad_group,
                exclude_types=[
                    constants.BidModifierType.PUBLISHER,
                    constants.BidModifierType.OPERATING_SYSTEM,
                    constants.BidModifierType.ENVIRONMENT,
                ],
            ),
            [
                {
                    "type": constants.BidModifierType.SOURCE,
                    "target": str(self.source.id),
                    "source": None,
                    "modifier": 4.6,
                },
                {
                    "type": constants.BidModifierType.DEVICE,
                    "target": str(dash.constants.DeviceType.DESKTOP),
                    "source": None,
                    "modifier": 1.3,
                },
                {"type": constants.BidModifierType.COUNTRY, "target": "test_country", "source": None, "modifier": 2.9},
                {"type": constants.BidModifierType.STATE, "target": "test_state", "source": None, "modifier": 2.4},
                {"type": constants.BidModifierType.DMA, "target": "100", "source": None, "modifier": 0.6},
                {
                    "type": constants.BidModifierType.AD,
                    "target": str(self.content_ad.id),
                    "source": None,
                    "modifier": 1.1,
                },
            ],
        )

    def test_set_nonexisting(self):
        self.assertEqual(dash.models.BidModifier.objects.filter(ad_group=self.ad_group).count(), 0)

        service.set(self.ad_group, constants.BidModifierType.DEVICE, dash.constants.DeviceType.DESKTOP, None, 1.2)

        self.assertEqual(dash.models.BidModifier.objects.filter(ad_group=self.ad_group).count(), 1)

        self.assertEqual(
            service.get(self.ad_group),
            [
                {
                    "type": constants.BidModifierType.DEVICE,
                    "target": str(dash.constants.DeviceType.DESKTOP),
                    "source": None,
                    "modifier": 1.2,
                }
            ],
        )

    def test_set_existing(self):
        service.set(self.ad_group, constants.BidModifierType.DEVICE, dash.constants.DeviceType.DESKTOP, None, 0.5)

        self.assertEqual(dash.models.BidModifier.objects.filter(ad_group=self.ad_group).count(), 1)

        service.set(self.ad_group, constants.BidModifierType.DEVICE, dash.constants.DeviceType.DESKTOP, None, 1.2)

        self.assertEqual(dash.models.BidModifier.objects.filter(ad_group=self.ad_group).count(), 1)

        self.assertEqual(
            service.get(self.ad_group),
            [
                {
                    "type": constants.BidModifierType.DEVICE,
                    "target": str(dash.constants.DeviceType.DESKTOP),
                    "source": None,
                    "modifier": 1.2,
                }
            ],
        )

    def test_set_none(self):
        service.set(self.ad_group, constants.BidModifierType.DEVICE, dash.constants.DeviceType.DESKTOP, None, 0.5)

        self.assertEqual(dash.models.BidModifier.objects.filter(ad_group=self.ad_group).count(), 1)

        service.set(self.ad_group, constants.BidModifierType.DEVICE, dash.constants.DeviceType.DESKTOP, None, None)

        self.assertEqual(dash.models.BidModifier.objects.filter(ad_group=self.ad_group).count(), 0)

    def test_set_invalid_type(self):
        with self.assertRaises(exceptions.BidModifierValueInvalid):
            service.set(
                self.ad_group, constants.BidModifierType.DEVICE, dash.constants.DeviceType.DESKTOP, None, "invalid"
            )

    def test_set_invalid_too_big(self):
        with self.assertRaises(exceptions.BidModifierValueTooHigh):
            service.set(self.ad_group, constants.BidModifierType.DEVICE, dash.constants.DeviceType.DESKTOP, None, 35)

    def test_set_invalid_too_small(self):
        with self.assertRaises(exceptions.BidModifierValueTooLow):
            service.set(self.ad_group, constants.BidModifierType.DEVICE, dash.constants.DeviceType.DESKTOP, None, -2.0)

    def test_set_invalid_publisher_type(self):
        with self.assertRaises(exceptions.BidModifierSourceInvalid):
            service.set(self.ad_group, constants.BidModifierType.PUBLISHER, "test_publisher", None, 0.5)

    def test_set_invalid_non_publisher_type(self):
        with self.assertRaises(exceptions.BidModifierSourceInvalid):
            service.set(
                self.ad_group, constants.BidModifierType.DEVICE, dash.constants.DeviceType.DESKTOP, self.source, 0.5
            )

    def test_set_invalid_ad(self):
        content_ad = magic_mixer.blend(dash.models.ContentAd)

        with self.assertRaises(exceptions.BidModifierTargetAdGroupMismatch):
            service.set(self.ad_group, constants.BidModifierType.AD, content_ad.id, None, 0.5)

    def test_set_bulk(self):
        bms_to_set = [
            service.BidModifierData(constants.BidModifierType.DEVICE, dash.constants.DeviceType.DESKTOP, None, 0.5),
            service.BidModifierData(constants.BidModifierType.DEVICE, dash.constants.DeviceType.MOBILE, None, 0.6),
        ]
        service.set_bulk(self.ad_group, bms_to_set)
        self.assertEqual(dash.models.BidModifier.objects.filter(ad_group=self.ad_group).count(), 2)

        bms_to_set = [
            service.BidModifierData(constants.BidModifierType.DEVICE, dash.constants.DeviceType.DESKTOP, None, 0.7),
            service.BidModifierData(constants.BidModifierType.DEVICE, dash.constants.DeviceType.MOBILE, None, 0.8),
        ]
        service.set_bulk(self.ad_group, bms_to_set)
        self.assertEqual(dash.models.BidModifier.objects.filter(ad_group=self.ad_group).count(), 2)

        bms_to_set = [
            service.BidModifierData(constants.BidModifierType.DEVICE, dash.constants.DeviceType.TABLET, None, 0.9)
        ]
        service.set_bulk(self.ad_group, bms_to_set)
        self.assertEqual(dash.models.BidModifier.objects.filter(ad_group=self.ad_group).count(), 3)

        self.assertEqual(
            service.get(self.ad_group),
            [
                {
                    "type": constants.BidModifierType.DEVICE,
                    "target": str(dash.constants.DeviceType.DESKTOP),
                    "source": None,
                    "modifier": 0.7,
                },
                {
                    "type": constants.BidModifierType.DEVICE,
                    "target": str(dash.constants.DeviceType.MOBILE),
                    "source": None,
                    "modifier": 0.8,
                },
                {
                    "type": constants.BidModifierType.DEVICE,
                    "target": str(dash.constants.DeviceType.TABLET),
                    "source": None,
                    "modifier": 0.9,
                },
            ],
        )

    def test_set_bulk_invalid_ad(self):
        valid_content_ad = magic_mixer.blend(dash.models.ContentAd, ad_group=self.ad_group)
        invalid_content_ad = magic_mixer.blend(dash.models.ContentAd)

        bms_to_set = [service.BidModifierData(constants.BidModifierType.AD, str(valid_content_ad.id), None, 0.5)]
        service.set_bulk(self.ad_group, bms_to_set)
        self.assertEqual(dash.models.BidModifier.objects.filter(ad_group=self.ad_group).count(), 1)

        bms_to_set.append(service.BidModifierData(constants.BidModifierType.AD, str(invalid_content_ad.id), None, 0.6))
        with self.assertRaises(exceptions.BidModifierTargetAdGroupMismatch):
            service.set_bulk(self.ad_group, bms_to_set)

    def test_clean_entries(self):
        entries = [
            {
                constants.BidModifierType.get_text(constants.BidModifierType.PUBLISHER): "all publishers",
                "Source Slug": "some_slug",
                "Bid Modifier": "",
            },
            {
                constants.BidModifierType.get_text(constants.BidModifierType.PUBLISHER): "example1.com",
                "Source Slug": "some_slug",
                "Bid Modifier": 1.0,
            },
            {
                constants.BidModifierType.get_text(constants.BidModifierType.PUBLISHER): "example2.com",
                "Source Slug": "some_slug",
                "Bid Modifier": 2.1,
            },
            {
                constants.BidModifierType.get_text(
                    constants.BidModifierType.DEVICE
                ): dash.constants.DeviceType.get_name(dash.constants.DeviceType.MOBILE),
                "Source Slug": "",
                "Bid Modifier": 1.6,
            },
        ]
        test_entries = entries.copy()
        cleaned_entries, has_error = service.clean_entries(entries)
        self.assertFalse(has_error)
        self.assertEqual(
            cleaned_entries,
            [
                {
                    "type": constants.BidModifierType.PUBLISHER,
                    "target": "example1.com",
                    "modifier": None,
                    "source": self.source,
                },
                {
                    "type": constants.BidModifierType.PUBLISHER,
                    "target": "example2.com",
                    "modifier": 2.1,
                    "source": self.source,
                },
                {
                    "type": constants.BidModifierType.DEVICE,
                    "target": str(dash.constants.DeviceType.MOBILE),
                    "modifier": 1.6,
                    "source": None,
                },
            ],
        )
        self.assertEqual(entries, test_entries)

        entries = [
            {
                helpers.output_modifier_type(constants.BidModifierType.PUBLISHER): "",
                "Source Slug": "bad_slug",
                "Bid Modifier": 12.0,
            },
            {
                helpers.output_modifier_type(constants.BidModifierType.PUBLISHER): "example3.com",
                "Source Slug": "some_slug",
                "Bid Modifier": "ASD",
            },
            {
                helpers.output_modifier_type(constants.BidModifierType.PUBLISHER): "all publishers",
                "Source Slug": "some_slug",
                "Bid Modifier": 2.0,
            },
            {
                constants.BidModifierType.get_text(constants.BidModifierType.DEVICE): "Illegal",
                "Source Slug": "",
                "Bid Modifier": 1.6,
            },
        ]
        cleaned_entries, has_error = service.clean_entries(entries)
        self.assertEqual(has_error, True)
        self.assertEqual(
            entries[0]["Errors"],
            "%s; Invalid Source Slug; Publisher should not be empty" % helpers._get_modifier_bounds_error_message(12.0),
        )
        self.assertEqual(entries[1]["Errors"], "Invalid Bid Modifier")
        self.assertEqual(entries[2]["Errors"], "'all publishers' can not have a bid modifier set")
        self.assertEqual(entries[3]["Errors"], "Invalid Device Type")

    def test_set_from_cleaned_entries(self):
        cleaned_entries = [
            {
                "type": constants.BidModifierType.PUBLISHER,
                "target": "test_publisher",
                "source": self.source,
                "modifier": 0.5,
            },
            {"type": constants.BidModifierType.SOURCE, "target": str(self.source.id), "source": None, "modifier": 4.6},
            {
                "type": constants.BidModifierType.DEVICE,
                "target": str(dash.constants.DeviceType.DESKTOP),
                "source": None,
                "modifier": 1.3,
            },
            {
                "type": constants.BidModifierType.OPERATING_SYSTEM,
                "target": dash.constants.OperatingSystem.ANDROID,
                "source": None,
                "modifier": 1.7,
            },
            {
                "type": constants.BidModifierType.ENVIRONMENT,
                "target": dash.constants.Environment.SITE,
                "source": None,
                "modifier": 3.6,
            },
            {"type": constants.BidModifierType.COUNTRY, "target": "test_country", "source": None, "modifier": 2.9},
            {"type": constants.BidModifierType.STATE, "target": "test_state", "source": None, "modifier": 2.4},
            {"type": constants.BidModifierType.DMA, "target": "100", "source": None, "modifier": 0.6},
            {"type": constants.BidModifierType.AD, "target": str(self.content_ad.id), "source": None, "modifier": 1.1},
        ]
        service.set_from_cleaned_entries(self.ad_group, cleaned_entries)
        self.assertEqual(
            service.get(self.ad_group),
            [
                {
                    "type": constants.BidModifierType.PUBLISHER,
                    "target": "test_publisher",
                    "source": self.source,
                    "modifier": 0.5,
                },
                {
                    "type": constants.BidModifierType.SOURCE,
                    "target": str(self.source.id),
                    "source": None,
                    "modifier": 4.6,
                },
                {
                    "type": constants.BidModifierType.DEVICE,
                    "target": str(dash.constants.DeviceType.DESKTOP),
                    "source": None,
                    "modifier": 1.3,
                },
                {
                    "type": constants.BidModifierType.OPERATING_SYSTEM,
                    "target": dash.constants.OperatingSystem.ANDROID,
                    "source": None,
                    "modifier": 1.7,
                },
                {
                    "type": constants.BidModifierType.ENVIRONMENT,
                    "target": dash.constants.Environment.SITE,
                    "source": None,
                    "modifier": 3.6,
                },
                {"type": constants.BidModifierType.COUNTRY, "target": "test_country", "source": None, "modifier": 2.9},
                {"type": constants.BidModifierType.STATE, "target": "test_state", "source": None, "modifier": 2.4},
                {"type": constants.BidModifierType.DMA, "target": "100", "source": None, "modifier": 0.6},
                {
                    "type": constants.BidModifierType.AD,
                    "target": str(self.content_ad.id),
                    "source": None,
                    "modifier": 1.1,
                },
            ],
        )

    def test_delete(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        self.ad_group = magic_mixer.blend(dash.models.AdGroup, campaign__account=account)
        bid_modifiers_ids = [
            service.set(self.ad_group, constants.BidModifierType.PUBLISHER, "test_publisher", self.source, 0.5)[0].id,
            service.set(
                self.ad_group, constants.BidModifierType.ENVIRONMENT, dash.constants.Environment.SITE, None, 3.6
            )[0].id,
            service.set(self.ad_group, constants.BidModifierType.COUNTRY, "test_country", None, 2.9)[0].id,
        ]

        service.delete(self.ad_group, bid_modifiers_ids)
        self.assertEqual([], service.get(self.ad_group))

        history = history_helpers.get_ad_group_history(self.ad_group).first()
        self.assertEqual(history.created_by, None)
        self.assertEqual(history.action_type, dash.constants.HistoryActionType.BID_MODIFIER_DELETE)
        self.assertEqual(history.changes_text, "Removed 3 bid modifiers.")

    def test_delete_user_no_access(self):
        bid_modifiers_ids = [
            service.set(self.ad_group, constants.BidModifierType.PUBLISHER, "test_publisher", self.source, 0.5)[0].id,
            service.set(
                self.ad_group, constants.BidModifierType.ENVIRONMENT, dash.constants.Environment.SITE, None, 3.6
            )[0].id,
            service.set(self.ad_group, constants.BidModifierType.COUNTRY, "test_country", None, 2.9)[0].id,
        ]
        with self.assertRaises(exceptions.BidModifierDeleteInvalidIds):
            service.delete(self.ad_group, bid_modifiers_ids, user=self.user)

    def test_delete_user_access(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        self.ad_group = magic_mixer.blend(dash.models.AdGroup, campaign__account=account)
        bid_modifiers_ids = [
            service.set(self.ad_group, constants.BidModifierType.PUBLISHER, "test_publisher", self.source, 0.5)[0].id,
            service.set(
                self.ad_group, constants.BidModifierType.ENVIRONMENT, dash.constants.Environment.SITE, None, 3.6
            )[0].id,
            service.set(self.ad_group, constants.BidModifierType.COUNTRY, "test_country", None, 2.9)[0].id,
        ]

        service.delete(self.ad_group, bid_modifiers_ids, user=self.user)
        self.assertEqual([], service.get(self.ad_group))

        history = history_helpers.get_ad_group_history(self.ad_group).first()
        self.assertEqual(history.created_by, self.user)
        self.assertEqual(history.action_type, dash.constants.HistoryActionType.BID_MODIFIER_DELETE)
        self.assertEqual(history.changes_text, "Removed 3 bid modifiers.")

    def test_delete_invalid_ids(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        self.ad_group = magic_mixer.blend(dash.models.AdGroup, campaign__account=account)
        bid_modifiers_ids = [
            service.set(self.ad_group, constants.BidModifierType.PUBLISHER, "test_publisher", self.source, 0.5)[0].id,
            service.set(
                self.ad_group, constants.BidModifierType.ENVIRONMENT, dash.constants.Environment.SITE, None, 3.6
            )[0].id,
            service.set(self.ad_group, constants.BidModifierType.COUNTRY, "test_country", None, 2.9)[0].id,
        ]

        with self.assertRaises(exceptions.BidModifierDeleteInvalidIds):
            service.delete(self.ad_group, [bm_id + 5555 for bm_id in bid_modifiers_ids])

    def test_make_and_parse_example_csv_file(self):
        magic_mixer.blend(dash.models.Source, name="Outbrain", bidder_slug="b1_outbrain")
        magic_mixer.blend(
            geolocation.Geolocation, key="US", type=dash.constants.LocationType.COUNTRY, name="United States"
        )
        magic_mixer.blend(
            geolocation.Geolocation, key="US-TX", type=dash.constants.LocationType.REGION, name="Texas, United States"
        )
        magic_mixer.blend(
            geolocation.Geolocation, key="765", type=dash.constants.LocationType.DMA, name="765 El Paso, TX"
        )
        magic_mixer.blend(dash.models.ContentAd)

        for modifier_type in constants.BidModifierType.get_all():
            input_csv_file = service.make_csv_example_file(modifier_type)

            entries, _ = service.parse_csv_file_entries(input_csv_file)
            cleaned_entries, has_error = service.clean_entries(entries)
            if modifier_type in [
                constants.BidModifierType.AD,
                constants.BidModifierType.SOURCE,
                constants.BidModifierType.PLACEMENT,
            ]:
                # these types have hardcoded ids and cannot be imported
                self.assertTrue(input_csv_file)
                continue

            self.assertFalse(has_error)

            # Because clean_entries changes 1.0 modifier value to None
            for entry in cleaned_entries:
                entry.update({"modifier": "1.0"})

            output_csv_file = service.make_csv_file(modifier_type, cleaned_entries)

            input_csv_file.seek(0)
            self.assertEqual(output_csv_file.read(), input_csv_file.read())

    def test_bulk_import_with_extra_commas(self):
        """
        Due to non-standard format we have chosen editing in a spreadsheet application may result in extra commas which should not make the file invalid.
        """
        csv_file = StringIO(
            (
                "Publisher,Source Slug,Bid Modifier\n"
                "example.com,some_slug,1.1\n"
                ",,\n"
                "Device,Bid Modifier,\n"
                "DESKTOP,1.2,\n"
            )
        )

        _, instances, error = service.process_bulk_csv_file_upload(self.ad_group, csv_file)
        self.assertIsNone(error)
        self.assertEqual(len(instances), 2)
        self.assertEqual(instances[0].modifier, 1.1)
        self.assertEqual(instances[1].modifier, 1.2)

        csv_file = StringIO(
            (
                "Publisher,Source Slug,Bid Modifier,\n"
                "example.com,some_slug,1.1,\n"
                ",,,\n"
                "Device,Bid Modifier,,\n"
                "DESKTOP,1.2,,\n"
            )
        )

        _, instances, error = service.process_bulk_csv_file_upload(self.ad_group, csv_file)
        self.assertIsNone(error)
        self.assertEqual(len(instances), 2)
        self.assertEqual(instances[0].modifier, 1.1)
        self.assertEqual(instances[1].modifier, 1.2)

    def test_parse_csv_file_entries_wrong_type(self):
        input_csv_file = service.make_csv_example_file(constants.BidModifierType.PUBLISHER)

        with self.assertRaises(exceptions.InvalidBidModifierFile):
            service.parse_csv_file_entries(input_csv_file, modifier_type=constants.BidModifierType.SOURCE)

    @mock.patch("utils.s3helpers.S3Helper.put")
    def test_make_and_store_csv_error_file(self, mock_s3_helper_put):
        input_entries = [
            {
                helpers.output_modifier_type(constants.BidModifierType.PUBLISHER): "example.com",
                "Source Slug": "some_slug",
                "Bid Modifier": "foo",
            },
            {helpers.output_modifier_type(constants.BidModifierType.DEVICE): "Illegal", "Bid Modifier": "1.3"},
            {
                helpers.output_modifier_type(
                    constants.BidModifierType.OPERATING_SYSTEM
                ): dash.constants.OperatingSystem.get_text(dash.constants.OperatingSystem.ANDROID),
                "Bid Modifier": "30.0",
            },
            {
                helpers.output_modifier_type(
                    constants.BidModifierType.ENVIRONMENT
                ): dash.constants.Environment.get_name(dash.constants.Environment.SITE),
                "Bid Modifier": "-0.1",
            },
            {
                helpers.output_modifier_type(
                    constants.BidModifierType.ENVIRONMENT
                ): dash.constants.Environment.get_name(dash.constants.Environment.APP),
                "Bid Modifier": "0.5",
            },
            {helpers.output_modifier_type(constants.BidModifierType.COUNTRY): "XY", "Bid Modifier": "1.6"},
        ]

        result_entires = [
            {
                helpers.output_modifier_type(constants.BidModifierType.PUBLISHER): "example.com",
                "Source Slug": "some_slug",
                "Bid Modifier": "foo",
                "Errors": "Invalid Bid Modifier",
            },
            {
                helpers.output_modifier_type(constants.BidModifierType.DEVICE): "Illegal",
                "Bid Modifier": "1.3",
                "Errors": "Invalid Device Type",
            },
            {
                helpers.output_modifier_type(
                    constants.BidModifierType.OPERATING_SYSTEM
                ): dash.constants.OperatingSystem.get_text(dash.constants.OperatingSystem.ANDROID),
                "Bid Modifier": "30.0",
                "Errors": helpers._get_modifier_bounds_error_message(30.0),
            },
            {
                helpers.output_modifier_type(
                    constants.BidModifierType.ENVIRONMENT
                ): dash.constants.Environment.get_name(dash.constants.Environment.SITE),
                "Bid Modifier": "-0.1",
                "Errors": helpers._get_modifier_bounds_error_message(-0.1),
            },
            {
                helpers.output_modifier_type(
                    constants.BidModifierType.ENVIRONMENT
                ): dash.constants.Environment.get_name(dash.constants.Environment.APP),
                "Bid Modifier": "0.5",
                "Errors": "",
            },
            {
                helpers.output_modifier_type(constants.BidModifierType.COUNTRY): "XY",
                "Bid Modifier": "1.6",
                "Errors": "Invalid Geolocation",
            },
        ]

        for idx, entry in enumerate(input_entries):
            modifier_type, target_column_name = helpers.extract_modifier_type(entry.keys())
            csv_columns = helpers.make_csv_file_columns(modifier_type)

            csv_file = StringIO()
            writer = csv.DictWriter(csv_file, csv_columns, extrasaction="ignore")
            writer.writeheader()
            writer.writerows([entry])
            csv_file.seek(0)

            entries, _ = service.parse_csv_file_entries(csv_file)
            cleaned_entries, has_error = service.clean_entries(entries)
            self.assertEqual(has_error, result_entires[idx]["Errors"] != "")

            service.make_and_store_csv_error_file(entries, csv_columns + ["Errors"], self.ad_group.id)

            csv_error_content = mock_s3_helper_put.call_args_list[idx][0][1]

            error_entires = [row for row in csv.DictReader(StringIO(csv_error_content))]

            self.assertEqual(error_entires, [result_entires[idx]])
